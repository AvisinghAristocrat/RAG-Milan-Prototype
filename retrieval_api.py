# retrieval_api.py
"""
Retrieval API - complete
Endpoints:
 - GET /health
 - POST /test_connectors
 - POST /confluence/page_ids
 - POST /ingest/confluence
 - POST /ingest/github
"""
from __future__ import annotations
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="Milan RAG - Retrieval API")

# config
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

# globals populated at startup
storage: Optional[PostgresStorage] = None
embedder: Optional[Embedder] = None
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


class IngestGithubRequest(BaseModel):
    repo: str
    token: Optional[str] = None
    branch: str = "main"

@app.on_event("startup")
def startup():
    global storage, embed_adapter
    # wait for DB to be reachable
    wait_for_db(DB_URL, timeout=60)
    storage = PostgresStorage(DB_URL)
    storage.create_tables()
    # Instantiate embed adapter - route sources to appropriate models
    # Optionally set model names via env: DOC_EMBED_MODEL, CODE_EMBED_MODEL
    embed_adapter = EmbedAdapter(doc_model=os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2"),
                                 code_model=os.getenv("CODE_EMBED_MODEL", None))


# -----------------------
# utilities
# -----------------------
def wait_for_db(url: str, timeout: int = 60):
    """Poll until Postgres accepts connection or raise."""
    import psycopg
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


# -----------------------
# startup
# -----------------------
@app.on_event("startup")
def startup():
    global storage, embedder
    # wait for DB to be reachable
    wait_for_db(DB_URL, timeout=60)
    storage = PostgresStorage(DB_URL)
    storage.create_tables()
    embedder = Embedder()


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
        pages = conf_conn.fetch_pages(base, user, token, space_key=req.space_key, page_id=req.page_id, limit=req.limit)
        simplified = [{"id": p["id"], "title": p.get("title"), "url": p.get("url")} for p in pages]
        return {"pages": simplified}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {e}")


@app.post("/ingest/confluence")
def ingest_confluence(req: IngestByPageIdsRequest):
    """
    Ingest Confluence pages. Accepts:
      - page_ids list  OR
      - space_key / page_id
    Optionally erase_existing (by space) if provided.
    """
    base = req.base_url or os.getenv("CONFLUENCE_BASE_URL")
    user = req.username or os.getenv("CONFLUENCE_USERNAME")
    token = req.token or os.getenv("CONFLUENCE_TOKEN")
    if not (base and user and token):
        raise HTTPException(status_code=400, detail="Confluence credentials missing (base/username/token)")

    pages = []
    try:
        if req.page_ids:
            # fetch each page individually (preserves content)
            for pid in req.page_ids:
                p = conf_conn.fetch_pages(base, user, token, page_id=pid)
                if p:
                    pages.extend(p)
        else:
            if not (req.space_key or req.page_id):
                raise HTTPException(status_code=400, detail="Provide page_ids or space_key/page_id")
            pages = conf_conn.fetch_pages(base, user, token, space_key=req.space_key, page_id=req.page_id, limit=100)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching pages: {e}")

    # Optional: erase existing for this space if requested
    if req.erase_existing and req.space_key:
        try:
            with storage.conn.cursor() as cur:
                cur.execute("DELETE FROM chunks WHERE (meta->>'space') = %s", (req.space_key,))
                cur.execute("DELETE FROM documents WHERE id NOT IN (SELECT DISTINCT document_id FROM chunks)")
                storage.conn.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to erase existing data for space {req.space_key}: {e}")

    # ingest pages
    doc_count = 0
    chunk_count = 0
    for p in pages:
        title = p.get("title", "untitled")
        url = p.get("url")
        meta = p.get("meta", {})
        doc_id = storage.insert_document(title, url, meta)
        chunks = confluence_ingest.chunk_page(p.get("content", ""))
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_many(texts)
        for c, emb in zip(chunks, embeddings):
            storage.insert_chunk(doc_id, c["text"], emb, {"page_id": p.get("id"), "title": title, "space": meta.get("space")})
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
        doc_id = storage.insert_document(f.get("path", "file"), f.get("url"), {"repo": req.repo})
        chunks = github_ingest.chunk_file(f.get("content", ""))
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_many(texts)
        for c, emb in zip(chunks, embeddings):
            storage.insert_chunk(doc_id, c["text"], emb, {"path": f.get("path")})
            chunk_count += 1
        doc_count += 1

    return {"status": "ingested", "documents": doc_count, "chunks": chunk_count}


if __name__ == "__main__":
    uvicorn.run("retrieval_api:app", host="0.0.0.0", port=int(os.getenv("API_PORT", "8000")), reload=True)
