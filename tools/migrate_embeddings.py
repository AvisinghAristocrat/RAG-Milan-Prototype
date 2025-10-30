#!/usr/bin/env python3
"""
Migrate JSONB embeddings in `chunks.embedding` into `chunks.embedding_vector` (pgvector).
Runs in batches and updates rows in a single transaction per batch.

Usage:
  source .venv/bin/activate
  python tools/migrate_embeddings.py --batch 200
  python tools/migrate_embeddings.py --dry-run
"""
import os
import json
import argparse
import time
import psycopg
from psycopg.rows import dict_row

DB_URL_DEFAULT = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")


def column_exists(conn: psycopg.Connection, table: str, column: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        return cur.fetchone() is not None


def count_rows_to_migrate(conn: psycopg.Connection) -> int:
    # Returns count of rows where embedding_vector IS NULL AND embedding IS NOT NULL
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='chunks' AND column_name='embedding'"
        )
        legacy_exists = cur.fetchone()[0] > 0
        if not legacy_exists:
            return 0
        cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_vector IS NULL AND embedding IS NOT NULL;")
        return cur.fetchone()[0]


def fetch_batch(conn: psycopg.Connection, batch_size: int):
    # Fetch a single batch of rows needing migration
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, embedding FROM chunks WHERE embedding_vector IS NULL AND embedding IS NOT NULL LIMIT %s",
            (batch_size,),
        )
        rows = cur.fetchall()
        return rows


def normalize_embedding_value(emb_value):
    """
    Normalize embedding field into a Python list of floats.
    emb_value may be:
      - JSONB returned as Python list
      - string containing JSON array
      - other -> return None
    """
    if emb_value is None:
        return None
    if isinstance(emb_value, (list, tuple)):
        return emb_value
    if isinstance(emb_value, str):
        # Try to parse JSON
        try:
            parsed = json.loads(emb_value)
            if isinstance(parsed, (list, tuple)):
                return parsed
        except Exception:
            # Not JSON — cannot handle
            return None
    # Unknown type
    return None


def update_batch(conn: psycopg.Connection, rows, dry_run=False):
    """
    Update rows: rows is list of dicts {'id':..., 'embedding':...}
    For each row, build vector literal "[0.1,0.2,...]" and update embedding_vector.
    """
    migrated = 0
    if not rows:
        return migrated

    with conn.cursor() as cur:
        for r in rows:
            cid = r["id"]
            emb_raw = r["embedding"]
            emb_list = normalize_embedding_value(emb_raw)
            if emb_list is None:
                print(f"[WARN] id={cid}: cannot normalize embedding, skipping")
                continue
            # Try convert all items to float
            try:
                emb_floats = [float(x) for x in emb_list]
            except Exception as e:
                print(f"[WARN] id={cid}: embedding contains non-numeric values: {e}; skipping")
                continue
            # Build vector literal
            vec_text = "[" + ",".join(map(str, emb_floats)) + "]"
            if dry_run:
                migrated += 1
                continue
            # Parameterize id, but the vector literal is casted in SQL.
            # Use %s placeholders for psycopg safe parameters.
            try:
                cur.execute("UPDATE chunks SET embedding_vector = %s::vector WHERE id = %s", (vec_text, cid))
            except Exception as e:
                print(f"[ERROR] id={cid}: failed to update embedding_vector: {e}")
                # continue rather than abort whole batch
                continue
            migrated += 1
        if not dry_run:
            conn.commit()
    return migrated


def migrate(db_url: str, batch_size: int = 200, dry_run: bool = False):
    print(f"[INFO] Connecting to DB: {db_url}")
    with psycopg.connect(db_url) as conn:
        # Check for legacy column
        legacy_exists = column_exists(conn, "chunks", "embedding")
        vec_exists = column_exists(conn, "chunks", "embedding_vector")
        if not legacy_exists:
            print("[INFO] No legacy 'embedding' column found on chunks. Nothing to migrate.")
            return 0
        if not vec_exists:
            print("[ERROR] 'embedding_vector' column does not exist on chunks. Please add it and retry.")
            return 0

        total_need = count_rows_to_migrate(conn)
        print(f"[INFO] Total rows needing migration: {total_need}")
        if total_need == 0:
            return 0
        if dry_run:
            print("[INFO] Dry-run mode. No updates will be performed.")
            return total_need

        migrated_total = 0
        start_time = time.time()
        while True:
            rows = fetch_batch(conn, batch_size)
            if not rows:
                break
            print(f"[INFO] Processing batch of {len(rows)}")
            migrated = update_batch(conn, rows, dry_run=dry_run)
            migrated_total += migrated
            elapsed = time.time() - start_time
            print(f"[INFO] Migrated so far: {migrated_total}/{total_need} rows (elapsed {elapsed:.1f}s)")
        print(f"[INFO] Migration complete. Total migrated: {migrated_total}")
        return migrated_total


def main():
    parser = argparse.ArgumentParser(description="Migrate JSONB embeddings -> pgvector embedding_vector")
    parser.add_argument("--db", default=DB_URL_DEFAULT, help="Database URL")
    parser.add_argument("--batch", type=int, default=200, help="Batch size")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes")
    args = parser.parse_args()

    try:
        migrated = migrate(args.db, batch_size=args.batch, dry_run=args.dry_run)
        print("Result: migrated rows:", migrated)
    except Exception as e:
        print("[FATAL] Migration error:", e)
        raise


if __name__ == "__main__":
    main()
