#!/usr/bin/env python3
"""
tools/check_similarity.py

For each failure in a fusion analysis JSON, compute:
  - query embedding (doc model)
  - embeddings for the expected document's chunks
  - report the max cosine similarity between query and any chunk of the expected doc

Usage:
  source .venv/bin/activate
  python tools/check_similarity.py --fusion tools/fusion_analysis_ef64.json --out tools/similarity_ef64.json
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
import psycopg
from psycopg.rows import dict_row

# ensure repo root on sys.path for local imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from embeddings.embed_adapter import EmbedAdapter

def pg_connect(db_url):
    return psycopg.connect(db_url, row_factory=dict_row)

def fetch_chunks_for_doc(conn, doc_id, limit=None):
    with conn.cursor() as cur:
        if limit:
            cur.execute("SELECT id, chunk_text FROM chunks WHERE document_id=%s ORDER BY id LIMIT %s", (doc_id, limit))
        else:
            cur.execute("SELECT id, chunk_text FROM chunks WHERE document_id=%s ORDER BY id", (doc_id,))
        return cur.fetchall()

def cosine_sim(a, b):
    # a: 1D array, b: 2D array (n x d) => returns array of cosine sims
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    if a.size == 0 or b.size == 0:
        return np.array([])
    aa = np.linalg.norm(a)
    bb = np.linalg.norm(b, axis=1)
    # avoid div by zero
    denom = aa * bb
    denom[denom == 0] = 1e-12
    sims = np.dot(b, a) / denom
    return sims

def analyze(fusion_json, db_url, model_doc, out_path=None, chunk_limit=200, embed_batch=64):
    print("Loading fusion analysis:", fusion_json)
    J = json.load(open(fusion_json, "r", encoding="utf-8"))
    failures = J.get("failures", [])
    print("Failures:", len(failures))
    conn = pg_connect(db_url)
    embedder = EmbedAdapter(doc_model=model_doc)
    results = []
    for f in failures:
        qid = f.get("qid")
        query = f.get("query")
        expected_docs_info = f.get("expected_docs_info", [])
        rec = {"qid": qid, "query": query, "expected": [], "ann": f.get("ann_docs"), "fts": f.get("fts_docs"), "union_top_k": f.get("union_top_k")}
        # embed the query
        try:
            qvec = embedder.embed_many([query], source="confluence", batch_size=embed_batch)[0]
        except Exception as e:
            qvec = None
            rec["query_embed_error"] = str(e)
        for ed in expected_docs_info:
            doc_id = ed.get("doc_id")
            info = {"doc_id": doc_id, "exists": ed.get("exists"), "title": ed.get("title")}
            if not ed.get("exists"):
                info["note"] = "doc missing"
                rec["expected"].append(info)
                continue
            # fetch chunks
            chunks = fetch_chunks_for_doc(conn, doc_id, limit=chunk_limit)
            info["num_chunks"] = len(chunks)
            texts = [c["chunk_text"] for c in chunks]
            # guard: remove empty texts
            texts = [t if t is not None else "" for t in texts]
            info["sample_chunks"] = [{"id": c["id"], "sample": (c["chunk_text"] or "")[:400]} for c in chunks[:3]]
            if not texts:
                info["note"] = "no chunks"
                rec["expected"].append(info)
                continue
            # embed chunks in batches
            try:
                embeddings = []
                for i in range(0, len(texts), embed_batch):
                    batch_texts = texts[i:i+embed_batch]
                    emb_batch = embedder.embed_many(batch_texts, source="confluence", batch_size=embed_batch)
                    embeddings.extend(emb_batch)
                embeddings = np.array(embeddings, dtype=np.float32)
            except Exception as e:
                info["embed_error"] = str(e)
                rec["expected"].append(info)
                continue
            # compute max cosine similarity between qvec and chunk embeddings
            if qvec is None:
                info["max_sim"] = None
            else:
                sims = cosine_sim(qvec, embeddings)
                info["max_sim"] = float(np.max(sims)) if sims.size else None
                info["mean_sim"] = float(np.mean(sims)) if sims.size else None
            rec["expected"].append(info)
        results.append(rec)
    out = {"summary": {"failures": len(failures)}, "details": results}
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print("Wrote analysis to", out_path)
    return out

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--fusion", required=True)
    p.add_argument("--db", default=os.getenv("DB_URL","postgresql://postgres:postgres@localhost:5432/milan_rag"))
    p.add_argument("--model_doc", default=os.getenv("DOC_EMBED_MODEL","all-MiniLM-L6-v2"))
    p.add_argument("--out", default="tools/similarity_results.json")
    p.add_argument("--chunk_limit", type=int, default=200)
    args = p.parse_args()
    analyze(args.fusion, args.db, args.model_doc, out_path=args.out, chunk_limit=args.chunk_limit)
