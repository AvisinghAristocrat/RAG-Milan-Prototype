# retrieval_api.py
"""
Retrieval API - full file
Endpoints:
 - GET /health
 - POST /test_connectors
 - POST /confluence/page_ids
 - POST /ingest/confluence
 - POST /ingest/github
 - GET/POST /query
 - GET /diagnostics
 - Admin:
     /admin/migrate_embeddings
     /admin/ann_eval
     /admin/targeted_reembed
     /admin/... job status/log/document inspector
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Body, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from dotenv import load_dotenv
from connectors import confluence as conf_conn
from connectors import github as gh_conn
from ingesters import confluence_ingest, github_ingest
from storage.postgres import PostgresStorage
from embeddings.embed_adapter import EmbedAdapter
from mcp.mcp import assemble_mcp_context, log_mcp
from psycopg.rows import dict_row
from pathlib import Path
from math import sqrt
from jobs.ann_jobs import create_job, update_job, get_job, list_jobs, result_path, save_result, save_log

import os
import time
import datetime
import logging
import traceback
import uvicorn
import re
import hashlib
import psycopg
import json
import uuid
import subprocess
import sys

try:
    from rerank.rerank import rerank_candidates
except Exception:
    rerank_candidates = None

# sentence-transformers for optional explicit model embedding (stronger models)
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


# load .env so API process sees credentials if present
load_dotenv()

# enable basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Milan RAG - Retrieval API")

# config
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))  # default to 1024 per DB migration; change via .env if needed

# Retrieval tuning knobs (safe defaults for prototype)
MIN_CHUNK_CHARS = int(os.getenv("MIN_CHUNK_CHARS", "40"))  # ignore ultra-short chunks in dense
HNSW_EF_SEARCH = int(os.getenv("HNSW_EF_SEARCH", "200"))   # higher = better recall
IVFFLAT_PROBES = int(os.getenv("IVFFLAT_PROBES", "10"))    # higher = better recall

# FTS configs (we'll try primary first, then fallback)
FTS_CONFIG_PRIMARY = os.getenv("FTS_CONFIG_PRIMARY", "english")
FTS_CONFIG_FALLBACK = os.getenv("FTS_CONFIG_FALLBACK", "simple")

# globals populated at startup
storage: Optional[PostgresStorage] = None
embed_adapter: Optional[EmbedAdapter] = None

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", None)
LOG_DIR = os.getenv("ADMIN_LOG_DIR", "/tmp")

CODE_INTENT_RE = re.compile(
    r"(\.cs|\.py|\.ts|\.js|\.java|\.go|\.cpp|\.h|\.yaml|\.yml|\.json|"
    r"Exception|StackTrace|NullReference|Traceback|"
    r"\bclass\b|\bpublic\b|\bprivate\b|\bdef\b|\bfunc\b|\breturn\b|"
    r"[A-Za-z]+[A-Z][A-Za-z0-9]+)",   # CamelCase identifiers like JoinResponse
    re.IGNORECASE
)

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

class DocSimilarityRequest(BaseModel):
    token: Optional[str] = None            # ADMIN token required
    document_id: Optional[int] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    q: str
    model: Optional[str] = None            # optional model for embedding (sentence-transformers)
    include_fts: bool = True
    top_k: int = 50                        # how many top chunks to return (by dense sim)
    batch_size: int = 64

class TargetedReembedRequest(BaseModel):
    token: str = None                # ADMIN_TOKEN required
    document_id: Optional[int] = None
    source: Optional[str] = None     # e.g., "confluence" or "github"
    external_id: Optional[str] = None
    create_title_chunk: bool = True
    title_chunk_len: int = 400
    erase_existing_title_chunk: bool = False
    reembed_full: bool = False
    model: Optional[str] = None
    batch_size: int = 64

class AnnEvalParams(BaseModel):
    model: str = "all-MiniLM-L6-v2"
    queries: str = "tools/ground_truth.json"
    top_k: int = 10
    ef_search: int = 64
    num_queries: int = 0

class QueryRequest(BaseModel):
    q: str

def infer_query_source(q: str) -> str:
    q = (q or "").strip()
    if not q:
        return "confluence"
    # CamelCase / identifiers => code intent
    if CODE_INTENT_RE.search(q):
        return "github"
    ql = q.lower()
    codey = any(t in ql for t in [
        "class ", "def ", ".cs", ".py", ".ts", ".js", ".java", ".go",
        ".yaml", ".yml", "stacktrace", "exception", "nullreference", "namespace"
    ])
    return "github" if codey else "confluence"

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

def _safe_fts_cfg(cfg: str) -> str:
    cfg = (cfg or "").strip().lower()
    return cfg if cfg in ("english", "simple") else "english"

def _db_connect():
    """
    IMPORTANT: Do NOT reuse a single global psycopg connection for concurrent FastAPI requests.
    A single aborted transaction can poison the connection and cascade 500s.
    For query-like endpoints we open a short-lived connection per request.

    This helper returns a connection with:
      - row_factory=dict_row (dict-like rows)
      - autocommit=True (avoids lingering aborted transaction states)
    """
    conn = psycopg.connect(DB_URL, row_factory=dict_row)
    conn.autocommit = True
    return conn

def _safe_rollback(conn):
    try:
        conn.rollback()
    except Exception:
        pass

def _looks_like_exact_query(q: str) -> bool:
    """Heuristic to detect short, label-ish queries where lexical matches should dominate.

    Examples: "Recovery/Join Response", "MFF-792", "Milan.SlotEngine.Shared.DTO".
    """
    if not q:
        return False

    q = q.strip()
    if not q:
        return False

    # "Label-ish" signals: slashes, dots, underscores, ticket-like dashes, etc.
    if any(ch in q for ch in ["/", "\\", ".", "_", ":", "-"]):
        # ignore very long paths/phrases
        if len(q) <= 80:
            return True

    # Short queries (<= 5 terms) with mostly TitleCase/Uppercase tokens also look label-ish.
    toks = [t for t in re.split(r"\s+", q) if t]
    if 1 <= len(toks) <= 5:
        alpha = sum(1 for t in toks if re.match(r"^[A-Z][A-Za-z0-9]+$", t))
        upper = sum(1 for t in toks if re.match(r"^[A-Z0-9_-]+$", t))
        if (alpha + upper) / max(1, len(toks)) >= 0.6:
            return True

    return False

def _chunk_sig(doc_id, chunk_id, text):
    norm = " ".join((text or "").split())  # whitespace normalize
    base = f"{doc_id if doc_id is not None else 'none'}|{chunk_id}|{norm}" if doc_id is None else f"{doc_id}|{norm}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def _simple_title_chunk_text(title: str, canonical_text: Optional[str], char_limit: int = 400) -> str:
    parts = []
    if title:
        parts.append(title.strip())
    if canonical_text:
        para = None
        for sep in ["\r\n\r\n", "\n\n"]:
            if sep in canonical_text:
                para = canonical_text.split(sep)[0].strip()
                break
        if not para:
            para = canonical_text.strip()
        excerpt = para[:char_limit].strip()
        if excerpt:
            parts.append(excerpt)
    return "\n\n".join(parts) if parts else (title or "")

def _find_existing_title_chunk(doc_id: int) -> Optional[int]:
    if storage is None:
        return None
    q = "SELECT id FROM chunks WHERE document_id = %s AND (meta->>'title_chunk') = 'true' LIMIT 1"
    with storage.conn.cursor() as cur:
        cur.execute(q, (doc_id,))
        row = cur.fetchone()
        if row:
            return row[0]
    return None

def _delete_title_chunk(doc_id: int):
    if storage is None:
        return
    q = "DELETE FROM chunks WHERE document_id = %s AND (meta->>'title_chunk') = 'true'"
    with storage.conn.cursor() as cur:
        cur.execute(q, (doc_id,))
        storage.conn.commit()

def _embed_with_sentencetransformer(model_name: str, texts: List[str], batch_size: int = 64):
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed in this environment")
    st_model = SentenceTransformer(model_name)
    embs = st_model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    out = []
    for e in embs:
        try:
            out.append(e.tolist())
        except Exception:
            out.append([float(x) for x in e])
    return out

def _safe_embed_title_text(model_name: Optional[str], source: str, title_text: str) -> Tuple[bool, Optional[List[float]], str]:
    try:
        if model_name:
            if SentenceTransformer is None:
                return False, None, "sentence-transformers not available in this environment"
            emb = _embed_with_sentencetransformer(model_name, [title_text], batch_size=1)[0]
        else:
            if embed_adapter is None:
                return False, None, "embed_adapter not initialized"
            emb = embed_adapter.embed_many([title_text], source=source, batch_size=1)[0]

        if not isinstance(emb, (list, tuple)):
            try:
                emb = emb.tolist()
            except Exception:
                return False, None, "Embedding returned by model is not list-like and cannot be converted."

        if len(emb) != EMBED_DIM:
            return False, None, f"embedding_dim_mismatch: expected={EMBED_DIM}, got={len(emb)}"
        return True, list(emb), ""
    except Exception as e:
        return False, None, f"embedding error: {e}"

def _validate_model_name(model_name: Optional[str], source: Optional[str] = None) -> Tuple[bool, str]:
    if not model_name:
        return True, ""
    try:
        if embed_adapter and hasattr(embed_adapter, "ensure_model"):
            try:
                embed_adapter.ensure_model(model_name)
                return True, ""
            except Exception as e:
                logger.debug("embed_adapter.ensure_model failed: %s", e)

        try:
            _ = embed_adapter.embed_many(["__validate__"], source=source or "confluence", model=model_name, batch_size=1)
            return True, ""
        except TypeError:
            pass
        except Exception as e:
            return False, f"embed_adapter.embed_many(model={model_name}) failed: {e}"

        if SentenceTransformer is not None:
            try:
                SentenceTransformer(model_name)
                return True, ""
            except Exception as e:
                return False, f"SentenceTransformer loading failed for model '{model_name}': {e}"
        return False, "SentenceTransformer not available to validate model"
    except Exception as e:
        return False, f"Unexpected validation error for model '{model_name}': {e}"

def _run_reembed_full_job(job_row_id: int, doc_id: int, source: str, canonical_text: str, model_name: Optional[str], batch_size: int, log_path: str):
    if storage is None or embed_adapter is None:
        return
    try:
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"Starting reembed job for doc={doc_id}, source={source}, model={model_name}\n")

            if source == "confluence":
                chunker = confluence_ingest.chunk_page
            elif source == "github":
                chunker = github_ingest.chunk_file
            else:
                def chunker(text):
                    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
                    out = []
                    for p in paras:
                        if len(p) <= 1200:
                            out.append({"text": p})
                        else:
                            step = 1000 - 150
                            i = 0
                            while i < len(p):
                                out.append({"text": p[i:i+1000]})
                                i += step
                    return out

            lf.write("Chunking document...\n")
            chunks = chunker(canonical_text or "")
            lf.write(f"Generated {len(chunks)} chunks\n")

            lf.write("Deleting existing non-title chunks (keeping title chunk if present)...\n")
            del_q = "DELETE FROM chunks WHERE document_id = %s AND NOT (meta->>'title_chunk') = 'true'"
            with storage.conn.cursor() as cur:
                cur.execute(del_q, (doc_id,))
                storage.conn.commit()
            lf.write("Deleted old chunks.\n")

            texts = [c["text"] for c in chunks]
            lf.write(f"Embedding {len(texts)} chunks in batches (batch_size={batch_size})...\n")

            if model_name:
                embeddings = _embed_with_sentencetransformer(model_name, texts, batch_size=batch_size)
            else:
                embeddings = embed_adapter.embed_many(texts, source=source, batch_size=batch_size)

            lf.write(f"Generated embeddings: {len(embeddings)}\n")

            lf.write("Inserting chunks into DB...\n")
            inserted = 0
            for txt, emb in zip(texts, embeddings):
                if not isinstance(emb, (list, tuple)):
                    try:
                        emb = emb.tolist()
                    except Exception:
                        raise RuntimeError("Invalid embedding object; expected list/array of floats")
                if len(emb) != EMBED_DIM:
                    lf.write(f"ERROR: embedding dim mismatch for doc={doc_id}, expected={EMBED_DIM}, got={len(emb)}\n")
                    with storage.conn.cursor() as cur:
                        summary = {"error": f"embedding_dim_mismatch for doc {doc_id}, got {len(emb)}"}
                        cur.execute("UPDATE ingest_jobs SET status=%s, finished_at=now(), summary=%s WHERE id=%s",
                                    ("failed", json.dumps(summary), job_row_id))
                        storage.conn.commit()
                    return
                storage.insert_chunk(doc_id, txt, emb, {"source": source})
                inserted += 1

            lf.write(f"Inserted {inserted} chunks for doc {doc_id}\n")

            with storage.conn.cursor() as cur:
                summary = {"doc_id": doc_id, "inserted": inserted}
                cur.execute("UPDATE ingest_jobs SET status=%s, finished_at=now(), summary=%s WHERE id=%s",
                            ("succeeded", json.dumps(summary), job_row_id))
                storage.conn.commit()
            lf.write("Job completed successfully.\n")
    except Exception as e:
        tb = traceback.format_exc()
        try:
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write("Exception during reembed:\n")
                lf.write(tb)
        except Exception:
            pass
        try:
            with storage.conn.cursor() as cur:
                summary = {"error": str(e)}
                cur.execute("UPDATE ingest_jobs SET status=%s, finished_at=now(), summary=%s WHERE id=%s",
                            ("failed", json.dumps(summary), job_row_id))
                storage.conn.commit()
        except Exception:
            pass

def _ph(sql: str) -> int:
    return sql.count("%s")

def _run_ann_eval_job(job_id: str, params: dict):
    update_job(job_id, status="running", started_at=datetime.datetime.utcnow().isoformat() + "Z")
    log_lines = []
    try:
        out_file = result_path(job_id)
        os.makedirs(os.path.dirname(out_file), exist_ok=True)

        cmd = [
            sys.executable or "python",
            "tools/eval_ann.py",
            "--queries",
            params.get("queries", "tools/ground_truth.json"),
            "--k",
            str(params.get("top_k", 10)),
            "--ef_search",
            str(params.get("ef_search", 64)),
            "--out",
            out_file,
        ]
        if params.get("model"):
            cmd += ["--model", params["model"]]
        if params.get("num_queries"):
            cmd += ["--num_queries", str(params["num_queries"])]

        log_lines.append(f"Running command: {' '.join(cmd)}\n")
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        log_lines.append("=== STDOUT ===\n" + (proc.stdout or "") + "\n")
        log_lines.append("=== STDERR ===\n" + (proc.stderr or "") + "\n")

        if proc.returncode != 0:
            update_job(job_id, status="failed", finished_at=datetime.datetime.utcnow().isoformat() + "Z")
            save_log(job_id, "".join(log_lines))
            return

        try:
            with open(out_file, "r", encoding="utf-8") as fh:
                result = json.load(fh)
            save_result(job_id, result)
        except Exception as e:
            log_lines.append(f"Failed to read output file {out_file}: {e}\n")
            save_log(job_id, "".join(log_lines))
            update_job(job_id, status="failed", finished_at=datetime.datetime.utcnow().isoformat() + "Z")
            return

        save_log(job_id, "".join(log_lines))

    except Exception as e:
        save_log(job_id, f"Unexpected error: {str(e)}\n")
        update_job(job_id, status="failed", finished_at=datetime.datetime.utcnow().isoformat() + "Z")

@app.on_event("startup")
def startup():
    global storage, embed_adapter
    wait_for_db(DB_URL, timeout=60)
    storage = PostgresStorage(DB_URL)
    storage.create_tables()
    embed_adapter = EmbedAdapter(
        doc_model=os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2"),
        code_model=os.getenv("CODE_EMBED_MODEL", None),
    )
    logger.info("Embed adapter initialized. Expected embed dim = %s", EMBED_DIM)

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
    if typ == "github":
        token = payload.token or os.getenv("GITHUB_TOKEN")
        if not token:
            return {"ok": False, "message": "GitHub token missing"}
        ok, msg = gh_conn.test_connection(token)
        return {"ok": ok, "message": msg}
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
        pages = conf_conn.fetch_pages(
            base, user, token, space_key=req.space_key, page_id=req.page_id, limit=default_limit, max_docs=None
        )
        simplified = [{"id": p["id"], "title": p.get("title"), "url": p.get("url")} for p in pages]
        return {"pages": simplified}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {e}")

@app.post("/ingest/confluence")
def ingest_confluence(req: IngestByPageIdsRequest):
    """
    Idempotent ingest for Confluence pages.
    Accepts: page_ids list OR space_key/page_id.
    If page content unchanged (by content_hash) -> skip (unless erase_existing=True).
    Returns detailed per-document results and aggregate summary.
    """
    if storage is None or embed_adapter is None:
        raise HTTPException(status_code=500, detail="service not initialized")

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
            pages = conf_conn.fetch_pages(
                base, user, token, space_key=req.space_key, page_id=req.page_id, limit=default_limit, max_docs=req.max_docs
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching pages: {e}")

    total_chunks = 0
    per_doc: List[Dict[str, Any]] = []
    skipped_reasons: Dict[str, int] = {}
    inserted_docs = 0
    skipped_docs = 0
    failed_docs = 0

    for p in pages:
        page_id = p.get("id")
        title = p.get("title", "untitled")
        url = p.get("url")
        meta = p.get("meta", {}) or {}
        if req.space_key:
            meta.setdefault("space", req.space_key)

        canonical_text = (
            confluence_ingest._strip_html(p.get("content", ""))
            if hasattr(confluence_ingest, "_strip_html")
            else p.get("content", "")
        )
        content_hash = hashlib.sha256((canonical_text or "").encode("utf-8")).hexdigest()

        existing = storage.get_document_by_source_external("confluence", page_id)

        try:
            if existing and req.erase_existing:
                storage.delete_chunks_for_document(existing["id"])
                existing = None
            else:
                if existing and existing.get("content_hash") == content_hash:
                    skipped_docs += 1
                    per_doc.append(
                        {
                            "external_id": page_id,
                            "document_id": existing.get("id"),
                            "title": title,
                            "url": url,
                            "status": "skipped",
                            "reason": "unchanged",
                            "chunks": 0,
                        }
                    )
                    skipped_reasons["unchanged"] = skipped_reasons.get("unchanged", 0) + 1
                    continue
                if existing:
                    storage.delete_chunks_for_document(existing["id"])

            last_modified_val = _extract_last_modified_from_meta(p.get("meta", {}) or {})

            doc_id = storage.insert_document(
                source="confluence",
                external_id=page_id,
                title=title,
                url=url,
                content_hash=content_hash,
                canonical_text=canonical_text,
                meta=meta,
                last_modified=last_modified_val,
            )

            chunks = confluence_ingest.chunk_page(p.get("content", ""))
            texts = [c["text"] for c in chunks] if chunks else []
            if not texts:
                per_doc.append(
                    {
                        "external_id": page_id,
                        "document_id": doc_id,
                        "title": title,
                        "url": url,
                        "status": "skipped",
                        "reason": "no_chunks",
                        "chunks": 0,
                    }
                )
                skipped_docs += 1
                skipped_reasons["no_chunks"] = skipped_reasons.get("no_chunks", 0) + 1
                continue

            embeddings = embed_adapter.embed_many(texts, source="confluence")
            inserted_chunks_for_doc = 0
            for c_text, emb in zip(texts, embeddings):
                storage.insert_chunk(doc_id, c_text, emb, {"source": "confluence", "page_id": page_id, "title": title, **meta})
                inserted_chunks_for_doc += 1
            total_chunks += inserted_chunks_for_doc
            inserted_docs += 1
            per_doc.append(
                {
                    "external_id": page_id,
                    "document_id": doc_id,
                    "title": title,
                    "url": url,
                    "status": "inserted",
                    "reason": None,
                    "chunks": inserted_chunks_for_doc,
                }
            )

        except Exception as e:
            failed_docs += 1
            per_doc.append(
                {
                    "external_id": page_id,
                    "document_id": existing.get("id") if existing else None,
                    "title": title,
                    "url": url,
                    "status": "failed",
                    "reason": str(e),
                    "chunks": 0,
                }
            )
            skipped_reasons["failed"] = skipped_reasons.get("failed", 0) + 1

    return {
        "status": "ingested",
        "documents_total": len(pages),
        "documents_inserted": inserted_docs,
        "documents_skipped": skipped_docs,
        "documents_failed": failed_docs,
        "chunks_inserted": total_chunks,
        "skipped_reasons": skipped_reasons,
        "details": per_doc,
    }

@app.post("/ingest/github")
def ingest_github(req: IngestGithubRequest):
    if storage is None or embed_adapter is None:
        raise HTTPException(status_code=500, detail="service not initialized")

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
            last_modified=None,
        )

        chunks = github_ingest.chunk_file(f.get("content", ""))
        texts = [c["text"] for c in chunks]
        if texts:
            embeddings = embed_adapter.embed_many(texts, source="github")
            for c, emb in zip(chunks, embeddings):
                storage.insert_chunk(doc_id, c["text"], emb, {"path": path, "repo": req.repo})
                chunk_count += 1
        doc_count += 1

    return {"status": "ingested", "documents": doc_count, "chunks": chunk_count}

@app.post("/query")
def query_endpoint(
    req: QueryRequest,
    k_dense: int = 200,
    k_fts: int = 100,
    alpha: float = 0.7,
    top_k: int = 10,
    rerank: bool = False,
    rerank_top_k: int = 100,
    rerank_weight: float = 1.0,
    source: Optional[str] = Query(default=None),
):
    q = (req.q or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Missing required field 'q'.")
    if storage is None or embed_adapter is None:
        raise HTTPException(status_code=500, detail="service not initialized")

    # --- sanitize inputs ---
    k_dense = max(1, int(k_dense))
    k_fts = max(1, int(k_fts))
    top_k = max(1, int(top_k))
    alpha = float(alpha)

    # If the user didn't override alpha, and the query looks like an exact label/token,
    # bias toward lexical matches so we don't bury "exact hit" chunks under dense-only results.
    alpha_eff = alpha
    if abs(alpha - 0.7) < 1e-9 and _looks_like_exact_query(q):
        alpha_eff = 0.35

    # --- embed query ---
    src = (source or "").strip().lower()
    effective_source = src if src in ("confluence", "github") else None   # None = search all sources
    embed_source = effective_source or "confluence"
    qvec = embed_adapter.embed_many([q], source=embed_source)[0]
    if len(qvec) != EMBED_DIM:
        raise HTTPException(
            status_code=500,
            detail=f"Query embedding dim mismatch: expected {EMBED_DIM}, got {len(qvec)}. "
                   f"Check DOC_EMBED_MODEL / EMBED_DIM env vars."
        )

    qvec_text = _vec_to_literal(qvec)

    # FTS normalization: treat "/" as a delimiter
    q_fts = (q or "").replace("/", " ").strip()

    fts_cfg_primary = _safe_fts_cfg(FTS_CONFIG_PRIMARY)
    if effective_source == "github":
        fts_cfg_primary = "simple"
    fts_cfg_fallback = _safe_fts_cfg(FTS_CONFIG_FALLBACK)

    conn = None
    try:
        conn = _db_connect()
        with conn.cursor() as cur:

            # Improve ANN recall (optional). If SET fails, rollback so we don't poison the connection.
            for stmt, val in (
                ("SET hnsw.ef_search = %s", HNSW_EF_SEARCH),
                ("SET ivfflat.probes = %s", IVFFLAT_PROBES),
            ):
                try:
                    cur.execute(stmt, (int(val),))
                except Exception:
                    _safe_rollback(conn)

            # --- Lexical probe for exact/label-ish queries ---
            lex_probe_rows = []
            if _looks_like_exact_query(q):
                q_raw = q.strip()
                if q_raw:
                    pat = f"%{q_raw}%"
                    try:
                        cur.execute(
                            """
                            SELECT c.id, c.document_id, c.chunk_text, c.meta, 1.0 AS fts_rank
                            FROM chunks c
                            JOIN documents d ON d.id = c.document_id
                            WHERE (%s::text IS NULL OR d.source = %s::text)
                              AND (
                                c.chunk_text ILIKE %s
                                OR COALESCE(c.meta->>'title','') ILIKE %s
                                OR COALESCE(d.title,'') ILIKE %s
                              )
                            ORDER BY c.id DESC
                            LIMIT %s;
                            """,
                            (effective_source, effective_source, pat, pat, pat, k_fts),
                        )
                        lex_probe_rows = cur.fetchall()
                    except Exception as e:
                        logger.debug("Lex probe failed: %s", e)
                        _safe_rollback(conn)
                        lex_probe_rows = []

            # --- Dense ANN (FILTER BY documents.source, NOT meta->>'source') ---
            dense_sql = """
                SELECT c.id, c.document_id, c.chunk_text, c.meta,
                       (c.embedding_vector <-> %s::vector) AS dist
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.embedding_vector IS NOT NULL
                  AND (%s::text IS NULL OR d.source = %s::text)
                  AND (LENGTH(c.chunk_text) >= %s OR (c.meta->>'title_chunk') = 'true')
                ORDER BY dist
                LIMIT %s;
            """
            dense_params = (qvec_text, effective_source, effective_source, MIN_CHUNK_CHARS, k_dense)
            cur.execute(dense_sql, dense_params)
            dense_rows = cur.fetchall()
            logger.info("dense placeholders=%d params=%d", dense_sql.count("%s"), len(dense_params))

            # --- FTS primary/fallback (FILTER BY documents.source) ---
            def _run_fts(cfg: str):
                def _fetch(tsquery_fn: str, use_stored_tsv: bool):
                    if use_stored_tsv:
                        vec_expr = f"COALESCE(c.chunk_tsv, to_tsvector('{cfg}', c.chunk_text))"
                    else:
                        vec_expr = f"to_tsvector('{cfg}', c.chunk_text)"
                    fts_sql = f"""
                        WITH q AS (
                          SELECT {tsquery_fn}('{cfg}', %s) AS tsq
                        )
                        SELECT c.id, c.document_id, c.chunk_text, c.meta,
                            COALESCE(ts_rank_cd({vec_expr}, (SELECT tsq FROM q)), 0.0) AS fts_rank
                        FROM chunks c
                        JOIN documents d ON d.id = c.document_id
                        WHERE (%s::text IS NULL OR d.source = %s::text)
                            AND {vec_expr} @@ (SELECT tsq FROM q)
                        ORDER BY fts_rank DESC
                        LIMIT %s;
                    """
                    cur.execute(fts_sql, (q_fts, effective_source,effective_source, k_fts))
                    return cur.fetchall()

                for tsq_fn in ("websearch_to_tsquery", "plainto_tsquery"):
                    try:
                        rows = _fetch(tsq_fn, use_stored_tsv=True)
                    except Exception:
                        _safe_rollback(conn)
                        rows = []
                    if rows:
                        return rows

                    try:
                        rows = _fetch(tsq_fn, use_stored_tsv=False)
                    except Exception:
                        _safe_rollback(conn)
                        rows = []
                    if rows:
                        return rows

                return []

            fts_rows = _run_fts(fts_cfg_primary)
            if not fts_rows and fts_cfg_fallback != fts_cfg_primary:
                fts_rows = _run_fts(fts_cfg_fallback)

            # --- ILIKE lexical fallback if FTS produced nothing (FILTER BY documents.source) ---
            if not fts_rows:
                q_raw = q.strip()
                if q_raw:
                    pat = f"%{q_raw}%"
                    try:
                        cur.execute(
                            """
                            SELECT c.id, c.document_id, c.chunk_text, c.meta, 1.0 AS fts_rank
                            FROM chunks c
                            JOIN documents d ON d.id = c.document_id
                            WHERE (%s::text IS NULL OR d.source = %s::text)
                              AND (
                                c.chunk_text ILIKE %s
                                OR COALESCE(c.meta->>'title','') ILIKE %s
                                OR COALESCE(d.title,'') ILIKE %s
                              )
                            ORDER BY c.id DESC
                            LIMIT %s;
                            """,
                            (effective_source,effective_source, pat, pat, pat, k_fts),
                        )
                        fts_rows = cur.fetchall()
                    except Exception as e:
                        logger.debug("ILIKE fallback failed: %s", e)
                        _safe_rollback(conn)
                        fts_rows = []

            # --- Merge candidates (dense + fts + lex_probe) ---
            dense_candidates: Dict[int, Dict[str, Any]] = {}

            # keep lexical sources distinct, then dedupe properly (do NOT double-add lex_probe)
            logger.info("LEX DEBUG: dense=%s fts=%s lex_probe=%s",
                        len(dense_rows), len(fts_rows or []), len(lex_probe_rows or []))

            max_dense_sim = 0.0
            for r in dense_rows:
                dist = float(r["dist"]) if r.get("dist") is not None else 1e9
                sim = 1.0 / (1.0 + dist)
                cid = int(r["id"])
                dense_candidates[cid] = {
                    "id": cid,
                    "document_id": r.get("document_id"),
                    "chunk_text": r.get("chunk_text"),
                    "meta": r.get("meta"),
                    "dense_sim": sim,
                    "fts_score": 0.0,
                }
                if sim > max_dense_sim:
                    max_dense_sim = sim

            # combine lexical sources: fts_rows plus lex_probe_rows (dedupe by chunk id)
            combined_lex = []
            seen_lex_ids = set()

            for rr in (fts_rows or []):
                cid = int(rr["id"])
                if cid in seen_lex_ids:
                    continue
                seen_lex_ids.add(cid)
                combined_lex.append(rr)

            for rr in (lex_probe_rows or []):
                cid = int(rr["id"])
                if cid in seen_lex_ids:
                    continue
                seen_lex_ids.add(cid)
                combined_lex.append(rr)

            max_fts = 0.0
            for r in combined_lex:
                fts_score = float(r.get("fts_rank") or 0.0)
                if fts_score > max_fts:
                    max_fts = fts_score
                cid = int(r["id"])
                if cid in dense_candidates:
                    dense_candidates[cid]["fts_score"] = max(dense_candidates[cid]["fts_score"], fts_score)
                else:
                    dense_candidates[cid] = {
                        "id": cid,
                        "document_id": r.get("document_id"),
                        "chunk_text": r.get("chunk_text"),
                        "meta": r.get("meta"),
                        "dense_sim": 0.0,
                        "fts_score": fts_score,
                    }

            fused_list: List[Dict[str, Any]] = []
            for info in dense_candidates.values():
                dense_sim = float(info.get("dense_sim", 0.0) or 0.0)
                fts_score = float(info.get("fts_score", 0.0) or 0.0)

                dense_norm = (dense_sim / max_dense_sim) if max_dense_sim > 0 else dense_sim
                fts_norm = (fts_score / max_fts) if max_fts > 0 else fts_score

                fused = alpha_eff * dense_norm + (1.0 - alpha_eff) * fts_norm
                info["dense_norm"] = dense_norm
                info["fts_norm"] = fts_norm
                info["fused_score"] = float(fused)
                fused_list.append(info)

            fused_list.sort(key=lambda x: float(x.get("fused_score", 0.0)), reverse=True)

            dedup = {}
            for c in fused_list:
                sig = _chunk_sig(c.get("document_id"), c.get("id"), c.get("chunk_text"))
                prev = dedup.get(sig)
                if prev is None or float(c.get("fused_score", 0.0)) > float(prev.get("fused_score", 0.0)):
                    dedup[sig] = c

            fused_list = list(dedup.values())
            fused_list.sort(key=lambda x: float(x.get("fused_score", 0.0)), reverse=True)

            # --- return top_k chunk-level candidates ---
            top_candidates = fused_list[:top_k]

            # --- Enrich candidate meta with documents.title/url/source fallbacks (fix "unknown |") ---
            doc_ids_needed = list({int(c["document_id"]) for c in top_candidates if c.get("document_id") is not None})
            doc_map: Dict[int, Dict[str, Any]] = {}
            if doc_ids_needed:
                try:
                    cur.execute(
                        "SELECT id, title, url, source FROM documents WHERE id = ANY(%s)",
                        (doc_ids_needed,),
                    )
                    for r in cur.fetchall():
                        doc_map[int(r["id"])] = {
                            "title": r.get("title"),
                            "url": r.get("url"),
                            "source": r.get("source"),
                        }
                except Exception:
                    _safe_rollback(conn)
                    doc_map = {}

            enriched_candidates = []
            for c in top_candidates:
                doc_id = c.get("document_id")
                chunk_meta = c.get("meta") or {}
                doc_meta = doc_map.get(int(doc_id), {}) if doc_id is not None else {}

                merged_meta = dict(chunk_meta)
                merged_meta.setdefault("title", doc_meta.get("title"))
                merged_meta.setdefault("url", doc_meta.get("url"))
                merged_meta.setdefault("source", doc_meta.get("source"))

                cc = dict(c)
                cc["meta"] = merged_meta
                enriched_candidates.append(cc)

            # Build MCP context from enriched candidates
            chunks_for_mcp = []
            for c in enriched_candidates:
                meta = c.get("meta") or {}
                chunks_for_mcp.append(
                    {
                        "chunk_text": c.get("chunk_text") or "",
                        "score": float(c.get("fused_score") or 0.0),
                        "title": meta.get("title"),
                        "url": meta.get("url"),
                    }
                )

            mcp = assemble_mcp_context(q, chunks_for_mcp, max_chunks=min(len(chunks_for_mcp), 6))
            log_mcp(mcp["metadata"])

            return {
                "query": q,
                "top_k": top_k,
                "candidates": enriched_candidates,
                "mcp_context": mcp["context_str"],
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Query failed")
        if conn is not None:
            _safe_rollback(conn)

        if os.getenv("DEBUG_JSON_ERRORS", "") == "1":
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": f"{type(e).__name__}: {str(e)}",
                    "traceback": traceback.format_exc(),
                },
            )
        raise HTTPException(status_code=500, detail=f"Query DB operation failed: {e}")
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

@app.get("/diagnostics")
def diagnostics(doc_id: Optional[int] = None):
    """
    Lightweight health/DB sanity checks.

    Uses a fresh DB connection per request and autocommit=True.
    Any caught SQL exception triggers conn.rollback() so later statements still work.

    Optional:
      - doc_id: include deeper stats for a specific document (e.g., 816)
    """
    out: Dict[str, Any] = {}

    try:
        with _db_connect() as conn:
            with conn.cursor() as cur:

                # 1) DB reachable?
                try:
                    cur.execute("SELECT 1 AS ok")
                    out["db"] = {"ok": True}
                except Exception as e:
                    out["db"] = {"ok": False, "error": str(e)}
                    _safe_rollback(conn)
                    return JSONResponse(status_code=500, content=out)

                # 2) extensions
                try:
                    cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname")
                    out["extensions"] = [{"extname": r["extname"], "version": r["extversion"]} for r in cur.fetchall()]
                except Exception as e:
                    out["extensions_error"] = str(e)
                    _safe_rollback(conn)

                # 3) tables present
                try:
                    cur.execute(
                        "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                        "AND tablename IN ('documents','chunks','ingest_jobs')"
                    )
                    out["tables_present"] = [r["tablename"] for r in cur.fetchall()]
                except Exception as e:
                    out["tables_error"] = str(e)
                    _safe_rollback(conn)

                # 4) counts + quality
                try:
                    cur.execute("SELECT COUNT(*) AS n FROM documents")
                    out["documents_count"] = int(cur.fetchone()["n"])

                    cur.execute("SELECT COUNT(*) AS n FROM chunks")
                    out["chunks_count"] = int(cur.fetchone()["n"])

                    cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE embedding_vector IS NULL")
                    out["missing_vectors"] = int(cur.fetchone()["n"])

                    try:
                        cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE chunk_tsv IS NULL")
                        out["missing_chunk_tsv"] = int(cur.fetchone()["n"])
                    except Exception as e:
                        out["missing_chunk_tsv_error"] = str(e)
                        _safe_rollback(conn)

                    cur.execute("SELECT ROUND(AVG(LENGTH(chunk_text))::numeric, 2) AS avg_len FROM chunks")
                    out["avg_chunk_chars"] = float(cur.fetchone()["avg_len"] or 0.0)

                    cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE LENGTH(chunk_text) < %s", (MIN_CHUNK_CHARS,))
                    out["chunks_below_min_chars"] = int(cur.fetchone()["n"])
                except Exception as e:
                    out["counts_error"] = str(e)
                    _safe_rollback(conn)

                # 5) embedding dim diagnostics
                out["embedding_dims"] = []
                out["embedding_dim_error"] = None
                try:
                    try:
                        cur.execute(
                            "SELECT vector_dims(embedding_vector) AS dim, COUNT(*) AS n "
                            "FROM chunks WHERE embedding_vector IS NOT NULL "
                            "GROUP BY dim ORDER BY dim"
                        )
                        rows = cur.fetchall()
                        out["embedding_dims"] = [{"dim": int(r["dim"]), "count": int(r["n"])} for r in rows]
                    except Exception:
                        _safe_rollback(conn)
                        cur.execute(
                            "SELECT array_length(embedding_vector::float8[], 1) AS dim, COUNT(*) AS n "
                            "FROM chunks WHERE embedding_vector IS NOT NULL "
                            "GROUP BY dim ORDER BY dim"
                        )
                        rows = cur.fetchall()
                        out["embedding_dims"] = [{"dim": int(r["dim"]), "count": int(r["n"])} for r in rows]
                except Exception as e:
                    out["embedding_dim_error"] = str(e)
                    _safe_rollback(conn)

                # 6) indexes (esp hnsw + chunk_tsv)
                try:
                    cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='chunks'")
                    idx_rows = cur.fetchall()
                    out["indexes"] = [r["indexname"] for r in idx_rows]
                    out["chunk_tsv_index_exists"] = any("chunk_tsv" in (r["indexdef"] or "") for r in idx_rows)
                    out["hnsw_indexes"] = [
                        {"indexname": r["indexname"], "indexdef": r["indexdef"]}
                        for r in idx_rows
                        if "using hnsw" in (r["indexdef"] or "").lower()
                    ]
                except Exception as e:
                    out["indexes_error"] = str(e)
                    _safe_rollback(conn)

                # 7) sample docs/chunks
                try:
                    cur.execute(
                        "SELECT id, title, url, source, external_id FROM documents "
                        "ORDER BY ingested_at DESC NULLS LAST LIMIT 3"
                    )
                    out["sample_documents"] = [
                        {"id": int(r["id"]), "title": r["title"], "url": r["url"], "source": r["source"], "external_id": r["external_id"]}
                        for r in cur.fetchall()
                    ]

                    cur.execute("SELECT id, document_id, substring(chunk_text,1,200) AS sample FROM chunks ORDER BY id DESC LIMIT 3")
                    out["sample_chunks"] = [
                        {"id": int(r["id"]), "document_id": int(r["document_id"]), "sample": r["sample"]}
                        for r in cur.fetchall()
                    ]
                except Exception as e:
                    out["sample_error"] = str(e)
                    _safe_rollback(conn)

                # 8) Optional: deep-inspect a specific document
                if doc_id is not None:
                    dd: Dict[str, Any] = {"document_id": int(doc_id)}
                    try:
                        cur.execute(
                            "SELECT id, source, external_id, title, url, ingested_at "
                            "FROM documents WHERE id = %s",
                            (int(doc_id),)
                        )
                        doc_row = cur.fetchone()
                        if not doc_row:
                            dd["exists"] = False
                        else:
                            dd["exists"] = True
                            dd["document"] = {
                                "id": int(doc_row["id"]),
                                "source": doc_row["source"],
                                "external_id": doc_row["external_id"],
                                "title": doc_row["title"],
                                "url": doc_row["url"],
                                "ingested_at": str(doc_row.get("ingested_at")) if doc_row.get("ingested_at") else None,
                            }

                            cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE document_id=%s", (int(doc_id),))
                            dd["chunks_total"] = int(cur.fetchone()["n"])

                            cur.execute(
                                "SELECT COUNT(*) AS n FROM chunks "
                                "WHERE document_id=%s AND embedding_vector IS NOT NULL",
                                (int(doc_id),)
                            )
                            dd["chunks_with_vectors"] = int(cur.fetchone()["n"])

                            cur.execute(
                                "SELECT COUNT(*) AS n FROM chunks "
                                "WHERE document_id=%s AND (meta->>'title_chunk')='true'",
                                (int(doc_id),)
                            )
                            dd["title_chunks"] = int(cur.fetchone()["n"])

                            cur.execute(
                                "SELECT id, LENGTH(chunk_text) AS n, substring(chunk_text,1,120) AS sample "
                                "FROM chunks WHERE document_id=%s "
                                "ORDER BY LENGTH(chunk_text) DESC NULLS LAST LIMIT 5",
                                (int(doc_id),)
                            )
                            dd["longest_chunks"] = [
                                {"chunk_id": int(r["id"]), "chars": int(r["n"]), "sample": r["sample"]}
                                for r in cur.fetchall()
                            ]

                    except Exception as e:
                        dd["error"] = str(e)
                        _safe_rollback(conn)

                    out["document_inspect"] = dd

        return out

    except Exception as e:
        return JSONResponse(status_code=500, content={"db": {"ok": False, "error": str(e)}})

@app.post("/admin/targeted_reembed")
def admin_targeted_reembed(req: TargetedReembedRequest, background_tasks: BackgroundTasks):
    if storage is None:
        raise HTTPException(status_code=500, detail="service not initialized")

    if ADMIN_TOKEN is None:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured on server")
    if req.token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    doc = None
    if req.document_id:
        with storage.conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, source, external_id, title, canonical_text FROM documents WHERE id = %s", (req.document_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="document not found")
            doc = row
    else:
        if not (req.source and req.external_id):
            raise HTTPException(status_code=400, detail="document_id or (source + external_id) required")
        doc = storage.get_document_by_source_external(req.source, req.external_id)
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")

    doc_id = doc["id"]
    source = doc.get("source") or req.source or "confluence"
    canonical_text = doc.get("canonical_text") or ""

    result = {"document_id": doc_id, "title_chunk_created": False, "title_chunk_id": None, "reembed_job": None}

    if req.model:
        ok, msg = _validate_model_name(req.model, source=source)
        if not ok:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Model validation failed", "detail": msg})

    if req.create_title_chunk:
        existing = _find_existing_title_chunk(doc_id)
        if existing and not req.erase_existing_title_chunk:
            result["title_chunk_id"] = existing
        else:
            if existing and req.erase_existing_title_chunk:
                _delete_title_chunk(doc_id)

            title_text = _simple_title_chunk_text(doc.get("title"), canonical_text, char_limit=req.title_chunk_len)
            if not title_text:
                raise HTTPException(status_code=400, detail="Cannot build title chunk (no title/canonical_text)")

            ok, emb, err = _safe_embed_title_text(req.model, source, title_text)
            if not ok:
                return JSONResponse(status_code=400, content={"ok": False, "error": "failed to embed title chunk", "detail": err})

            meta = {"title_chunk": True, "created_by": "targeted_reembed", "model": req.model or os.getenv("DOC_EMBED_MODEL")}
            new_chunk_id = storage.insert_chunk(doc_id, title_text, emb, meta)
            result["title_chunk_created"] = True
            result["title_chunk_id"] = new_chunk_id

    if req.reembed_full:
        try:
            with storage.conn.cursor() as cur:
                summary = {"doc_id": doc_id, "note": "targeted_reembed", "log": None}
                cur.execute(
                    "INSERT INTO ingest_jobs (source, external_key, status, summary) VALUES (%s,%s,%s,%s) RETURNING id",
                    ("admin", f"targeted_reembed:{doc_id}", "queued", json.dumps(summary)),
                )
                job_row_id = cur.fetchone()[0]
                storage.conn.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create ingest job record: {e}")

        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = str(Path(LOG_DIR) / f"reembed_{uuid.uuid4()}.log")

        try:
            with storage.conn.cursor() as cur:
                summary = {"doc_id": doc_id, "note": "targeted_reembed", "log": log_path}
                cur.execute("UPDATE ingest_jobs SET summary=%s WHERE id=%s", (json.dumps(summary), job_row_id))
                storage.conn.commit()
        except Exception:
            pass

        background_tasks.add_task(_run_reembed_full_job, job_row_id, doc_id, source, canonical_text, req.model, req.batch_size, log_path)
        result["reembed_job"] = {"job_row_id": job_row_id, "log": log_path}

    return result

@app.get("/admin/ingest_job/{job_id}")
def get_ingest_job(job_id: int, token: Optional[str] = None):
    if storage is None:
        raise HTTPException(status_code=500, detail="service not initialized")
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
            return {
                "id": row[0],
                "source": row[1],
                "external_key": row[2],
                "status": row[3],
                "summary": row[4],
                "started_at": row[5].isoformat() if row[5] else None,
                "finished_at": row[6].isoformat() if row[6] else None,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/ingest_job/{job_id}/log")
def get_ingest_job_log(job_id: int, token: Optional[str] = None):
    if storage is None:
        raise HTTPException(status_code=500, detail="service not initialized")
    if ADMIN_TOKEN is None:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN not configured on server")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        with storage.conn.cursor() as cur:
            cur.execute("SELECT summary FROM ingest_jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="job not found")
            summary = row[0] or {}
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary)
                except Exception:
                    summary = {"note": summary}
            log_path = summary.get("log")
            if not log_path or not os.path.exists(log_path):
                return {"log": "", "note": "no log file available yet", "log_path": log_path}
            with open(log_path, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                sz = fh.tell()
                tail_size = 20000
                fh.seek(max(0, sz - tail_size))
                data = fh.read().decode(errors="replace")
            return {"log": data, "log_path": log_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/document/{document_id}")
def get_document_detail(document_id: int, token: Optional[str] = None):
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        with _db_connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT id, title, url, meta, canonical_text, content_hash, last_modified, ingested_at "
                    "FROM documents WHERE id = %s",
                    (document_id,),
                )
                doc = cur.fetchone()
                if not doc:
                    raise HTTPException(status_code=404, detail="document not found")

                cur.execute(
                    "SELECT id, substring(chunk_text,1,1000) as sample, meta, (embedding_vector IS NOT NULL) as has_vector "
                    "FROM chunks WHERE document_id=%s ORDER BY id",
                    (document_id,),
                )
                chunks = cur.fetchall()

        payload = {"document": doc, "chunks": chunks}
        return JSONResponse(content=jsonable_encoder(payload))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in get_document_detail for id %s", document_id)
        if os.getenv("DEBUG_JSON_ERRORS", "") == "1":
            return JSONResponse(status_code=500, content={"ok": False, "error": str(e), "traceback": traceback.format_exc()})
        raise HTTPException(status_code=500, detail="internal server error")

@app.post("/admin/ann_eval")
def create_ann_eval(background_tasks: BackgroundTasks, params: AnnEvalParams):
    job_id = create_job(params.dict())
    background_tasks.add_task(_run_ann_eval_job, job_id, params.dict())
    return {"job_id": job_id, "status": "queued"}

@app.get("/admin/ann_eval")
def list_ann_jobs():
    return {"jobs": list_jobs()}

@app.get("/admin/ann_eval/{job_id}")
def get_ann_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

@app.get("/admin/ann_eval/{job_id}/result")
def get_ann_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.get("status") != "succeeded":
        raise HTTPException(status_code=400, detail="result not ready")
    rpath = job.get("result_path")
    if not rpath or not os.path.exists(rpath):
        raise HTTPException(status_code=500, detail="result file missing")
    with open(rpath, "r", encoding="utf-8") as fh:
        return json.load(fh)


@app.post("/admin/doc_similarity")
def admin_doc_similarity(payload: Dict[str, Any]):
    if storage is None or embed_adapter is None:
        raise HTTPException(status_code=500, detail="service not initialized")

    token = payload.get("token")
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    doc_id = payload.get("document_id")
    q = payload.get("q")
    top_k = int(payload.get("top_k") or 20)
    source = payload.get("source") or "confluence"
    if not doc_id or not q:
        raise HTTPException(status_code=400, detail="document_id and q are required")

    rows = []
    try:
        with _db_connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                try:
                    cur.execute(
                        "SELECT id, chunk_text, meta, embedding_vector::float8[] AS emb "
                        "FROM chunks WHERE document_id = %s AND embedding_vector IS NOT NULL",
                        (int(doc_id),),
                    )
                    rows = cur.fetchall()
                except Exception:
                    cur.execute(
                        "SELECT id, chunk_text, meta, embedding_vector::text AS emb_text "
                        "FROM chunks WHERE document_id = %s AND embedding_vector IS NOT NULL",
                        (int(doc_id),),
                    )
                    raw = cur.fetchall()
                    for r in raw:
                        rows.append(
                            {
                                "id": r["id"],
                                "chunk_text": r["chunk_text"],
                                "meta": r["meta"],
                                "emb_text": r["emb_text"],
                            }
                        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error fetching chunks: {e}")

    if not rows:
        return {"document_id": doc_id, "num_chunks": 0, "max_sim": 0.0, "mean_sim": 0.0, "per_chunk": []}

    try:
        qvecs = embed_adapter.embed_many([q], source=source, batch_size=1)
        if not qvecs:
            raise RuntimeError("embed_adapter returned no vector")
        qvec = list(map(float, qvecs[0]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error for query: {e}")

    def dot(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def norm(a: List[float]) -> float:
        return sqrt(sum(x * x for x in a))

    qnorm = norm(qvec) + 1e-12

    sims = []
    for r in rows:
        chunk_id = r.get("id")
        sample = (r.get("chunk_text") or "")[:800]
        emb = r.get("emb")
        if emb is None:
            emb_text = r.get("emb_text")
            if isinstance(emb_text, str):
                s = emb_text.strip()
                if s.startswith("[") and s.endswith("]"):
                    inner = s[1:-1].strip()
                    try:
                        emb = [float(x) for x in inner.split(",")] if inner else []
                    except Exception:
                        emb = None

        if emb is None:
            sims.append({"chunk_id": chunk_id, "sample": sample, "sim": None, "dim_mismatch": None})
            continue

        emb = [float(x) for x in emb]
        if len(emb) != len(qvec):
            sims.append({"chunk_id": chunk_id, "sample": sample, "sim": None, "dim_mismatch": len(emb)})
            continue

        sim = dot(qvec, emb) / (qnorm * (norm(emb) + 1e-12))
        sims.append({"chunk_id": chunk_id, "sample": sample, "sim": float(sim)})

    sims_valid = [s["sim"] for s in sims if isinstance(s.get("sim"), (int, float))]
    max_sim = max(sims_valid) if sims_valid else 0.0
    mean_sim = (sum(sims_valid) / len(sims_valid)) if sims_valid else 0.0

    sims.sort(key=lambda x: (x.get("sim") is not None, x.get("sim") or -999), reverse=True)

    return {
        "document_id": doc_id,
        "num_chunks": len(sims),
        "max_sim": float(max_sim),
        "mean_sim": float(mean_sim),
        "per_chunk": sims[:int(top_k)],
    }


if __name__ == "__main__":
    uvicorn.run("retrieval_api:app", host="0.0.0.0", port=int(os.getenv("API_PORT", "8000")), reload=True)
