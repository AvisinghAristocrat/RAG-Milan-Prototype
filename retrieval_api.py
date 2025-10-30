"""
Retrieval API - complete
Endpoints:
 - GET /health
 - POST /test_connectors
 - POST /confluence/page_ids
 - POST /ingest/confluence
 - POST /ingest/github
 - GET/POST /query
 - GET /diagnostics
"""
from __future__ import annotations
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Body, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# load .env so API process sees credentials if present
load_dotenv()

# project modules (connectors/ingesters/storage/embeddings)
from connectors import confluence as conf_conn
from connectors import github as gh_conn
from ingesters import confluence_ingest, github_ingest
from storage.postgres import PostgresStorage
from embeddings.embed_adapter import EmbedAdapter
from mcp.mcp import assemble_mcp_context, log_mcp

import hashlib
import psycopg
from psycopg.rows import dict_row

import json
import uuid
import subprocess
import sys 
from pathlib import Path

app = FastAPI(title="Milan RAG - Retrieval API")

# config
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

# globals populated at startup
storage: Optional[PostgresStorage] = None
embed_adapter: Optional[EmbedAdapter] = None

# -----------------------
# request/response models
# -----------------------
class ConnectorTest(BaseModel):
    type: str
    base_url: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    repo: Optional[str] = None


class PageIdsRequest(BaseModel):
    base_url: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    space_key: Optional[str] = None
    page_id: Optional[str] = None
    limit: int = 100


class PageIdsResponseItem(BaseModel):
    id: str
    title: Optional[str]
    url: Optional[str]


class IngestByPageIdsRequest(BaseModel):
    base_url: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    space_key: Optional[str] = None
    page_id: Optional[str] = None
    page_ids: Optional[List[str]] = None
    erase_existing: bool = False
    max_docs: Optional[int] = None   # None = full ingest (no artificial cap)


class IngestGithubRequest(BaseModel):
    repo: str
    token: Optional[str] = None
    branch: str = "main"

# -----------------------
# utilities
# -----------------------
def wait_for_db(url: str, timeout: int = 60):
    """Poll until Postgres accepts connection or raise."""
    start = time.time()
    while True:
        try:
            conn = psycopg.connect(url)
            conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise RuntimeError(f"Timed out waiting for DB at {url}")
            time.sleep(1)

def _vec_to_literal(vec: List[float]) -> str:
    """Turn python list of floats into Postgres vector literal text like [0.1,0.2,...]."""
    return "[" + ",".join(str(float(x)) for x in vec) + "]"

