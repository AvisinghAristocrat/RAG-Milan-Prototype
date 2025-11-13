import os
import json
import sys
try:
    import psycopg
    from psycopg.rows import dict_row
except Exception as e:
    print("psycopg not available. Activate venv and install requirements.", file=sys.stderr)
    raise

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    print(
        "Please set DB_URL environment variable.\n"
        "Example (use real credentials only in your environment, do NOT commit them):\n"
        "  export DB_URL='postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB>'\n"
        "Then run: python tools/db_sanity.py"
    )
    sys.exit(1)

def run(conn, sql, params=None):
    """Run a single SQL statement using its own cursor; return rows or an error dict."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            try:
                rows = cur.fetchall()
                return rows
            except Exception:
                # no rows to fetch (e.g., DDL) -> return empty list
                return []
    except Exception as e:
        return {"__error__": str(e)}

def main():
    out = {"ok": True, "checks": {}}
    expected_dim = 384

    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        # 1) list indexes on chunks
        idx_sql = "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='chunks';"
        out["checks"]["pg_indexes_chunks"] = run(conn, idx_sql)

        # 2) count missing vectors
        missing_sql = "SELECT COUNT(*) AS missing_vectors FROM chunks WHERE embedding_vector IS NULL;"
        mv = run(conn, missing_sql)
        out["checks"]["missing_vectors"] = mv[0]["missing_vectors"] if isinstance(mv, list) and mv else mv

        # 3) check presence of important columns
        cols_sql = """
        SELECT column_name, udt_name FROM information_schema.columns
         WHERE table_name='chunks' AND column_name IN ('chunk_tsv','created_at','embedding_vector');
        """
        out["checks"]["chunks_columns"] = run(conn, cols_sql)

        # 4) compute embedding dimension safely by casting vector to text and splitting on commas
        dim_sql = """
        SELECT array_length(
            regexp_split_to_array(trim(BOTH '[]' FROM embedding_vector::text), ',\\s*'), 1
        ) AS dim
        FROM chunks WHERE embedding_vector IS NOT NULL LIMIT 1;
        """
        dim = run(conn, dim_sql)
        try:
            if isinstance(dim, list) and dim:
                out["checks"]["embedding_dim"] = dim[0].get("dim")
            else:
                out["checks"]["embedding_dim"] = None
                if isinstance(dim, dict) and "__error__" in dim:
                    out["checks"]["embedding_dim_error"] = dim["__error__"]
        except Exception as e:
            out["checks"]["embedding_dim_error"] = str(e)
            out["checks"]["embedding_dim"] = None

        # 5) count rows with dimension != expected (384) — only if we got a dim result
        try:
            if out["checks"].get("embedding_dim"):
                dim_check_sql = """
                SELECT COUNT(*) AS wrong_dim_count
                FROM (
                  SELECT array_length(regexp_split_to_array(trim(BOTH '[]' FROM embedding_vector::text), ',\\s*'),1) as dim
                  FROM chunks WHERE embedding_vector IS NOT NULL
                ) q WHERE dim != %s;
                """
                drows = run(conn, dim_check_sql, (expected_dim,))
                out["checks"]["wrong_dim_count"] = drows[0]["wrong_dim_count"] if isinstance(drows, list) and drows else None
            else:
                out["checks"]["wrong_dim_count"] = None
        except Exception as e:
            out["checks"]["wrong_dim_count_error"] = str(e)
            out["checks"]["wrong_dim_count"] = None

        # 6) check chunk_tsv index exists (use parameter to avoid psycopg placeholder issues)
        tsv_idx_sql = "SELECT indexname FROM pg_indexes WHERE tablename='chunks' AND indexdef ILIKE %s;"
        tsv_idx = run(conn, tsv_idx_sql, ('%chunk_tsv%',))
        if isinstance(tsv_idx, dict) and "__error__" in tsv_idx:
            out["checks"]["chunk_tsv_index_error"] = tsv_idx["__error__"]
            out["checks"]["chunk_tsv_index_exists"] = False
        else:
            out["checks"]["chunk_tsv_index_exists"] = bool(tsv_idx) and isinstance(tsv_idx, list) and len(tsv_idx) > 0

        # 7) list HNSW indexes and look for operator class mention (parameterized)
        hnsw_sql = "SELECT indexname, indexdef FROM pg_indexes WHERE tablename='chunks' AND indexdef ILIKE %s;"
        hnsw = run(conn, hnsw_sql, ('%hnsw%',))
        out["checks"]["hnsw_indexes"] = hnsw
        if isinstance(hnsw, list):
            oc = []
            for row in hnsw:
                idxdef = row.get("indexdef","").lower()
                oc.append({"indexname": row["indexname"], "has_vector_op": ("vector_l2_ops" in idxdef or "vector_l2_ops" in idxdef)})
            out["checks"]["hnsw_operator_classes"] = oc

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
