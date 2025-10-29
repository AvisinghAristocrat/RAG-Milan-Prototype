#!/usr/bin/env python3
# tools/rechunk_documents.py
import os, sys, math, time
from typing import Optional, List
import psycopg
from psycopg.rows import dict_row
from embeddings.embed_adapter import EmbedAdapter
from ingesters import confluence_ingest, github_ingest

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
BATCH = int(os.getenv("RECHUNK_BATCH", "32"))  # number of documents processed per loop
EMBED_BATCH = int(os.getenv("EMBED_BATCH", "64"))

embed_adapter = EmbedAdapter(doc_model=os.getenv("DOC_EMBED_MODEL","all-MiniLM-L6-v2"),
                             code_model=os.getenv("CODE_EMBED_MODEL", None))

def fetch_doc_ids(conn, space: Optional[str], limit: Optional[int] = None):
    with conn.cursor(row_factory=dict_row) as cur:
        if space:
            sql = "SELECT id FROM documents WHERE (meta->>'space') = %s ORDER BY id"
            params = (space,)
        else:
            sql = "SELECT id FROM documents ORDER BY id"
            params = ()
        if limit:
            sql = sql + " LIMIT %s"
            params = params + (limit,)
        cur.execute(sql, params)
        return [r["id"] for r in cur.fetchall()]

def get_document(conn, docid: int):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id, source, external_id, canonical_text, title, url, meta FROM documents WHERE id = %s", (docid,))
        return cur.fetchone()

def rechunk_document(conn, doc, embed_adapter, chunk_chars=1000, overlap=150):
    # doc is dict row
    canonical = doc.get("canonical_text") or ""
    if not canonical:
        print(f"[WARN] doc {doc['id']} has empty canonical_text; skipping")
        return 0

    # choose chunker
    if doc.get("source") and doc.get("source").lower() in ("github", "repo", "code"):
        chunks = github_ingest.chunk_file(canonical, chunk_size=chunk_chars, overlap=overlap) if hasattr(github_ingest, "chunk_file") else []
    else:
        chunks = confluence_ingest.chunk_page(canonical, chunk_chars, overlap)

    texts = [c["text"] for c in chunks]
    if not texts:
        return 0

    # compute embeddings in batches
    embeddings = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i+EMBED_BATCH]
        emb_batch = embed_adapter.embed_many(batch, source=doc.get("source", "confluence"), batch_size=EMBED_BATCH)
        embeddings.extend(emb_batch)

    # replace chunks within transaction for this document
    with conn.cursor() as cur:
        # delete old
        cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc["id"],))
        # bulk insert new
        for text, emb in zip(texts, embeddings):
            vec_txt = "[" + ",".join(str(float(x)) for x in emb) + "]"
            cur.execute("INSERT INTO chunks (document_id, chunk_text, embedding_vector, meta, created_at) VALUES (%s, %s, %s::vector, %s, now())",
                        (doc["id"], text, vec_txt, doc.get("meta") or {}))
        conn.commit()
    return len(texts)

def main(space: Optional[str]=None, limit: Optional[int]=None):
    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        doc_ids = fetch_doc_ids(conn, space, limit)
        total = len(doc_ids)
        print(f"Found {total} docs to rechunk in space={space}")
        processed = 0
        for docid in doc_ids:
            doc = get_document(conn, docid)
            try:
                new_chunks = rechunk_document(conn, doc, embed_adapter)
                processed += 1
                print(f"[{processed}/{total}] doc {docid} => {new_chunks} chunks")
            except Exception as e:
                print(f"[ERR] doc {docid} failed: {e}")
        print("Done")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--space", help="space key to restrict rechunk (optional)")
    p.add_argument("--limit", type=int, help="limit number of docs to process (optional)")
    args = p.parse_args()
    main(space=args.space, limit=args.limit)