def _extract_last_modified_from_meta(meta: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Given Confluence meta (possibly containing a 'version' dict), extract a scalar
    last_modified value. Prefer 'when' timestamp, else 'number', else None.
    """
    if not meta or not isinstance(meta, dict):
        return None
    version_obj = meta.get("version") or meta.get("lastModified") or None
    if isinstance(version_obj, dict):
        return version_obj.get("when") or version_obj.get("number")
    # if version_obj is a scalar, return as-is
    return version_obj

# -----------------------
# startup
# -----------------------
@app.on_event("startup")
def startup():
    global storage, embed_adapter
    # wait for DB to be reachable
    wait_for_db(DB_URL, timeout=60)
    storage = PostgresStorage(DB_URL)
    storage.create_tables()
    # Initialize multi-model embed adapter
    embed_adapter = EmbedAdapter(
        doc_model=os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2"),
        code_model=os.getenv("CODE_EMBED_MODEL", None)
    )

# -----------------------
# endpoints
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/test_connectors")
def test_connectors(payload: ConnectorTest):
    typ = payload.type.lower()
    if typ == "confluence":
        base = payload.base_url or os.getenv("CONFLUENCE_BASE_URL")
        user = payload.username or os.getenv("CONFLUENCE_USERNAME")
        token = payload.token or os.getenv("CONFLUENCE_TOKEN")
        if not (base and user and token):
            return {"ok": False, "message": "Confluence credentials missing (base/username/token)"}
        ok, msg = conf_conn.test_connection(base, user, token)
        return {"ok": ok, "message": msg}
    elif typ == "github":
        token = payload.token or os.getenv("GITHUB_TOKEN")
        if not token:
            return {"ok": False, "message": "GitHub token missing"}
        ok, msg = gh_conn.test_connection(token)
        return {"ok": ok, "message": msg}
    else:
        raise HTTPException(status_code=400, detail="unsupported connector type")


@app.post("/confluence/page_ids")
def confluence_page_ids(req: PageIdsRequest):
    """
    Return list of pages (id,title,url) for a space or a page subtree.
    The API uses credentials from the request OR falls back to .env.
    """
    base = req.base_url or os.getenv("CONFLUENCE_BASE_URL")
    user = req.username or os.getenv("CONFLUENCE_USERNAME")
    token = req.token or os.getenv("CONFLUENCE_TOKEN")
    if not (base and user and token):
        raise HTTPException(status_code=400, detail="Confluence credentials missing (base/username/token)")
    if not (req.space_key or req.page_id):
        raise HTTPException(status_code=400, detail="Provide space_key or page_id")

    try:
        default_limit = req.limit or 100
        pages = conf_conn.fetch_pages(base, user, token, space_key=req.space_key, page_id=req.page_id, limit=default_limit, max_docs=None)
        simplified = [{"id": p["id"], "title": p.get("title"), "url": p.get("url")} for p in pages]
        return {"pages": simplified}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {e}")


@app.post("/ingest/confluence")
def ingest_confluence(req: IngestByPageIdsRequest):
    """
    Idempotent ingest for Confluence pages.
    Accepts: page_ids list OR space_key/page_id.
    If page content unchanged (by content_hash), skip; otherwise delete previous chunks and insert new ones.
    """
    base = req.base_url or os.getenv("CONFLUENCE_BASE_URL")
    user = req.username or os.getenv("CONFLUENCE_USERNAME")
    token = req.token or os.getenv("CONFLUENCE_TOKEN")

    if not (base and user and token):
        raise HTTPException(status_code=400, detail="Confluence credentials missing (base/username/token)")

    pages: List[dict] = []
    try:
        if req.page_ids:
            for pid in req.page_ids:
                p = conf_conn.fetch_pages(base, user, token, page_id=pid)
                if p:
                    pages.extend(p)
        else:
            if not (req.space_key or req.page_id):
                raise HTTPException(status_code=400, detail="Provide page_ids or space_key/page_id")
            default_limit = 100
            pages = conf_conn.fetch_pages(base, user, token, space_key=req.space_key, page_id=req.page_id, limit=default_limit, max_docs=req.max_docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching pages: {e}")

    doc_count = 0
    chunk_count = 0

    for p in pages:
        page_id = p.get("id")
        title = p.get("title", "untitled")
        url = p.get("url")
        meta = p.get("meta", {}) or {}
        if req.space_key:
            meta.setdefault("space", req.space_key)

        # canonicalize page text using the ingester's stripper
        canonical_text = confluence_ingest._strip_html(p.get("content", "")) if hasattr(confluence_ingest, "_strip_html") else p.get("content", "")
        content_hash = hashlib.sha256((canonical_text or "").encode("utf-8")).hexdigest()

        existing = storage.get_document_by_source_external("confluence", page_id)

        if existing and existing.get("content_hash") == content_hash:
            # no change -> skip
            continue

        # If existing and changed, delete old chunks first
        if existing:
            storage.delete_chunks_for_document(existing["id"])

        # Compute last_modified scalar safely
        last_modified_val = _extract_last_modified_from_meta(p.get("meta", {}) or {})

        # Insert or update document idempotently
        doc_id = storage.insert_document(
            source="confluence",
            external_id=page_id,
            title=title,
            url=url,
            content_hash=content_hash,
            canonical_text=canonical_text,
            meta=meta,
            last_modified=last_modified_val
        )

        # Chunk page and embed
        chunks = confluence_ingest.chunk_page(p.get("content", ""))
        texts = [c["text"] for c in chunks]
        if texts:
            embeddings = embed_adapter.embed_many(texts, source="confluence")
            for c, emb in zip(chunks, embeddings):
                storage.insert_chunk(doc_id, c["text"], emb, {"page_id": page_id, "title": title, **meta})
                chunk_count += 1

        doc_count += 1

    return {"status": "ingested", "documents": doc_count, "chunks": chunk_count}


@app.post("/ingest/github")
def ingest_github(req: IngestGithubRequest):
    token = req.token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token missing")
    if not req.repo:
        raise HTTPException(status_code=400, detail="repo (owner/repo) required")

    try:
        files = gh_conn.fetch_repo_docs(req.repo, token, branch=req.branch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching repo docs: {e}")

    doc_count = 0
    chunk_count = 0
    for f in files:
        # use repo + path as external_id to uniquely identify a file
        path = f.get("path", "file")
        external_id = f"{req.repo}:{path}"
        title = path
        url = f.get("url")
        meta = {"repo": req.repo}

        canonical_text = github_ingest._strip_html(f.get("content", "")) if hasattr(github_ingest, "_strip_html") else f.get("content", "")
        content_hash = hashlib.sha256((canonical_text or "").encode("utf-8")).hexdigest()

        existing = storage.get_document_by_source_external("github", external_id)
        if existing and existing.get("content_hash") == content_hash:
            continue

        if existing:
            storage.delete_chunks_for_document(existing["id"])

        doc_id = storage.insert_document(
            source="github",
            external_id=external_id,
            title=title,
            url=url,
            content_hash=content_hash,
            canonical_text=canonical_text,
            meta=meta,
            last_modified=None
        )

        chunks = github_ingest.chunk_file(f.get("content", ""))
        texts = [c["text"] for c in chunks]
        if texts:
            embeddings = embed_adapter.embed_many(texts, source="github")
            for c, emb in zip(chunks, embeddings):
                storage.insert_chunk(doc_id, c["text"], emb, {"path": path, "repo": req.repo})
                chunk_count += 1

        doc_count += 1

@app.api_route("/query", methods=["GET", "POST"])
def query_endpoint(
    q: Optional[str] = Query(None, description="Query string (as query param)"),
    body: Optional[Dict[str, Any]] = Body(None, description="Optional JSON body with {'q': '...'}"),
    k_dense: int = 100,
    k_fts: int = 100,
    alpha: float = 0.7,
    top_k: int = 5,
):
    """
    Hybrid retrieval endpoint.
    - q: query string
    - k_dense: number of dense ANN candidates to retrieve
    - k_fts: number of FTS candidates to retrieve
    - alpha: weight for dense (beta = 1-alpha)
    - top_k: how many top candidates to return
    Returns: JSON with candidates and an MCP context (for testing)
    """
    # allow q from either query param or JSON body
    if not q:
        if body and isinstance(body, dict) and "q" in body:
            q = body.get("q")
    if not q:
        raise HTTPException(status_code=400, detail="Missing required parameter 'q' (either query param or JSON body).")

    if storage is None or embed_adapter is None:
        raise HTTPException(status_code=500, detail="service not initialized")

    # 1) embed the query (use doc model)
    qe = embed_adapter.embed_many([q], source="confluence", batch_size=int(os.getenv("EMBED_BATCH","64")))
    if not qe:
        raise HTTPException(status_code=500, detail="failed to embed query")
    qvec = qe[0]
    qvec_text = _vec_to_literal(qvec)

    # 2) Dense ANN: use pgvector operator "<->" (L2 distance) - lower is better
    dense_sql = f"""
        SELECT id, document_id, chunk_text, meta, (embedding_vector <-> %s::vector) AS dist
        FROM chunks
        WHERE embedding_vector IS NOT NULL
        ORDER BY dist
        LIMIT %s;
    """
    with storage.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(dense_sql, (qvec_text, k_dense))
        dense_rows = cur.fetchall()

    # convert dense distance -> similarity
    dense_candidates = {}
    max_dense_sim = 0.0
    for r in dense_rows:
        dist = float(r["dist"]) if r["dist"] is not None else 1e9
        sim = 1.0 / (1.0 + dist)  # simple transform, -> (0,1]
        dense_candidates[r["id"]] = {"id": r["id"], "document_id": r["document_id"],
                                     "chunk_text": r["chunk_text"], "meta": r["meta"],
                                     "dense_sim": sim, "fts_score": 0.0}

        if sim > max_dense_sim:
            max_dense_sim = sim

    # 3) FTS candidates: get ts_rank for the query
    fts_sql = """
        SELECT id, document_id, chunk_text, meta,
               ts_rank(chunk_tsv, plainto_tsquery('english', %s)) AS fts_rank
        FROM chunks
        WHERE chunk_tsv @@ plainto_tsquery('english', %s)
        ORDER BY fts_rank DESC
        LIMIT %s;
    """
    with storage.conn.cursor(row_factory=dict_row) as cur:
        cur.execute(fts_sql, (q, q, k_fts))
        fts_rows = cur.fetchall()

    max_fts = 0.0
    for r in fts_rows:
        fts_score = float(r["fts_rank"] or 0.0)
        if fts_score > max_fts:
            max_fts = fts_score
        cid = r["id"]
        if cid in dense_candidates:
            dense_candidates[cid]["fts_score"] = fts_score
        else:
            dense_candidates[cid] = {"id": cid, "document_id": r["document_id"],
                                     "chunk_text": r["chunk_text"], "meta": r["meta"],
                                     "dense_sim": 0.0, "fts_score": fts_score}

    # 4) Normalize scores and compute fusion
    # Normalize dense_sim by max_dense_sim (if zero, leave as is), fts by max_fts
    fused_list = []
    for cid, info in dense_candidates.items():
        dense_sim = info.get("dense_sim", 0.0)
        fts_score = info.get("fts_score", 0.0)
        dense_norm = (dense_sim / max_dense_sim) if max_dense_sim > 0 else dense_sim
        fts_norm = (fts_score / max_fts) if max_fts > 0 else fts_score
        fused = alpha * dense_norm + (1.0 - alpha) * fts_norm
        info["dense_norm"] = dense_norm
        info["fts_norm"] = fts_norm
        info["fused_score"] = fused
        fused_list.append(info)

    # 5) Sort by fused_score desc and pick top_k
    fused_list.sort(key=lambda x: x["fused_score"], reverse=True)
    top_candidates = fused_list[:top_k]

    # 6) Assemble MCP context (for debugging / actual LLM call)
    chunks_for_mcp = []
    for c in top_candidates:
        chunks_for_mcp.append({
            "chunk_text": c["chunk_text"],
            "score": c["fused_score"],
            "title": (c.get("meta") or {}).get("title"),
            "url": (c.get("meta") or {}).get("url")
        })
    mcp = assemble_mcp_context(q, chunks_for_mcp, max_chunks=min(len(chunks_for_mcp), top_k))
    # log the context for audit
    log_mcp(mcp["metadata"])

    return {"query": q, "top_k": top_k, "candidates": top_candidates, "mcp_context": mcp["context_str"]}

# diagnostics endpoint
@app.get("/diagnostics")
def diagnostics():
    out = {}
    # DB reachable?
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT 1")
            out["db"] = {"ok": True}
    except Exception as e:
        out["db"] = {"ok": False, "error": str(e)}
        return JSONResponse(status_code=500, content=out)

    # extensions
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT extname, extversion FROM pg_extension")
            ext = cur.fetchall()
            out["extensions"] = [{"extname": r[0], "version": r[1]} for r in ext]
    except Exception as e:
        out["extensions_error"] = str(e)

    # tables and counts
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('documents','chunks','ingest_jobs')")
            t = [r[0] for r in cur.fetchall()]
            out["tables_present"] = t

            cur.execute("SELECT COUNT(*) FROM documents")
            out["documents_count"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM chunks")
            out["chunks_count"] = cur.fetchone()[0]
            cur.execute("SELECT ROUND(AVG(LENGTH(chunk_text))::numeric,2) FROM chunks")
            out["avg_chunk_chars"] = cur.fetchone()[0]
    except Exception as e:
        out["counts_error"] = str(e)

    # indexes
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename='chunks'")
            out["indexes"] = [r[0] for r in cur.fetchall()]
    except Exception as e:
        out["indexes_error"] = str(e)

    # sample doc + chunk
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT id, title, url FROM documents ORDER BY ingested_at DESC LIMIT 3")
            out["sample_documents"] = [{"id":r[0],"title":r[1],"url":r[2]} for r in cur.fetchall()]
            cur.execute("SELECT id, substring(chunk_text,1,200) FROM chunks ORDER BY id DESC LIMIT 3")
            out["sample_chunks"] = [{"id":r[0],"sample":r[1]} for r in cur.fetchall()]
    except Exception as e:
        out["sample_error"] = str(e)

    return out

# admin migration endpoints

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", None)
LOG_DIR = os.getenv("ADMIN_LOG_DIR", "/tmp")  # can be changed to repo/logs

def run_migration_job(job_row_id: int, job_uuid: str, log_path: str):
    """
    Background job to run the embedding migration script and update ingest_jobs.
    """
    # update job status to running
    try:
        with storage.conn.cursor() as cur:
            cur.execute("UPDATE ingest_jobs SET status=%s, started_at=now() WHERE id=%s", ("running", job_row_id))
            storage.conn.commit()
    except Exception as e:
        # If we cannot update DB, still proceed to run migration but log the DB error
        pass

    rc = 1
    try:
        env = os.environ.copy()
        # ensure we execute with the same python as the running process
        python_exec = sys.executable or "python"
        # open logfile and run migration
        with open(log_path, "w", encoding="utf-8") as fh:
            proc = subprocess.Popen([python_exec, "tools/migrate_embeddings.py"], stdout=fh, stderr=fh, env=env)
            rc = proc.wait()
    except Exception as e:
        # write exception into log
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\nException running migration: {e}\n")
        rc = 2

    # update job status on completion
    try:
        status = "succeeded" if rc == 0 else "failed"
        summary = {"job_uuid": job_uuid, "rc": rc, "log": log_path}
        with storage.conn.cursor() as cur:
            cur.execute(
                "UPDATE ingest_jobs SET status=%s, finished_at=now(), summary=%s WHERE id=%s",
                (status, json.dumps(summary), job_row_id)
            )
            storage.conn.commit()
    except Exception as e:
        # best-effort: log but do not raise
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\nException updating job record: {e}\n")

@app.post("/admin/migrate_embeddings")
def admin_migrate(background_tasks: BackgroundTasks, token: str = None):
    # simple admin auth
    if ADMIN_TOKEN is None:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured on server")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    # create a job record
    job_uuid = str(uuid.uuid4())
    log_fn = f"migrate_{job_uuid}.log"
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = str(Path(LOG_DIR) / log_fn)

    try:
        with storage.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ingest_jobs (source, external_key, status, summary) VALUES (%s,%s,%s,%s) RETURNING id",
                ("migration", "migrate_embeddings", "queued", json.dumps({"log": log_path}))
            )
            job_row_id = cur.fetchone()[0]
            storage.conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job record: {e}")

    # spawn background job
    background_tasks.add_task(run_migration_job, job_row_id, job_uuid, log_path)
    return {"started": True, "job_id": job_row_id, "log": log_path}

@app.get("/admin/migration_status/{job_id}")
def admin_migration_status(job_id: int, token: str = None):
    if ADMIN_TOKEN is None:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured on server")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT id, source, external_key, status, summary, started_at, finished_at FROM ingest_jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="job not found")
            job = {
                "id": row[0],
                "source": row[1],
                "external_key": row[2],
                "status": row[3],
                "summary": row[4],
                "started_at": row[5].isoformat() if row[5] else None,
                "finished_at": row[6].isoformat() if row[6] else None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # tail the log file if present in summary
    log_tail = None
    try:
        summary = job.get("summary") or {}
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except:
                summary = {}
        log_path = summary.get("log")
        if log_path and os.path.exists(log_path):
            with open(log_path, "rb") as fh:
                # read last ~20000 bytes safely
                fh.seek(0, os.SEEK_END)
                sz = fh.tell()
                tail_size = 20000
                if sz > tail_size:
                    fh.seek(sz - tail_size)
                else:
                    fh.seek(0)
                log_tail = fh.read().decode(errors="replace")
    except Exception:
        log_tail = "error reading log"
    job["log_tail"] = log_tail
    return job

if __name__ == "__main__":
    uvicorn.run("retrieval_api:app", host="0.0.0.0", port=int(os.getenv("API_PORT", "8000")), reload=True)
