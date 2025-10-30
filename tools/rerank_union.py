#!/usr/bin/env python3
"""
tools/rerank_union.py

Given fusion_eval JSON, rerank union_top_k for each query using a CrossEncoder.
Outputs recall@K after rerank.
"""
import json, os
import argparse
from sentence_transformers import CrossEncoder
from psycopg import connect
from psycopg.rows import dict_row
from statistics import mean

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")

def get_chunk_texts(conn, chunk_ids):
    if not chunk_ids:
        return {}
    ids = tuple(chunk_ids)
    sql = f"SELECT id, chunk_text FROM chunks WHERE id IN %s"
    with conn.cursor() as cur:
        cur.execute(sql, (ids,))
        return {r["id"]: r["chunk_text"] for r in cur.fetchall()}

def rerank(fusion_json, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2", top_k=10):
    data = json.load(open(fusion_json))
    conn = connect(DB_URL, row_factory=dict_row)
    model = CrossEncoder(model_name)
    recalls = []
    latencies = []
    for d in data["details"]:
        q = d["query"]
        union = d["ann_docs"][:200] + [x for x in d["fts_docs"][:200] if x not in d["ann_docs"]]
        # union is list of document_ids — we need chunk-level ids. For simplicity, pick top chunk per doc:
        # get one chunk id per doc (best chunk) — naive approach: pick any chunk
        chunk_map = {}
        doc_chunk_ids = []
        for doc in union:
            with conn.cursor() as cur:
                cur.execute("SELECT id, chunk_text FROM chunks WHERE document_id=%s LIMIT 1", (doc,))
                row = cur.fetchone()
                if row:
                    doc_chunk_ids.append(row["id"])
                    chunk_map[row["id"]] = row["chunk_text"]
        if not doc_chunk_ids:
            recalls.append(0)
            continue
        # prepare pairs
        pairs = [(q, chunk_map[cid]) for cid in doc_chunk_ids]
        scores = model.predict(pairs)
        zipped = list(zip(doc_chunk_ids, doc_chunk_ids))  # placeholder
        # pair ids with scores
        scored = list(zip(doc_chunk_ids, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        reranked_docs = [doc for (cid, s) in scored for doc in union if True]  # awkward: we need doc ids - we only have chunk_ids
        # For a fast approach, get document_id for each chunk:
        ordered_docs = []
        for cid, s in scored:
            with conn.cursor() as cur:
                cur.execute("SELECT document_id FROM chunks WHERE id=%s", (cid,))
                r = cur.fetchone()
                if r:
                    ordered_docs.append(r["document_id"])
        top_docs = ordered_docs[:top_k]
        expected = d.get("expected", [])
        hit = int(any(e in top_docs for e in expected))
        recalls.append(hit)
    summary = {"recall_at_k": sum(recalls)/len(recalls) if recalls else None}
    return summary
