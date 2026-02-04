# ui/app.py
"""
Milan RAG — Streamlit Admin UI (updated)
Tabs: Dashboard | Connectors | Ingest | Verification | Tasks | Roadmap | Admin
- Uses ui/tasks.py for task persistence (supports result attachments)
- Calls API endpoints under API_BASE (stored in session_state)
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import streamlit as st
import requests

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)



# tasks helpers
from ui.tasks import load_tasks, add_task, set_done, add_result, update_task, delete_task

# local UI libs (import lazily in heavy pages)
try:
    import pandas as pd
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
except Exception:
    pd = None
    AgGrid = None
    GridOptionsBuilder = None
    GridUpdateMode = None
    DataReturnMode = None
    JsCode = None

st.set_page_config(page_title="Milan RAG — Admin UI", layout="wide")

# -------------------------
# session-level API base and admin token
# -------------------------
if "API_BASE" not in st.session_state:
    st.session_state["API_BASE"] = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
if "ADMIN_TOKEN" not in st.session_state:
    st.session_state["ADMIN_TOKEN"] = os.getenv("ADMIN_TOKEN", "")

# top-bar inputs (persisted in session_state)
col_top1, col_top2 = st.columns([3, 2])
with col_top1:
    api_base_input = st.text_input("API base URL", value=st.session_state["API_BASE"], key="api_base_input")
    if api_base_input and api_base_input.rstrip("/") != st.session_state["API_BASE"]:
        st.session_state["API_BASE"] = api_base_input.rstrip("/")
with col_top2:
    admin_token_input = st.text_input("ADMIN TOKEN (for admin ops)", value=st.session_state["ADMIN_TOKEN"], type="password", key="admin_token_input")
    if admin_token_input != st.session_state["ADMIN_TOKEN"]:
        st.session_state["ADMIN_TOKEN"] = admin_token_input

API_BASE = st.session_state["API_BASE"]
ADMIN_TOKEN = st.session_state["ADMIN_TOKEN"]

st.title("Milan RAG — Admin Console")
st.markdown("Admin UI for connectors, ingestion, verification, migration and tasks.")

# -------------------------
# Helper functions
# -------------------------
def safe_rerun():
    """Call experimental rerun if available, otherwise prompt user to refresh."""
    try:
        st.experimental_rerun()
    except Exception:
        st.info("Please refresh the page to see updates.")

def call_api_get(path: str, timeout: int = 10, admin: bool = False) -> Dict[str, Any]:
    """
    GET helper: path must start with '/' (e.g. '/diagnostics').
    If admin=True, will append token param from session_state.
    """
    url = f"{st.session_state['API_BASE'].rstrip('/')}{path}"
    params = {}

    if admin:
        token = st.session_state.get("ADMIN_TOKEN")
        if token:
            params["token"] = token

    try:
        r = requests.get(url, params=params or None, timeout=timeout)
        r.raise_for_status()
        try:
            return {"ok": True, "status_code": r.status_code, "json": r.json()}
        except Exception:
            return {"ok": True, "status_code": r.status_code, "json": {"text": r.text}}
    except Exception as e:
        text = getattr(getattr(e, "response", None), "text", None)
        return {"ok": False, "error": str(e), "response_text": text}

def call_api_post(
    path: str,
    payload: dict = None,
    timeout: int = 20,
    admin: bool = False,
    params_extra: dict = None
) -> Dict[str, Any]:
    """
    POST helper: path must start with '/' (e.g. '/ingest/confluence', '/query').
    - params_extra: additional query params appended to the request URL (e.g. alpha/top_k knobs)
    - If admin=True, will add token param and inject token into JSON body if absent.
    """
    url = f"{st.session_state['API_BASE'].rstrip('/')}{path}"
    params = {}

    if params_extra:
        params.update(params_extra)

    body = payload.copy() if payload else {}

    if admin:
        token = st.session_state.get("ADMIN_TOKEN")
        if token:
            params["token"] = token
            if "token" not in body:
                body["token"] = token

    try:
        r = requests.post(url, json=body or {}, params=params or None, timeout=timeout)
        r.raise_for_status()
        try:
            return {"ok": True, "status_code": r.status_code, "json": r.json()}
        except Exception:
            return {"ok": True, "status_code": r.status_code, "json": {"text": r.text}}
    except Exception as e:
        text = getattr(getattr(e, "response", None), "text", None)
        return {"ok": False, "error": str(e), "response_text": text}

def extract_page_id_from_url(u: str) -> Optional[str]:
    if not u:
        return None
    m = re.search(r"/pages/([0-9]+)", u)
    if m:
        return m.group(1)
    m = re.search(r"pageId=([0-9]+)", u)
    if m:
        return m.group(1)
    m = re.search(r"/(\d+)(?:/|$)", u)
    if m:
        return m.group(1)
    return None

# -------------------------
# Tabs
# -------------------------
tabs = st.tabs(["Dashboard", "Connectors", "Ingest", "Query", "Verification", "Tasks", "Roadmap", "Admin"])

# -------------------------
# Dashboard
# -------------------------
with tabs[0]:
    st.header("System Dashboard")
    st.markdown("Quick system snapshot (powered by /diagnostics).")
    diag = None
    res = call_api_get("/diagnostics", timeout=6)
    if res["ok"]:
        diag = res["json"]
    if diag:
        docs = diag.get("documents_count", "N/A")
        chunks = diag.get("chunks_count", "N/A")
        avg_chars = diag.get("avg_chunk_chars", "N/A")
        ext_names = ", ".join([e.get("extname") for e in diag.get("extensions", [])]) if diag.get("extensions") else "N/A"
        col1, col2, col3 = st.columns(3)
        col1.metric("Documents", docs)
        col2.metric("Chunks", chunks)
        col3.metric("Avg chunk chars", avg_chars)
        st.markdown(f"**Extensions:** {ext_names}")
        st.markdown("**Indexes:**")
        st.table(diag.get("indexes", []))
    else:
        st.warning("Diagnostics not available. Check API base and that API is running.")

# -------------------------
# Connectors
# -------------------------
with tabs[1]:
    st.header("Connectors")
    st.write("Test connectors — leave fields blank to use `.env` on the server.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Confluence")
        conf_base = st.text_input("Confluence Base URL", value=os.getenv("CONFLUENCE_BASE_URL", ""), key="conf_base")
        conf_user = st.text_input("Confluence Username", value=os.getenv("CONFLUENCE_USERNAME", ""), key="conf_user")
        conf_token = st.text_input("Confluence Token", value=os.getenv("CONFLUENCE_TOKEN", ""), key="conf_token", type="password")
        if st.button("Test Confluence"):
            payload = {"type": "confluence", "base_url": conf_base or None, "username": conf_user or None, "token": conf_token or None}
            res = call_api_post("/test_connectors", payload=payload, timeout=15)
            if res["ok"]:
                st.success("Confluence test OK")
                st.json(res["json"])
            else:
                err = res.get("response_text") or res.get("error")
                st.error(f"Confluence test failed: {err}")

    with c2:
        st.subheader("GitHub")
        gh_token = st.text_input("GitHub Token (optional)", value=os.getenv("GITHUB_TOKEN", ""), key="gh_token", type="password")
        if st.button("Test GitHub"):
            payload = {"type": "github", "token": gh_token or None}
            res = call_api_post("/test_connectors", payload=payload, timeout=15)
            if res["ok"]:
                st.success("GitHub test OK")
                st.json(res["json"])
            else:
                err = res.get("response_text") or res.get("error")
                st.error(f"GitHub test failed: {err}")

# -------------------------
# Ingest
# -------------------------
with tabs[2]:
    st.header("Ingest")
    st.markdown("Collect Confluence pages, select, and ingest. GitHub ingest supported.")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Confluence — collect & ingest")
        collect_page_url = st.text_input("Confluence Page URL (optional)", key="collect_page_url")
        space = st.text_input("Space Key (or blank for subtree)", key="collect_space")
        page = st.text_input("Page ID (optional)", key="collect_page")

        if st.button("Collect Page IDs"):
            # prefer URL if provided, then explicit page ID, then space
            effective_page = None
            if collect_page_url:
                pid = extract_page_id_from_url(collect_page_url.strip())
                if not pid:
                    st.error("Could not extract page id from URL. Ensure URL contains /pages/<id>/ or ?pageId=<id>.")
                else:
                    effective_page = pid
            else:
                effective_page = page or None

            payload = {
                "base_url": conf_base or None,
                "username": conf_user or None,
                "token": conf_token or None,
                "space_key": space or None,
                "page_id": effective_page
            }
            res = call_api_post("/confluence/page_ids", payload, timeout=60)
            if not res["ok"]:
                st.error(f"Collect failed: {res.get('response_text') or res.get('error')}")
            else:
                pages = res["json"].get("pages", [])
                st.session_state["collected_pages"] = pages
                st.success(f"Collected {len(pages)} pages")

        collected = st.session_state.get("collected_pages", [])
        if collected:
            st.subheader("Collected pages")
            options = [f'{p["id"]} - {p.get("title")}' for p in collected]
            selected = st.multiselect("Select pages to ingest", options, default=options, key="col_select")
            erase_sel = st.checkbox("Erase existing for selected pages", value=False)
            if st.button("Ingest selected pages"):
                sel_ids = [s.split(" - ", 1)[0] for s in selected]
                if not sel_ids:
                    st.warning("Select pages to ingest first.")
                else:
                    payload = {
                        "page_ids": sel_ids,
                        "erase_existing": erase_sel,
                        "base_url": conf_base or None,
                        "username": conf_user or None,
                        "token": conf_token or None
                    }
                    res = call_api_post("/ingest/confluence", payload, timeout=1200)
                    if not res["ok"]:
                        st.error(f"Ingest failed: {res.get('response_text') or res.get('error')}")
                    else:
                        resp = res["json"]
                        docs_ins = resp.get("documents_inserted") or resp.get("documents", 0)
                        docs_skip = resp.get("documents_skipped", 0)
                        docs_fail = resp.get("documents_failed", 0)
                        chunks_ins = resp.get("chunks_inserted") or resp.get("chunks", 0)
                        st.success(f"Ingest finished — inserted {docs_ins} docs, skipped {docs_skip}, failed {docs_fail}, chunks {chunks_ins}")
                        if resp.get("skipped_reasons"):
                            st.write("Skipped reasons:", resp["skipped_reasons"])
                        if resp.get("details"):
                            try:
                                import pandas as _pd
                                df = _pd.DataFrame(resp["details"])
                                st.dataframe(df)
                            except Exception:
                                st.json(resp["details"])
                        add_task(f"Ingested {len(sel_ids)} pages", note=f"Selected pages", side_task=False, result=resp)

        st.subheader("Ingest whole space / subtree")
        space2 = st.text_input("Space Key (or blank)", key="ing_space")
        page2 = st.text_input("Page ID (optional)", key="ing_page")
        page2_url = st.text_input("Or Confluence Page URL (optional)", key="ing_page_url")
        full_ingest = st.checkbox("Full ingest (entire space/subtree)", value=False)
        max_docs = st.number_input("Max pages (0 or blank = all)", min_value=0, value=0, step=50, key="ing_max_docs")
        erase_existing = st.checkbox("Erase existing for this space before ingest", value=False)
        if st.button("Start whole ingest"):
            effective_page2 = None
            if page2_url:
                pid2 = extract_page_id_from_url(page2_url.strip())
                if not pid2:
                    st.error("Could not extract page id from Page URL. Provide a valid Confluence page URL.")
                else:
                    effective_page2 = pid2
            else:
                effective_page2 = page2 or None

            if not (space2 or effective_page2):
                st.warning("Provide space key or page id (or paste page URL).")
            else:
                payload = {
                    "base_url": conf_base or None,
                    "username": conf_user or None,
                    "token": conf_token or None,
                    "space_key": space2 or None,
                    "page_id": effective_page2 or None,
                    "erase_existing": erase_existing,
                    "max_docs": None if full_ingest or max_docs == 0 else int(max_docs)
                }
                res = call_api_post("/ingest/confluence", payload, timeout=3600)
                if not res["ok"]:
                    st.error(f"Ingest failed: {res.get('response_text') or res.get('error')}")
                else:
                    resp = res["json"]
                    docs_ins = resp.get("documents_inserted") or resp.get("documents", 0)
                    docs_skip = resp.get("documents_skipped", 0)
                    docs_fail = resp.get("documents_failed", 0)
                    chunks_ins = resp.get("chunks_inserted") or resp.get("chunks", 0)
                    st.success(f"Ingest finished — inserted {docs_ins} docs, skipped {docs_skip}, failed {docs_fail}, chunks {chunks_ins}")
                    if resp.get("skipped_reasons"):
                        st.write("Skipped reasons:", resp["skipped_reasons"])
                    if resp.get("details"):
                        try:
                            import pandas as _pd
                            df = _pd.DataFrame(resp["details"])
                            st.dataframe(df)
                        except Exception:
                            st.json(resp["details"])
                    add_task(f"Ingest space {space2 or effective_page2}", note="Whole/limited ingest", side_task=False, result=resp)

    with right:
        st.subheader("GitHub ingest")
        repo = st.text_input("Repo (owner/repo)", key="ing_repo")
        branch = st.text_input("Branch", value="main", key="ing_branch")
        gh_token_local = st.text_input("GitHub token (optional)", value="", key="ing_gh_token", type="password")
        if st.button("Ingest GitHub"):
            payload = {"repo": repo, "token": gh_token_local or None, "branch": branch}
            res = call_api_post("/ingest/github", payload, timeout=600)
            if not res["ok"]:
                st.error(f"Ingest failed: {res.get('response_text') or res.get('error')}")
            else:
                resp = res["json"]
                docs = resp.get("documents") or resp.get("documents_inserted") or 0
                chunks = resp.get("chunks") or resp.get("chunks_inserted") or 0
                st.success(f"Ingest finished — documents {docs}, chunks {chunks}")
                st.json(resp)
                add_task(f"Ingest GitHub {repo}", note=f"branch={branch}", side_task=False, result=resp)

# -------------------------
# Query — hybrid retrieval (ANN + FTS)
# -------------------------
# -------------------------
# Query — hybrid retrieval (ANN + FTS)
# -------------------------
with tabs[3]:
    st.header("Query — hybrid retrieval (ANN + FTS)")
    st.markdown(
        "Quick querying UI (ANN + FTS fusion). "
        "You can choose chunk-level or document-level results, boost title chunks, and request reranking."
    )

    # Query inputs
    c1, c2 = st.columns([3, 1])
    with c1:
        q_text = st.text_input("Query text", value="JoinResponse", key="query_text")
        q_top_k = st.number_input("Top K to return", min_value=1, value=10, key="query_top_k")  # default 10
        q_alpha = st.slider("Dense weight α (alpha)", min_value=0.0, max_value=1.0, value=0.7, step=0.05, key="query_alpha")
        q_k_dense = st.number_input("k_dense (ANN candidates)", min_value=1, value=200, key="query_k_dense")
        q_k_fts = st.number_input("k_fts (FTS candidates)", min_value=1, value=100, key="query_k_fts")
        q_rerank = st.checkbox("Request reranker (server-side if configured)", value=False, key="query_rerank")

        # NEW UI controls for document-level behaviour and title-boost
        doc_level = st.checkbox("Document-level ranking (aggregate chunks → documents)", value=False, key="query_doc_level")
        title_boost = st.slider("Title chunk boost (additive)", min_value=0.0, max_value=1.0, value=0.20, step=0.01, key="query_title_boost")
        agg_method = st.selectbox("Document aggregation method", options=["max", "avg"], index=0, key="query_agg_method")

        rerank_top_k = st.number_input("Reranker pool (top N chunks)", min_value=1, value=100, key="query_rerank_pool")
        rerank_weight = st.number_input("Rerank weight (blend score)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="query_rerank_weight")

    with c2:
        q_admin_token = st.text_input("Admin token (optional, for document inspect)", value="", type="password", key="query_admin_token")
        run_q = st.button("Run Query", key="run_query_button")

    if run_q:
        if not q_text or not q_text.strip():
            st.warning("Please enter a query.")
        else:
            payload = {"q": q_text.strip()}
            params = {
                "k_dense": int(q_k_dense),
                "k_fts": int(q_k_fts),
                "alpha": float(q_alpha),
                "top_k": int(q_top_k),
                "rerank": bool(q_rerank),
                "rerank_top_k": int(rerank_top_k),
                "rerank_weight": float(rerank_weight),
                # If/when backend supports these:
                # "doc_level": bool(doc_level),
                # "title_boost": float(title_boost),
                # "agg_method": agg_method,
            }
            body = {"q": q_text.strip()}

            res = call_api_post("/query", payload=body, params_extra=params, timeout=60)

            if not res["ok"]:
                st.error(f"Query failed: {res.get('response_text') or res.get('error')}")
            else:
                out = res["json"]

                # If server returned document-level results
                if out.get("documents") is not None:
                    docs = out.get("documents", [])
                    st.markdown(f"### Document-level Results — {len(docs)} documents (top_k={out.get('top_k')})")
                    if not docs:
                        st.info("No document-level candidates returned.")
                    else:
                        try:
                            import pandas as _pd
                            from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

                            rows = []
                            for d in docs:
                                rows.append({
                                    "doc_id": d.get("document_id"),
                                    "score": round(float(d.get("score") or d.get("doc_score") or 0.0), 6),
                                    "title": d.get("title"),
                                    "url": d.get("url"),
                                    "best_chunk_id": d.get("best_chunk_id"),
                                    "best_chunk_text": (d.get("best_chunk_text") or "")[:800]
                                })
                            df = _pd.DataFrame(rows)

                            gb = GridOptionsBuilder.from_dataframe(df)
                            gb.configure_column("doc_id", header_name="Doc ID", width=100, pinned="left")
                            gb.configure_column("score", header_name="Score", width=130)
                            gb.configure_column("title", header_name="Title", width=350)
                            gb.configure_column("best_chunk_text", header_name="Best chunk (excerpt)", wrapText=True, autoHeight=True)
                            gb.configure_selection(selection_mode="single", use_checkbox=True)
                            gb.configure_default_column(filter=True, sortable=True, resizable=True)
                            grid_opts = gb.build()

                            grid_resp = AgGrid(
                                df,
                                gridOptions=grid_opts,
                                enable_enterprise_modules=False,
                                update_mode=GridUpdateMode.SELECTION_CHANGED,
                                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                                fit_columns_on_grid_load=True,
                                theme="alpine",
                                height=520
                            )
                            selected = grid_resp.get("selected_rows") or []
                        except Exception:
                            st.exception("UI widgets missing (install pandas & streamlit-aggrid). Showing raw JSON instead.")
                            st.json(out)
                            selected = []

                        # show MCP/context and controls
                        st.markdown("**MCP context**")
                        if out.get("mcp_context"):
                            st.code(out.get("mcp_context", ""), language="text")
                        # inspect selected document
                        if selected:
                            sel = selected[0]
                            sel_doc_id = sel.get("doc_id")
                            if sel_doc_id:
                                if st.button("Inspect selected document", key="inspect_selected_doc_doclevel"):
                                    token_param = q_admin_token.strip() or None
                                    path = f"/admin/document/{int(sel_doc_id)}"
                                    if token_param:
                                        path = path + f"?token={token_param}"
                                    doc_res = call_api_get(path, timeout=10)
                                    if not doc_res["ok"]:
                                        st.error(f"Document inspect failed: {doc_res.get('response_text') or doc_res.get('error')}")
                                    else:
                                        st.subheader(f"Document {sel_doc_id} — detail")
                                        st.json(doc_res["json"])

                # else fallback to chunk-level candidates (original behaviour)
                else:
                    candidates = out.get("candidates", [])
                    st.markdown(f"### Chunk-level Results — {len(candidates)} candidates (showing top_k={out.get('top_k')})")
                    if not candidates:
                        st.info("No candidates returned.")
                    else:
                        try:
                            import pandas as _pd
                            from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

                            rows = []
                            for c in candidates:
                                rows.append({
                                    "chunk_id": c.get("id"),
                                    "doc_id": c.get("document_id"),
                                    "score": round(float(c.get("fused_score") or c.get("dense_sim") or 0.0), 6),
                                    "title": (c.get("meta") or {}).get("title"),
                                    "url": (c.get("meta") or {}).get("url"),
                                    "sample": (c.get("chunk_text") or "")[:800]
                                })
                            df = _pd.DataFrame(rows)

                            gb = GridOptionsBuilder.from_dataframe(df)
                            gb.configure_column("chunk_id", header_name="Chunk ID", width=110, pinned="left")
                            gb.configure_column("doc_id", header_name="Doc ID", width=100)
                            gb.configure_column("score", header_name="Score", width=120)
                            gb.configure_column("title", header_name="Title", width=300)
                            gb.configure_column("sample", header_name="Chunk sample", wrapText=True, autoHeight=True)
                            gb.configure_selection(selection_mode="single", use_checkbox=True)
                            gb.configure_default_column(filter=True, sortable=True, resizable=True)
                            grid_opts = gb.build()

                            grid_resp = AgGrid(
                                df,
                                gridOptions=grid_opts,
                                enable_enterprise_modules=False,
                                update_mode=GridUpdateMode.SELECTION_CHANGED,
                                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                                fit_columns_on_grid_load=True,
                                theme="alpine",
                                height=520
                            )
                            selected = grid_resp.get("selected_rows") or []
                        except Exception:
                            st.exception("UI widgets missing (install pandas & streamlit-aggrid). Showing raw JSON instead.")
                            st.json(out)
                            selected = []

                        # show MCP/context and controls
                        st.markdown("**MCP context**")
                        if out.get("mcp_context"):
                            st.code(out.get("mcp_context", ""), language="text")

                        # inspect selected doc/chunk
                        if selected:
                            sel = selected[0]
                            sel_doc_id = sel.get("doc_id")
                            if sel_doc_id:
                                if st.button("Inspect selected document", key="inspect_selected_doc_chunklevel"):
                                    token_param = q_admin_token.strip() or None
                                    path = f"/admin/document/{int(sel_doc_id)}"
                                    if token_param:
                                        path = path + f"?token={token_param}"
                                    doc_res = call_api_get(path, timeout=10)
                                    if not doc_res["ok"]:
                                        st.error(f"Document inspect failed: {doc_res.get('response_text') or doc_res.get('error')}")
                                    else:
                                        st.subheader(f"Document {sel_doc_id} — detail")
                                        st.json(doc_res["json"])


# -------------------------
# Verification
# -------------------------
with tabs[4]:
    st.header("Verification & Diagnostics")
    st.markdown("Run system checks and store results as Tasks.")

    def check_api_health() -> Tuple[bool, Any]:
        resp = call_api_get("/health", 5)
        return resp["ok"], resp

    def check_diagnostics() -> Tuple[bool, Any]:
        res = call_api_get("/diagnostics", 20)
        return res["ok"], res

    CHECKS = [
        ("API Health", check_api_health),
        ("Diagnostics", check_diagnostics),
    ]

    st.write("Run checks individually or run all.")
    for name, fn in CHECKS:
        cols = st.columns([2, 1, 3])
        cols[0].markdown(f"**{name}**")
        if cols[1].button(f"Verify {name}", key=f"verify_{name}"):
            ok, out = fn()
            add_task(f"Verify: {name}", note=f"Result stored", side_task=False, result=out)
            if ok:
                st.success(f"{name} OK")
                st.json(out)
            else:
                st.error(f"{name} failed")
                st.json(out)

    if st.button("Verify All"):
        for name, fn in CHECKS:
            ok, out = fn()
            add_task(f"Verify: {name}", note=f"Automated run", side_task=False, result=out)
        st.success("All checks added as tasks")

# -------------------------
# Tasks (AgGrid table view)
# -------------------------
with tabs[5]:
    st.header("Tasks — Interactive Table")
    st.markdown("Interactive task table: search, filter, select, mark done, delete, view results, and export.")

    tasks = load_tasks()
    if not tasks:
        st.info("No tasks found. Run diagnostics or add tasks.")
    else:
        try:
            import pandas as pd
            from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
        except Exception as e:
            st.error("Please install dependencies: pip install streamlit-aggrid pandas")
            st.stop()

        rows = []
        for i, t in enumerate(tasks):
            result_status = None
            r = t.get("result")
            if isinstance(r, dict):
                status = r.get("status")
                if status:
                    result_status = status
                else:
                    summary = r.get("summary") or {}
                    if isinstance(summary, dict) and summary.get("status"):
                        result_status = summary.get("status")
                    else:
                        result_status = "has_result"
            else:
                result_status = "no_result"

            rows.append({
                "idx": i,
                "title": t.get("title", ""),
                "note": (t.get("note") or "")[:200],
                "done": bool(t.get("done", False)),
                "side": bool(t.get("side", False)),
                "has_result": bool(t.get("result")),
                "result_status": result_status
            })

        df = pd.DataFrame(rows)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True, groupSelectsChildren=True)
        gb.configure_column("idx", header_name="Index", pinned='left', width=80)
        gb.configure_column("title", header_name="Title", width=300)
        gb.configure_column("note", header_name="Note", wrapText=True, autoHeight=True)
        gb.configure_column("done", header_name="Done", editable=True, width=110)
        gb.configure_column("side", header_name="Side Task", width=110)
        gb.configure_column("has_result", header_name="Has Result", width=110)
        gb.configure_column("result_status", header_name="Result Status", width=150)
        gb.configure_default_column(filter=True, sortable=True, resizable=True)
        grid_options = gb.build()

        js_row_style = JsCode("""
        function(params) {
            if (!params || !params.data) return {};
            if (params.data.done === true) {
                return {'backgroundColor': '#e6ffe6'};
            }
            if (params.data.result_status && params.data.result_status.toString().toLowerCase().indexOf('failed') !== -1) {
                return {'backgroundColor': '#fff0f0'};
            }
            return {};
        }
        """)
        grid_options['getRowStyle'] = js_row_style

        grid_resp = AgGrid(
            df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='alpine',
            height=420,
            allow_unsafe_jscode=True
        )

        updated_data = None
        try:
            updated_data = grid_resp.get("data")
        except Exception:
            updated_data = None

        if updated_data is not None:
            cur_tasks = load_tasks()
            for row in updated_data:
                try:
                    idx_val = row.get("idx")
                    if idx_val is None:
                        continue
                    idx = int(idx_val)
                except Exception:
                    continue
                desired_done = bool(row.get("done", False))
                if 0 <= idx < len(cur_tasks):
                    if cur_tasks[idx].get("done", False) != desired_done:
                        set_done(idx, desired_done)
            tasks = load_tasks()

        selected = []
        try:
            sel = grid_resp.get("selected_rows")
            if sel is None:
                selected = []
            elif isinstance(sel, list):
                selected = sel
            else:
                try:
                    import pandas as _pd
                    if isinstance(sel, _pd.DataFrame):
                        selected = sel.to_dict("records")
                    else:
                        selected = [dict(x) if not isinstance(x, dict) else x for x in sel]
                except Exception:
                    try:
                        selected = list(sel)
                    except Exception:
                        selected = []
        except Exception:
            selected = []

        selected_idxs = []
        for r in selected:
            if not isinstance(r, dict):
                continue
            try:
                idx_val = r.get("idx")
            except Exception:
                idx_val = None
            if idx_val is None:
                continue
            try:
                selected_idxs.append(int(idx_val))
            except Exception:
                continue

        st.markdown("---")
        col_a, col_b, col_c, col_d = st.columns([1,1,1,1])

        if col_a.button("Mark selected DONE"):
            if not selected_idxs:
                st.info("No tasks selected.")
            else:
                for idx in selected_idxs:
                    set_done(idx, True)
                st.success(f"Marked {len(selected_idxs)} tasks done.")
                safe_rerun()

        if col_b.button("Delete selected"):
            if not selected_idxs:
                st.info("No tasks selected.")
            else:
                for idx in sorted(selected_idxs, reverse=True):
                    delete_task(idx)
                st.success(f"Deleted {len(selected_idxs)} tasks.")
                safe_rerun()

        if col_c.button("Show selected result JSON"):
            if not selected_idxs:
                st.info("No tasks selected.")
            elif len(selected_idxs) == 1:
                idx = selected_idxs[0]
                t = tasks[idx]
                st.subheader(f"Result for Task {idx}: {t.get('title')}")
                st.json(t.get("result") or {"note": "No result attached"})
            else:
                for idx in selected_idxs:
                    t = tasks[idx]
                    st.markdown(f"**Task {idx}: {t.get('title')}**")
                    st.json(t.get("result") or {"note": "No result attached"})

        if col_d.button("Export selected to CSV"):
            if not selected_idxs:
                st.info("No tasks selected.")
            else:
                export_rows = []
                for idx in selected_idxs:
                    t = tasks[idx]
                    export_rows.append({
                        "title": t.get("title"),
                        "note": t.get("note"),
                        "done": t.get("done"),
                        "side": t.get("side"),
                        "has_result": bool(t.get("result")),
                        "result_status": (t.get("result") or {}).get("status") if isinstance(t.get("result"), dict) else None
                    })
                try:
                    export_df = pd.DataFrame(export_rows)
                    csv = export_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, file_name="selected_tasks.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Export failed: {e}")

        st.markdown("---")
        st.subheader("Add a new task")
        with st.form("add_task_form"):
            title = st.text_input("Title")
            note = st.text_area("Note")
            side = st.checkbox("Side task", value=True)
            submitted = st.form_submit_button("Add")
            if submitted and title:
                add_task(title, note, side)
                st.success("Task added")
                safe_rerun()

# -------------------------
# Roadmap / Future Enhancements
# -------------------------
with tabs[6]:
    st.header("Roadmap / Future Enhancements")
    mdfile = Path("FUTURE_ENHANCEMENTS.md")
    if mdfile.exists():
        st.markdown(mdfile.read_text())
    else:
        st.info("FUTURE_ENHANCEMENTS.md not present in repo root.")

    jsonfile = Path("enhancements.json")
    if jsonfile.exists():
        st.subheader("Planned enhancements (structured)")
        enh = json.loads(jsonfile.read_text())
        for e in enh:
            st.markdown(f"**{e['id']} — {e['title']}**  \nPriority: {e['priority']}  \nComponents: {', '.join(e['components'])}  \n{e['description']}")
            st.write("")

# -------------------------
# Admin
# -------------------------
with tabs[7]:
    st.header("Admin: Migration & Eval")
    st.markdown("Admin operations. Requires admin token (set in top bar).")

    if st.button("Start embedding migration"):
        token = st.session_state.get("ADMIN_TOKEN")
        if not token:
            st.error("Admin token required (set it in the top bar).")
        else:
            res = call_api_post("/admin/migrate_embeddings", payload=None, timeout=10, admin=True)
            if not res["ok"]:
                st.error(f"Failed to start migration: {res.get('response_text') or res.get('error')}")
            else:
                job = res["json"]
                job_id = job.get("job_id")
                st.info(f"Started migration job {job_id}")
                last_log = ""
                while True:
                    time.sleep(2)
                    status_res = call_api_get(f"/admin/migration_status/{job_id}", timeout=10, admin=True)
                    if not status_res["ok"]:
                        st.error(f"Failed to poll migration status: {status_res.get('response_text') or status_res.get('error')}")
                        break
                    js = status_res["json"]
                    status = js.get("status")
                    st.markdown(f"Status: **{status}**")
                    log_tail = js.get("log_tail") or ""
                    if log_tail != last_log:
                        st.text_area("Log (tail)", value=log_tail, height=300, key=f"log_{job_id}")
                        last_log = log_tail
                    if status in ("succeeded", "failed"):
                        add_task(f"Embedding migration {job_id}", note=f"status={status}", side_task=False, result=js)
                        st.success(f"Migration {status}")
                        break

    st.markdown("---")
    st.subheader("ANN Eval (server-side if available)")
    ef_choice = st.selectbox("ef_search", [32, 64, 128, 256], index=1)
    top_k = st.number_input("top_k_candidates", min_value=10, value=100)
    gt_file = st.file_uploader("Upload GT JSONL (q + relevant_doc_ids)", type=["jsonl", "txt"])
    if st.button("Run ANN Eval"):
        if gt_file is None:
            st.error("Upload GT file first")
        else:
            tmp = Path("tools") / "gt_queries.jsonl"
            tmp.write_bytes(gt_file.getvalue())
            body = {"queries": str(tmp), "top_k": int(top_k), "ef_search": int(ef_choice)}
            res = call_api_post("/admin/ann_eval", payload=body, timeout=10, admin=True)
            if not res["ok"]:
                st.error(f"ANN eval failed: {res.get('response_text') or res.get('error')}")
            else:
                st.json(res["json"])
                add_task("ANN eval", note=f"ef_search={ef_choice}", side_task=False, result=res["json"])

st.markdown("---")
st.caption("Milan RAG — Admin UI")
