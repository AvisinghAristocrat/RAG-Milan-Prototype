#!/usr/bin/env bash
set -euo pipefail
here="$(pwd)"
echo "Scaffolding Milan RAG repo in $here ..."

# Directories
mkdir -p api connectors ingesters embeddings storage ui tools

# Makefile
cat > Makefile <<'MAKE'
.PHONY: api
api:
  @python retrieval_api.py
MAKE

# retrieval_api.py (FastAPI orchestration)
cat > retrieval_api.py <<'PY'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from connectors import confluence as conf_conn, github as gh_conn
from ingesters import confluence_ingest, github_ingest
from storage.postgres import PostgresStorage
from embeddings.embedder import Embedder
import os

app = FastAPI(title="Milan RAG (scaffold)")

# minimal configuration via environment variables
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

# init shared components
storage = PostgresStorage(DB_URL)
storage.create_tables()
embedder = Embedder()  # lazy-load model

class ConnectorTest(BaseModel):
    type: str
    base_url: str = None
    username: str = None
    token: str = None
    repo: str = None

class IngestConfluenceRequest(BaseModel):
    base_url: str
    username: str
    token: str
    space_key: str = None
    page_id: str = None

class IngestGithubRequest(BaseModel):
    repo: str
    token: str
    branch: str = "main"

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/test_connectors")
def test_connectors(payload: ConnectorTest):
    if payload.type == "confluence":
        ok, msg = conf_conn.test_connection(payload.base_url, payload.username, payload.token)
        return {"ok": ok, "message": msg}
    elif payload.type == "github":
        ok, msg = gh_conn.test_connection(payload.token)
        return {"ok": ok, "message": msg}
    else:
        raise HTTPException(status_code=400, detail="unsupported connector type")

