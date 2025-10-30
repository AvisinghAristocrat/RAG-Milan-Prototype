#!/usr/bin/env python3
"""
Generate a robust ground-truth JSON by sampling documents.

This version is extra-defensive: converts bytes/memoryview -> str,
ensures no None is returned, and falls back to title/url/meta.
"""
import argparse, json, os
import psycopg
from psycopg.rows import dict_row
from random import sample

def to_str_safe(val):
    """Convert various possible DB types into a safe unicode string (never None)."""
    if val is None:
        return ""
    # memoryview -> bytes -> decode
    if isinstance(val, memoryview):
        try:
            return val.tobytes().decode("utf-8", errors="ignore")
        except Exception:
            return str(val)
    # bytes -> decode
    if isinstance(val, (bytes, bytearray)):
        try:
            return bytes(val).decode("utf-8", errors="ignore")
        except Exception:
            return str(val)
    # other scalar -> str
    try:
        return str(val)
    except Exception:
        return ""

def safe_text_from_doc(doc, words=20):
    """
    Return a safe text snippet for a query from a doc record.
    Always returns a plain string (may be empty).
    """
    text = ""
    # Try canonical_text first (often longest)
    cand = doc.get("canonical_text")
    if cand is not None:
        cand_s = to_str_safe(cand).strip()
        if cand_s:
            text = cand_s

    if not text:
        # fall back to title
        title = to_str_safe(doc.get("title"))
        if title:
            text = title

    if not text:
        url = to_str_safe(doc.get("url"))
        if url:
            text = url

    if not text:
        meta = doc.get("meta")
        if meta:
            try:
                if isinstance(meta, dict):
                    meta_vals = " ".join(to_str_safe(v) for v in meta.values() if v is not None)
                    if meta_vals.strip():
                        text = meta_vals
                else:
                    text = to_str_safe(meta)
            except Exception:
                text = ""

    # Final fallback if everything empty
    if not text:
        text = ""

    # Normalize whitespace and cut to first N words
    text = " ".join(text.split())
    words_list = text.split()
    if not words_list:
        return ""
    return " ".join(words_list[:words])

def sample_documents(db_url, n=20, words=20, seed=None):
    # if db_url is None, try to read from environment
    if not db_url:
        db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL is not set. Please set DB_URL in .env or pass --db.")
    conn = psycopg.connect(db_url, row_factory=dict_row)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, url, canonical_text, meta
            FROM documents
            WHERE (canonical_text IS NOT NULL AND length(canonical_text) > 0)
               OR (title IS NOT NULL AND length(title) > 0)
               OR (url IS NOT NULL AND length(url) > 0)
        """)
        docs = cur.fetchall()
    if not docs:
        raise RuntimeError("No suitable documents found to sample from.")
    if seed is not None:
        import random
        random.seed(seed)
    if len(docs) <= n:
        sel = docs
    else:
        sel = sample(docs, n)
    queries = []
    for i, d in enumerate(sel, start=1):
        qtext = safe_text_from_doc(d, words=words)
        if not qtext:
            # fallback: combine title and url
            qtext = " ".join(filter(None, [to_str_safe(d.get("title")), to_str_safe(d.get("url"))])) or "query"
        queries.append({
            "id": f"q{i}",
            "query": qtext,
            "expected_document_ids": [int(d["id"])]
        })
    return queries

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.getenv("DB_URL","postgresql://postgres:postgres@localhost:5432/milan_rag"))
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--words", type=int, default=20)
    p.add_argument("--out", default="tools/ground_truth.json")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    q = sample_documents(args.db, n=args.n, words=args.words, seed=args.seed)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(q, fh, indent=2)
    print("Wrote", args.out)


if __name__ == "__main__":
    main()
