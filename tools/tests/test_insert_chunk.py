#!/usr/bin/env python3
"""
Test insertion using PostgresStorage with the current document signature.
Run from the repo root as: python -m tools.test_insert_chunk
"""
import os
import uuid
from storage.postgres import PostgresStorage

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")

def main():
    s = PostgresStorage(DB_URL)
    # document args adapted to the new API: source, external_id, title, url, content_hash, canonical_text, meta, last_modified
    source = "confluence"
    external_id = str(uuid.uuid4())
    title = "test doc for chunk insert"
    url = "http://example.local/test"
    content_hash = None
    canonical_text = None
    meta = {"test": True}
    last_modified = None

    docid = s.insert_document(source, external_id, title, url, content_hash, canonical_text, meta, last_modified)
    print("Inserted docid", docid)

    # example embedding vector: 384 dims (adjust if vector dim differs)
    emb = [0.001 * (i % 10) for i in range(384)]
    chunkid = s.insert_chunk(docid, "This is a test chunk for verifying typed embedding insert.", emb, {"note":"test"})
    print("Inserted chunkid", chunkid)

if __name__ == "__main__":
    main()