@app.post("/ingest/confluence")
def ingest_confluence(req: IngestConfluenceRequest):
    try:
        pages = conf_conn.fetch_pages(req.base_url, req.username, req.token, space_key=req.space_key, page_id=req.page_id)
        doc_count = 0
        chunk_count = 0
        for p in pages:
            doc_id = storage.insert_document(p["title"], p.get("url"), p.get("meta", {}))
            chunks = confluence_ingest.chunk_page(p["content"])
            # compute embeddings in batches
            texts = [c["text"] for c in chunks]
            embeddings = embedder.embed_many(texts)
            for c, emb in zip(chunks, embeddings):
                storage.insert_chunk(doc_id, c["text"], emb, {"page_id": p["id"], "title": p["title"]})
                chunk_count += 1
            doc_count += 1
        return {"status":"ingested", "documents": doc_count, "chunks": chunk_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/github")
def ingest_github(req: IngestGithubRequest):
    try:
        files = gh_conn.fetch_repo_docs(req.repo, req.token, branch=req.branch)
        doc_count = 0
        chunk_count = 0
        for f in files:
            doc_id = storage.insert_document(f["path"], f.get("url"), {"repo": req.repo})
            chunks = github_ingest.chunk_file(f["content"])
            texts = [c["text"] for c in chunks]
            embeddings = embedder.embed_many(texts)
            for c, emb in zip(chunks, embeddings):
                storage.insert_chunk(doc_id, c["text"], emb, {"path": f["path"]})
                chunk_count += 1
            doc_count += 1
        return {"status":"ingested", "documents": doc_count, "chunks": chunk_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("retrieval_api:app", host="0.0.0.0", port=8000, reload=True)
PY

# connectors/confluence.py
cat > connectors/confluence.py <<'PY'
import requests
from typing import List, Dict, Tuple

def test_connection(base_url: str, username: str, token: str) -> Tuple[bool, str]:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/rest/api/space?limit=1", auth=(username, token), timeout=10)
        if r.status_code == 200:
            return True, "ok"
        return False, f"{r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def fetch_pages(base_url: str, username: str, token: str, space_key: str = None, page_id: str = None) -> List[Dict]:
    """Fetch pages from Confluence either by space_key (all pages) or by a page_id subtree.
    Returns a list of dicts: {id, title, url, content, meta}
    Uses Confluence REST API (cloud)."""
    sess = requests.Session()
    sess.auth = (username, token)
    pages = []
    if space_key:
        url = f"{base_url.rstrip('/')}/rest/api/content?spaceKey={space_key}&limit=100&expand=body.storage,version"
        r = sess.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        for item in data.get("results", []):
            content = item.get("body", {}).get("storage", {}).get("value", "")
            pages.append({"id": item["id"], "title": item.get("title"), "url": f'{base_url.rstrip("/")}/pages/{item["id"]}', "content": content, "meta": {"version": item.get("version")}})
        # NOTE: pagination not implemented here — keep simple for scaffold
    elif page_id:
        url = f"{base_url.rstrip('/')}/rest/api/content/{page_id}?expand=body.storage"
        r = sess.get(url, timeout=30)
        r.raise_for_status()
        item = r.json()
        content = item.get("body", {}).get("storage", {}).get("value", "")
        pages.append({"id": item["id"], "title": item.get("title"), "url": f'{base_url.rstrip("/")}/pages/{item["id"]}', "content": content, "meta": {}})
    else:
        raise ValueError("space_key or page_id must be provided")
    return pages
PY

# connectors/github.py
cat > connectors/github.py <<'PY'
import requests
from typing import List, Dict, Tuple
import base64

def test_connection(token: str) -> Tuple[bool, str]:
    if not token:
        return False, "missing token"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if r.status_code == 200:
        return True, r.json().get("login")
    return False, f"{r.status_code}: {r.text[:200]}"

def fetch_repo_docs(repo_full: str, token: str, branch: str = "main") -> List[Dict]:
    """Fetch markdown/text files from a repo. Returns list of {path, url, content}"""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    owner, repo = repo_full.split("/")
    # get tree recursively
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1", headers=headers, timeout=30)
    r.raise_for_status()
    tree = r.json().get("tree", [])
    docs = []
    for item in tree:
        if item["type"] == "blob" and any(item["path"].lower().endswith(ext) for ext in [".md", ".txt", ".rst"]):
            # fetch contents
            r2 = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{item['path']}?ref={branch}", headers=headers, timeout=30)
            if r2.status_code != 200:
                continue
            data = r2.json()
            content = ""
            if data.get("encoding") == "base64" and "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            else:
                content = data.get("content", "")
            docs.append({"path": item["path"], "url": data.get("html_url"), "content": content})
    return docs
PY

# ingesters/confluence_ingest.py
cat > ingesters/confluence_ingest.py <<'PY'
import re
from typing import List, Dict

# simple HTML stripper for storage format: remove tags leaving text.
def _strip_html(storage_value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", storage_value)
    text = re.sub(r"\\s+", " ", text).strip()
    return text

def chunk_page(storage_value: str, chunk_size: int = 1600, overlap: int = 100) -> List[Dict]:
    text = _strip_html(storage_value)
    return chunk_text(text, chunk_size, overlap)

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[Dict]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i+chunk_size]
        chunks.append({"text": " ".join(chunk_words)})
        i += chunk_size - overlap
    return chunks
PY

# ingesters/github_ingest.py
cat > ingesters/github_ingest.py <<'PY'
from typing import List, Dict
import re

def chunk_file(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
    # split by paragraphs or by words
    paras = [p.strip() for p in re.split(r"\\n\\s*\\n", content) if p.strip()]
    chunks = []
    for p in paras:
        words = p.split()
        i = 0
        while i < len(words):
            chunk_words = words[i:i+chunk_size]
            chunks.append({"text": " ".join(chunk_words)})
            i += chunk_size - overlap
    if not chunks:
        # fallback to splitting content
        words = content.split()
        i = 0
        while i < len(words):
            chunk_words = words[i:i+chunk_size]
            chunks.append({"text": " ".join(chunk_words)})
            i += chunk_size - overlap
    return chunks
PY

# embeddings/embedder.py
cat > embeddings/embedder.py <<'PY'
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # lazy-load (first call downloads the model)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, text: str):
        vec = self.model.encode([text], show_progress_bar=False)[0]
        return vec.tolist()

    def embed_many(self, texts: List[str]):
        if not texts:
            return []
        vecs = self.model.encode(texts, show_progress_bar=False)
        return [v.tolist() for v in vecs]
PY

# storage/postgres.py
cat > storage/postgres.py <<'PY'
import psycopg
import json
from typing import Any, Dict
from psycopg.rows import dict_row

class PostgresStorage:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg.connect(self.db_url)

    def create_tables(self):
        q = \"\"\"
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT,
            meta JSONB
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            chunk_text TEXT,
            embedding JSONB,
            meta JSONB
        );
        \"\"\"
        with self.conn.cursor() as cur:
            cur.execute(q)
            self.conn.commit()

    def insert_document(self, title: str, url: str, meta: Dict[str, Any] = None) -> int:
        meta = meta or {}
        with self.conn.cursor() as cur:
            cur.execute(\"INSERT INTO documents (title, url, meta) VALUES (%s, %s, %s) RETURNING id\", (title, url, json.dumps(meta)))
            docid = cur.fetchone()[0]
            self.conn.commit()
            return docid

    def insert_chunk(self, document_id: int, chunk_text: str, embedding: Any, meta: Dict[str, Any] = None) -> int:
        meta = meta or {}
        with self.conn.cursor() as cur:
            cur.execute(\"INSERT INTO chunks (document_id, chunk_text, embedding, meta) VALUES (%s, %s, %s::jsonb, %s) RETURNING id\", (document_id, chunk_text, json.dumps(embedding), json.dumps(meta)))
            chunkid = cur.fetchone()[0]
            self.conn.commit()
            return chunkid
PY

# ui/app.py (Streamlit UI - simple)
cat > ui/app.py <<'PY'
import streamlit as st
import requests
import os

API_BASE = st.text_input("API base URL", value=os.getenv("API_URL", "http://localhost:8000"))
st.title("Milan RAG — Minimal UI (scaffold)")

st.header("Connector Tests")
with st.form("test_connectors"):
    ctype = st.selectbox("Connector", ["confluence","github"])
    if ctype == "confluence":
        base = st.text_input("Confluence Base URL", key="conf_base")
        user = st.text_input("Confluence Username", key="conf_user")
        token = st.text_input("Confluence Token", key="conf_token", type="password")
        submitted = st.form_submit_button("Test Confluence")
        if submitted:
            resp = requests.post(f"{API_BASE.rstrip('/')}/test_connectors", json={
                "type":"confluence","base_url":base,"username":user,"token":token
            })
            st.json(resp.json())
    else:
        token = st.text_input("GitHub Token", key="gh_token", type="password")
        submitted = st.form_submit_button("Test GitHub")
        if submitted:
            resp = requests.post(f"{API_BASE.rstrip('/')}/test_connectors", json={
                "type":"github","token":token
            })
            st.json(resp.json())

st.header("Ingest Confluence")
with st.form("ingest_conf"):
    base = st.text_input("Confluence Base URL", key="ing_conf_base")
    user = st.text_input("Confluence Username", key="ing_conf_user")
    token = st.text_input("Confluence Token", key="ing_conf_token", type="password")
    space = st.text_input("Space Key (or leave blank)")
    page = st.text_input("Page ID (optional)")
    submitted = st.form_submit_button("Ingest Confluence")
    if submitted:
        payload = {"base_url": base, "username": user, "token": token, "space_key": space or None, "page_id": page or None}
        r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json=payload, timeout=600)
        st.json(r.json())

st.header("Ingest GitHub")
with st.form("ingest_gh"):
    repo = st.text_input("Repo (owner/repo)", key="ing_gh_repo")
    token = st.text_input("GitHub Token", key="ing_gh_token", type="password")
    branch = st.text_input("Branch", value="main")
    submitted = st.form_submit_button("Ingest GitHub")
    if submitted:
        payload = {"repo": repo, "token": token, "branch": branch}
        r = requests.post(f"{API_BASE.rstrip('/')}/ingest/github", json=payload, timeout=600)
        st.json(r.json())
PY

# optional: tools/check_connectors.py - if not present we add a simple one
if [ ! -f tools/check_connectors.py ]; then
cat > tools/check_connectors.py <<'PY'
#!/usr/bin/env python3
import os, requests
def check_github(token):
    if not token:
        return "MISSING"
    r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"})
    return "OK" if r.status_code==200 else f"FAIL {r.status_code}"

def check_confluence(base, user, token):
    if not (base and user and token):
        return "MISSING"
    r = requests.get(f"{base.rstrip('/')}/rest/api/space?limit=1", auth=(user,token))
    return "OK" if r.status_code==200 else f"FAIL {r.status_code}"

print("GitHub:", check_github(os.environ.get("GITHUB_TOKEN")))
print("Confluence:", check_confluence(os.environ.get("CONFLUENCE_BASE_URL"), os.environ.get("CONFLUENCE_USERNAME"), os.environ.get("CONFLUENCE_TOKEN")))
PY
fi

echo "Scaffold complete. Next: activate venv then run 'pip install -r requirements.txt', then run 'make api' and 'streamlit run ui/app.py' in another terminal."
