#!/usr/bin/env python3
"""
tools/eval_fusion.py

Evaluate union (ANN + FTS) recall@K.

Usage:
  source .venv/bin/activate
  python tools/eval_fusion.py --queries tools/ground_truth.json --k 10 --k_dense 100 --k_fts 100 --ef_search 64 --out tools/fusion_eval.json
"""
import argparse, json, os, time
import psycopg
from psycopg.rows import dict_row
from statistics import mean
from pathlib import Path
# ensure repo root is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from embeddings.embed_adapter import EmbedAdapter

def pg_connect(db_url):
    return psycopg.connect(db_url, row_factory=dict_row)

def vector_literal(vec):
    return "'[" + ",".join(str(float(x)) for x in vec) + "]'::vector"

def ann_top_doc_ids(conn, qvec, k):
    qvec_text = vector_literal(qvec)
    sql = f"""
    SELECT document_id, (embedding_vector <-> {qvec_text}) AS dist
    FROM chunks
    ORDER BY dist
    LIMIT {k};
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        return [r["document_id"] for r in rows]

def fts_top_doc_ids(conn, query_text, k):
    # use plainto_tsquery for simple phrase parsing
    sql = f"""
    SELECT document_id, MAX(ts_rank(chunk_tsv, plainto_tsquery('english', %s))) AS rank
    FROM chunks
    WHERE chunk_tsv @@ plainto_tsquery('english', %s)
    GROUP BY document_id
    ORDER BY rank DESC
    LIMIT {k};
    """
    with conn.cursor() as cur:
        cur.execute(sql, (query_text, query_text))
        rows = cur.fetchall()
        return [r["document_id"] for r in rows]

def set_ef_search(conn, ef_search):
    try:
        with conn.cursor() as cur:
            cur.execute(f"SET pgvector.hnsw.ef_search = {int(ef_search)};")
            conn.commit()
    except Exception:
        pass

def eval_fusion(db_url, model_doc, queries, top_k=10, k_dense=100, k_fts=100, ef_search=None, batch_size=64, out=None):
    embedder = EmbedAdapter(doc_model=model_doc)
    conn = pg_connect(db_url)
    if ef_search:
        set_ef_search(conn, ef_search)

    results = []
    latencies = []
    hits = []

    for q in queries:
        qid = q.get("id")
        qtext = q.get("query")
        expected = q.get("expected_document_ids", [])
        if not qtext:
            print("Skipping empty query", qid)
            continue

        t0 = time.perf_counter()
        qvec = embedder.embed_many([qtext], source="confluence", batch_size=batch_size)[0]
        ann_docs = ann_top_doc_ids(conn, qvec, k_dense)
        fts_docs = fts_top_doc_ids(conn, qtext, k_fts)
        union_docs = list(dict.fromkeys(ann_docs + fts_docs))  # preserve order preferring ANN then FTS
        elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed)

        # Check recall: is any expected doc in the top 'top_k' of the union?
        found = False
        top_union = union_docs[:top_k]
        for ed in expected:
            if ed in top_union:
                found = True
                break
        hits.append(int(found))
        results.append({
            "qid": qid,
            "query": qtext,
            "expected": expected,
            "ann_docs": ann_docs[:top_k],
            "fts_docs": fts_docs[:top_k],
            "union_top_k": top_union,
            "hit": found,
            "latency_ms": elapsed
        })
        print(f"[{qid}] hit={found} latency={elapsed:.1f}ms union_top_k_size={len(top_union)}")

    summary = {
        "num_queries": len(results),
        "top_k": top_k,
        "k_dense": k_dense,
        "k_fts": k_fts,
        "ef_search": ef_search,
        "avg_latency_ms": mean(latencies) if latencies else None,
        "recall_at_k": sum(hits)/len(hits) if hits else None,
        "details": results
    }

    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        print("Saved fusion evaluation to", out)

    return summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag"))
    p.add_argument("--model_doc", default=os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2"))
    p.add_argument("--queries", required=True)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--k_dense", type=int, default=100)
    p.add_argument("--k_fts", type=int, default=100)
    p.add_argument("--ef_search", type=int, default=None)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    queries = None
    if os.path.exists(args.queries):
        with open(args.queries, "r", encoding="utf-8") as fh:
            queries = json.load(fh)
    else:
        raise RuntimeError("queries file not found: " + args.queries)

    summary = eval_fusion(args.db, args.model_doc, queries, top_k=args.k, k_dense=args.k_dense, k_fts=args.k_fts, ef_search=args.ef_search, batch_size=args.batch_size, out=args.out)
    print("Summary:", json.dumps({
        "num_queries": summary["num_queries"],
        "top_k": summary["top_k"],
        "k_dense": summary["k_dense"],
        "k_fts": summary["k_fts"],
        "ef_search": summary["ef_search"],
        "avg_latency_ms": summary["avg_latency_ms"],
        "recall_at_k": summary["recall_at_k"]
    }, indent=2))

if __name__ == "__main__":
    main()
