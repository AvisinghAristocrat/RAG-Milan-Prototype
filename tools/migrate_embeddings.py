#!/usr/bin/env python3
"""
Migrate JSONB embeddings in `chunks.embedding` into `chunks.embedding_vector` (pgvector).
Runs in batches and updates rows in a single transaction per batch.
Usage: python tools/migrate_embeddings.py --batch 200
"""

import os
import json
import argparse
import psycopg
from psycopg.rows import dict_row

def migrate(db_url, batch_size=200, dry_run=False):
    with psycopg.connect(db_url, autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cur_select:
            # Count to report
            cur_select.execute("SELECT COUNT(*) AS need_migrate FROM chunks WHERE embedding_vector IS NULL AND embedding IS NOT NULL;")
            need = cur_select.fetchone()["need_migrate"]
            print(f"Rows needing migration: {need}")
            if need == 0:
                return

            cur_select.execute("SELECT id, embedding FROM chunks WHERE embedding_vector IS NULL AND embedding IS NOT NULL;")
            rows = cur_select.fetchmany(batch_size)
            total = 0
            while rows:
                print(f"Processing batch of {len(rows)}")
                if not dry_run:
                    with conn.cursor() as cur_update:
                        for r in rows:
                            cid = r["id"]
                            emb_json = r["embedding"]
                            # emb_json might be JSONB already, ensure Python list
                            if isinstance(emb_json, str):
                                try:
                                    emb = json.loads(emb_json)
                                except Exception as e:
                                    print(f"Skipping id={cid} malformed JSON: {e}")
                                    continue
                            else:
                                emb = emb_json
                            # Build vector literal string like: [0.123,0.234,...]
                            vec_text = "[" + ",".join(str(float(x)) for x in emb) + "]"
                            # Update typed column using cast to vector
                            # Use parameterized query; pass the vector text and id
                            sql = "UPDATE chunks SET embedding_vector = %s::vector WHERE id = %s"
                            cur_update.execute(sql, (vec_text, cid))
                        conn.commit()
                else:
                    print("Dry run - not updating. Would process this batch.")
                total += len(rows)
                rows = cur_select.fetchmany(batch_size)
            print(f"Migrated (or would migrate) total: {total}")

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=200, help="Batch size")
    p.add_argument("--dry-run", action="store_true", help="Do not write changes")
    args = p.parse_args()
    DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
    migrate(DB_URL, batch_size=args.batch, dry_run=args.dry_run)
