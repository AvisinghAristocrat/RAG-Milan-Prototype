#!/usr/bin/env python3
"""
tools/analyze_misses.py
Given a fusion eval JSON output, list failed queries and show:
 - expected doc ids
 - ann_docs, fts_docs, union_top_k
 - whether expected doc exists in DB and show some chunks
"""
import json, os, sys
from psycopg import connect
from psycopg.rows import dict_row

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")

def sample_chunks_for_doc(conn, docid, limit=3):
    with conn.cursor() as cur:
        cur.execute("SELECT id, substring(chunk_text,1,300) as sample FROM chunks WHERE document_id=%s LIMIT %s", (docid, limit))
        return cur.fetchall()

def analyze(fusion_json_path, out_path=None, max_show=20):
    data = json.load(open(fusion_json_path))
    fails = [d for d in data["details"] if not d.get("hit")]
    print(f"Total queries: {data['num_queries']}. Failures: {len(fails)}")
    conn = connect(DB_URL, row_factory=dict_row)
    report = {"num_queries":data['num_queries'], "failures": []}
    for i, f in enumerate(fails[:max_show], start=1):
        qid = f["qid"]
        expected = f.get("expected", [])
        ann = f.get("ann_docs", [])
        fts = f.get("fts_docs", [])
        union = f.get("union_top_k", [])
        rec = {"qid": qid, "query": f.get("query"), "expected": expected, "ann": ann, "fts": fts, "union_top_k": union}
        # for each expected doc, show if doc exists and sample chunks
        rec["expected_docs_info"] = []
        for ed in expected:
            info = {"doc_id": ed}
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, url FROM documents WHERE id=%s", (ed,))
                row = cur.fetchone()
                if row:
                    info["exists"] = True
                    info["title"] = row["title"]
                    info["url"] = row["url"]
                    # sample chunks
                    try:
                        chunks = sample_chunks_for_doc(conn, ed, limit=3)
                        info["chunks"] = [{ "id": c["id"], "sample": c["sample"] } for c in chunks]
                    except Exception as e:
                        info["chunks_error"] = str(e)
                else:
                    info["exists"] = False
                rec["expected_docs_info"].append(info)
        report["failures"].append(rec)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print("Wrote analysis to", out_path)

    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/analyze_misses.py fusion_eval.json [out.json]")
        sys.exit(1)
    fusion_json = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    r = analyze(fusion_json, out)
    print("Done. Failures shown (sample).")
