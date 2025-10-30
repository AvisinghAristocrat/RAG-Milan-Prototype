#!/usr/bin/env python3
"""
tools/eval_ann.py - importable evaluator for ANN

Usage (CLI):
  python tools/eval_ann.py --queries tools/ground_truth.json --k 10 --ef_search 64 --out tools/ann_eval.json

When imported:
  from tools.eval_ann import eval_ann
  summary = eval_ann(db_url, model_doc, queries_file, top_k, ef_search, batch_size, out)
"""
import argparse
import json
import time
import os
from statistics import mean
import sys
from pathlib import Path

# Ensure repo root is on sys.path so 'embeddings' and other modules are importable
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Now safe to import local modules
import psycopg
from psycopg.rows import dict_row

# Import the embed adapter
from embeddings.embed_adapter import EmbedAdapter

def pg_connect(db_url):
    return psycopg.connect(db_url, row_factory=dict_row)

def vector_literal(vec):
    """Return a postgres vector literal like '[0.1,0.2,...]'::vector"""
    return "'[" + ",".join(str(float(x)) for x in vec) + "]'::vector"

def run_query_pg(conn, qvec, top_k):
    qvec_text = vector_literal(qvec)
    sql = f"""
    SELECT document_id, id AS chunk_id
    FROM chunks
    ORDER BY embedding_vector <-> {qvec_text}
    LIMIT {top_k};
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        return [r["document_id"] for r in rows]

def set_ef_search(conn, ef_search):
    try:
        with conn.cursor() as cur:
            cur.execute(f"SET pgvector.hnsw.ef_search = {int(ef_search)};")
            conn.commit()
    except Exception:
        # not fatal; session setting might not be supported
        pass

def eval_ann(db_url, model_doc, queries_file_or_list, top_k=10, ef_search=None, batch_size=64, out=None):
    """
    db_url: Postgres connection URL
    model_doc: name of doc embedding model (EmbedAdapter will load)
    queries_file_or_list: path to JSON file OR a Python list of query dicts
    Returns summary dict.
    """
    embedder = EmbedAdapter(doc_model=model_doc)
    conn = pg_connect(db_url)
    if ef_search:
        set_ef_search(conn, ef_search)

    # load queries
    if isinstance(queries_file_or_list, str) and os.path.exists(queries_file_or_list):
        with open(queries_file_or_list, "r", encoding="utf-8") as fh:
            qdata = json.load(fh)
    elif isinstance(queries_file_or_list, list):
        qdata = queries_file_or_list
    else:
        raise ValueError("queries_file_or_list must be a path to JSON or a list of query dicts")

    results = []
    latencies = []
    recalls = []

    for q in qdata:
        qid = q.get("id") or q.get("qid") or str(time.time())
        query_text = q.get("query")
        expected = q.get("expected_document_ids", [])  # list of ints
        if not query_text:
            print("Skipping empty query", qid)
            continue

        start = time.perf_counter()
        qvec = embedder.embed_many([query_text], source="confluence", batch_size=batch_size)[0]
        doc_ids = run_query_pg(conn, qvec, top_k)
        elapsed = (time.perf_counter() - start) * 1000.0  # ms
        latencies.append(elapsed)

        hit = 0
        for ed in expected:
            if ed in doc_ids:
                hit = 1
                break
        recalls.append(hit)
        results.append({
            "qid": qid,
            "query": query_text,
            "expected": expected,
            "returned": doc_ids,
            "hit": bool(hit),
            "latency_ms": elapsed
        })
        print(f"[{qid}] hit={hit} latency={elapsed:.1f}ms returned={len(doc_ids)}")

    summary = {
        "num_queries": len(results),
        "top_k": top_k,
        "ef_search": ef_search,
        "avg_latency_ms": mean(latencies) if latencies else None,
        "recall_at_k": sum(recalls) / len(recalls) if recalls else None,
        "details": results
    }

    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        print("Saved evaluation to", out)

    return summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag"))
    p.add_argument("--model_doc", default=os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2"))
    p.add_argument("--queries", required=True, help="path to ground truth JSON")
    p.add_argument("--k", type=int, default=10, help="top-K to evaluate")
    p.add_argument("--ef_search", type=int, default=None, help="hnsw ef_search")
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    print("DB:", args.db)
    print("Model (doc):", args.model_doc)
    print("Queries file:", args.queries)
    print("Top-K:", args.k, "ef_search:", args.ef_search)

    summary = eval_ann(args.db, args.model_doc, args.queries, args.k, args.ef_search, args.batch_size, args.out)
    print("Summary:", json.dumps({
        "num_queries": summary["num_queries"],
        "top_k": summary["top_k"],
        "ef_search": summary["ef_search"],
        "avg_latency_ms": summary["avg_latency_ms"],
        "recall_at_k": summary["recall_at_k"]
    }, indent=2))

if __name__ == "__main__":
    main()
