# storage/postgres.py
import os
import json
import time
from typing import Any, Dict, Optional, Tuple

import psycopg
from psycopg.rows import dict_row

class PostgresStorage:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # Simple persistent connection. For production, use a pool.
        self.conn = psycopg.connect(self.db_url, autocommit=False)

    def create_tables(self):
        # Migration should have created tables already. Keep this method no-op
        # to avoid schema drift. If you want this to ensure schema exists,
        # implement DDL here (but we used migrations earlier).
        return

    # DOCUMENT helpers
    def get_document_by_source_external(self, source: str, external_id: str) -> Optional[Dict[str, Any]]:
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, content_hash, title, url, meta, last_modified FROM documents WHERE source = %s AND external_id = %s",
                (source, external_id)
            )
            row = cur.fetchone()
            return row

    def insert_document(self, source: str, external_id: str, title: str, url: str,
                        content_hash: Optional[str] = None, canonical_text: Optional[str] = None,
                        meta: Optional[Dict[str, Any]] = None, last_modified: Optional[str] = None) -> int:
        meta = meta or {}
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (source, external_id, title, url, content_hash, canonical_text, meta, last_modified)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (source, external_id) DO UPDATE
                  SET title = EXCLUDED.title,
                      url = EXCLUDED.url,
                      content_hash = EXCLUDED.content_hash,
                      canonical_text = EXCLUDED.canonical_text,
                      meta = EXCLUDED.meta,
                      last_modified = EXCLUDED.last_modified
                RETURNING id;
                """,
                (source, external_id, title, url, content_hash, canonical_text, json.dumps(meta), last_modified)
            )
            docid = cur.fetchone()[0]
            self.conn.commit()
            return docid

    def update_document_content(self, docid: int, content_hash: str, canonical_text: str, meta: Dict[str, Any], last_modified: Optional[str] = None):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET content_hash = %s, canonical_text = %s, meta = %s, last_modified = %s WHERE id = %s",
                (content_hash, canonical_text, json.dumps(meta), last_modified, docid)
            )
            self.conn.commit()

    # CHUNK helpers
    def delete_chunks_for_document(self, document_id: int):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
            self.conn.commit()

    def insert_chunk(self, document_id: int, chunk_text: str, embedding: Optional[Any], meta: Dict[str, Any] = None) -> int:
        """
        Inserts chunk into chunks table. Writes to embedding_vector if available,
        otherwise stores embedding into an 'embedding' JSONB column (if present).
        embedding: list[float] or None
        """
        meta = meta or {}

        # Prepare vector literal if embedding provided
        vec_text = None
        emb_list = None
        if embedding is not None:
            if isinstance(embedding, str):
                try:
                    emb_list = json.loads(embedding)
                except Exception:
                    # Fallback: parse bracketed text
                    emb_list = [float(x) for x in embedding.strip("[] ").split(",") if x.strip() != ""]
            else:
                emb_list = embedding
            vec_text = "[" + ",".join(str(float(x)) for x in emb_list) + "]"

        with self.conn.cursor() as cur:
            # Check if embedding_vector column exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='chunks' AND column_name='embedding_vector';
            """)
            has_embedding_vector = cur.fetchone() is not None

            if vec_text is not None and has_embedding_vector:
                cur.execute(
                    """
                    INSERT INTO chunks (document_id, chunk_text, embedding_vector, meta)
                    VALUES (%s, %s, %s::vector, %s)
                    RETURNING id
                    """,
                    (document_id, chunk_text, vec_text, json.dumps(meta))
                )
            else:
                # fallback: insert into JSONB 'embedding' if exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='chunks' AND column_name='embedding';
                """)
                has_json_embedding = cur.fetchone() is not None
                if vec_text is not None and has_json_embedding:
                    cur.execute(
                        """
                        INSERT INTO chunks (document_id, chunk_text, embedding, meta)
                        VALUES (%s, %s, %s::jsonb, %s)
                        RETURNING id
                        """,
                        (document_id, chunk_text, json.dumps(emb_list), json.dumps(meta))
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO chunks (document_id, chunk_text, meta)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (document_id, chunk_text, json.dumps(meta))
                    )

            cid = cur.fetchone()[0]
            self.conn.commit()
            return cid
