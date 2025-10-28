#!/usr/bin/env python3
import os
from storage.postgres import PostgresStorage

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")

s = PostgresStorage(DB_URL)
docid = s.insert_document("test doc for chunk insert", "http://example.local/test", {"test":True})
# example embedding vector: 384 dims of small values (adjust if your vector dim differs)
emb = [0.001 * (i % 10) for i in range(384)]
chunkid = s.insert_chunk(docid, "This is a test chunk for verifying typed embedding insert.", emb, {"note":"test"})
print("Inserted docid", docid, "chunkid", chunkid)
