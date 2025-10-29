# ui/app.py (top of file) — REPLACE THE FIRST LINES WITH THIS BLOCK
import os
import sys

# Ensure repo root is on sys.path so `import ui.*` works when running streamlit
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import requests

from ui.tasks import load_tasks, add_task, set_done

API_BASE = st.text_input("API base URL", value=os.getenv("API_URL", "http://localhost:8000"))

st.title("Milan RAG — Minimal UI (scaffold)")

st.write("Note: Ingest flows use credentials from the API server's `.env` by default. "
         "Leave credential fields empty to use server .env values.")

# -------------------------------------------------------
# Connector tests (optional)
# -------------------------------------------------------
st.header("Connector Tests (optional)")
with st.form("test_connectors_form"):
    ctype = st.selectbox("Connector", ["confluence", "github"], key="test_connector_type")
    if ctype == "confluence":
        base = st.text_input("Confluence Base URL (optional)", value=os.getenv("CONFLUENCE_BASE_URL", ""), key="test_conf_base")
        user = st.text_input("Confluence Username (optional)", value=os.getenv("CONFLUENCE_USERNAME", ""), key="test_conf_user")
        token = st.text_input("Confluence Token (optional)", value=os.getenv("CONFLUENCE_TOKEN", ""), key="test_conf_token", type="password")
        submitted = st.form_submit_button("Test Confluence")
        if submitted:
            try:
                resp = requests.post(f"{API_BASE.rstrip('/')}/test_connectors", json={
                    "type": "confluence",
                    "base_url": base or None,
                    "username": user or None,
                    "token": token or None
                }, timeout=15)
                st.json(resp.json())
            except Exception as e:
                st.error(f"Test failed: {e}")
    else:
        gh_token = st.text_input("GitHub Token (optional)", value=os.getenv("GITHUB_TOKEN", ""), key="test_gh_token", type="password")
        submitted = st.form_submit_button("Test GitHub")
        if submitted:
            try:
                resp = requests.post(f"{API_BASE.rstrip('/')}/test_connectors", json={
                    "type": "github",
                    "token": gh_token or None
                }, timeout=15)
                st.json(resp.json())
            except Exception as e:
                st.error(f"Test failed: {e}")

# Confluence: collect page ids and ingest (updated)
st.header("Confluence: collect page IDs and ingest")

# --- Collect Page IDs form ---
with st.form("collect_pages_form"):
    space = st.text_input("Space Key (or leave blank for page subtree)", key="collect_space")
    page = st.text_input("Page ID (optional)", key="collect_page")
    collect = st.form_submit_button("Collect Page IDs")
    if collect:
        payload = {"space_key": space or None, "page_id": page or None}
        try:
            r = requests.post(f"{API_BASE.rstrip('/')}/confluence/page_ids", json=payload, timeout=120)
            if r.status_code == 200:
                pages = r.json().get("pages", [])
                if not pages:
                    st.warning("No pages found for that space/page.")
                else:
                    st.session_state["collected_pages"] = pages
                    st.success(f"Collected {len(pages)} pages. Select which to ingest below.")
            else:
                st.error(f"Collect failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Collect failed: {e}")

# load collected pages from session (if any)
collected = st.session_state.get("collected_pages", [])

# --- Ingest selected pages (if any collected) ---

if collected:
    st.subheader("Collected pages")
    options = [f'{p["id"]} - {p.get("title")}' for p in collected]
    selected = st.multiselect("Select pages to ingest (by id - title)", options, default=options, key="collected_selected")
    col1, col2 = st.columns([1, 2])
    with col1:
        erase_sel = st.checkbox("Erase existing for selected pages", value=False, key="erase_selected")
    with col2:
        if st.button("Ingest selected pages"):
            selected_ids = [s.split(" - ", 1)[0] for s in selected]
            if not selected_ids:
                st.warning("No pages selected to ingest.")
            else:
                payload = {
                    "base_url": None,
                    "username": None,
                    "token": None,
                    "page_ids": selected_ids,
                    "erase_existing": erase_sel,
                    "max_docs": None
                }
                try:
                    # API call may take time for many pages; increase timeout if needed
                    r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json=payload, timeout=1200)
                    # Try to render JSON if possible, otherwise show raw text
                    try:
                        st.json(r.json())
                    except Exception:
                        st.text(r.text)
                except Exception as e:
                    st.error(f"Ingest failed: {e}")

# --- Ingest whole space or subtree ---
st.subheader("Ingest whole space or subtree")
with st.form("ingest_whole_form"):
    st.markdown("Use this to ingest the entire space or a page subtree. Full ingest may be heavy; use `Max pages` for testing.")
    space2 = st.text_input("Space Key (leave blank if using Page ID)", key="ing_space")
    page2 = st.text_input("Page ID (optional)", key="ing_page")
    full_ingest = st.checkbox("Full ingest (ingest entire space/subtree — may be heavy)", value=False, key="ing_full")
    max_docs = None
    if not full_ingest:
        max_docs = st.number_input("Max pages to ingest (for testing)", min_value=1, value=100, step=10, key="ing_maxdocs")
    erase_existing = st.checkbox("Erase existing docs for this space before ingest", value=False, key="ing_erase")
    submitted_ingest = st.form_submit_button("Ingest Space / Subtree")
    if submitted_ingest:
        if not (space2 or page2):
            st.warning("Provide a Space Key or Page ID for whole-ingest.")
        else:
            payload = {
                "base_url": None,
                "username": None,
                "token": None,
                "space_key": space2 or None,
                "page_id": page2 or None,
                "page_ids": None,
                "erase_existing": erase_existing,
                "max_docs": None if full_ingest else int(max_docs)
            }
            try:
                # Warn before heavy ingestion
                if full_ingest:
                    st.warning("Starting full ingest. This may take a long time and use significant resources.")
                r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json=payload, timeout=3600)
                try:
                    st.json(r.json())
                except Exception:
                    st.text(r.text)
            except Exception as e:
                st.error(f"Ingest failed: {e}")


# -------------------------------------------------------
# GitHub ingest (uses GITHUB_TOKEN from server .env)
# -------------------------------------------------------
st.header("Ingest GitHub (uses server .env token)")
with st.form("ingest_github_form"):
    repo = st.text_input("Repo (owner/repo)", key="ing_gh_repo")
    branch = st.text_input("Branch", value="main", key="ing_gh_branch")
    submitted = st.form_submit_button("Ingest GitHub")
    if submitted:
        payload = {"repo": repo, "token": None, "branch": branch}
        try:
            r = requests.post(f"{API_BASE.rstrip('/')}/ingest/github", json=payload, timeout=600)
            st.json(r.json())
        except Exception as e:
            st.error(f"Ingest failed: {e}")


if st.sidebar.button("Tasks"):
    st.sidebar.markdown("### Project Tasks")
    tasks = load_tasks()
    for i, t in enumerate(tasks):
        col1, col2 = st.sidebar.columns([0.1, 0.9])
        done = col1.checkbox("", value=t["done"], key=f"task_done_{i}")
        if done != t["done"]:
            set_done(i, done)
        col2.markdown(f"**{t['title']}**  \n{t.get('note','')}")
    st.sidebar.write("---")
    with st.sidebar.form("add_task_form"):
        new_title = st.text_input("New task title")
        new_note = st.text_area("Note")
        side = st.checkbox("Side task", value=True)
        submitted = st.form_submit_button("Add task")
        if submitted and new_title:
            add_task(new_title, new_note, side)
            st.sidebar.experimental_rerun()

# -----------------------------------------------------------------------------
# System Checklist (verifiable tasks)
# -----------------------------------------------------------------------------
import json
from typing import Tuple

def call_api_get(path: str, timeout: int = 10):
    try:
        r = requests.get(f"{API_BASE.rstrip('/')}{path}", timeout=timeout)
        r.raise_for_status()
        return {"ok": True, "status_code": r.status_code, "json": r.json()}
    except requests.exceptions.RequestException as e:
        # include response text if available
        try:
            text = getattr(e.response, "text", None)
        except Exception:
            text = None
        return {"ok": False, "error": str(e), "response_text": text}

def call_api_post(path: str, payload: dict = None, timeout: int = 20):
    try:
        r = requests.post(f"{API_BASE.rstrip('/')}{path}", json=payload or {}, timeout=timeout)
        r.raise_for_status()
        # try to decode json
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {"ok": True, "status_code": r.status_code, "json": data}
    except requests.exceptions.RequestException as e:
        try:
            text = getattr(e.response, "text", None)
        except Exception:
            text = None
        return {"ok": False, "error": str(e), "response_text": text}

# individual checks (return (passed:bool, result:dict))
def check_api_health() -> Tuple[bool, dict]:
    out = call_api_get("/health", timeout=5)
    passed = out.get("ok") and out.get("json", {}).get("status") == "ok"
    return passed, out

def check_diagnostics() -> Tuple[bool, dict]:
    out = call_api_get("/diagnostics", timeout=20)
    passed = out.get("ok")
    return passed, out

def check_pgvector() -> Tuple[bool, dict]:
    diag = call_api_get("/diagnostics", timeout=20)
    if not diag.get("ok"):
        return False, diag
    exts = diag.get("json", {}).get("extensions", [])
    has_vector = any(e.get("extname", "").lower() == "vector" for e in exts)
    return has_vector, {"ok": True, "extensions": exts, "has_vector": has_vector}

def check_tables_and_indexes() -> Tuple[bool, dict]:
    diag = call_api_get("/diagnostics", timeout=20)
    if not diag.get("ok"):
        return False, diag
    js = diag.get("json", {})
    tables = js.get("tables_present", [])
    indexes = js.get("indexes", [])
    have_tables = set(["documents","chunks"]).issubset(set(tables))
    have_indexes = any("chunk_tsv" in idx or "embedding" in idx for idx in indexes)
    summary = {"tables": tables, "indexes": indexes}
    return (have_tables and have_indexes), summary

def check_avg_chunk_size(max_allowed=1200, min_allowed=600) -> Tuple[bool, dict]:
    diag = call_api_get("/diagnostics", timeout=20)
    if not diag.get("ok"):
        return False, diag
    avg = diag.get("json", {}).get("avg_chunk_chars")
    passed = False
    if avg is None:
        passed = False
    else:
        passed = (avg <= max_allowed and avg >= min_allowed)
    return passed, {"avg_chunk_chars": avg, "min_ok":min_allowed, "max_ok":max_allowed}

def check_confluence_connector() -> Tuple[bool, dict]:
    payload = {"type": "confluence", "base_url": None, "username": None, "token": None}
    out = call_api_post("/test_connectors", payload=payload, timeout=20)
    passed = out.get("ok") and out.get("json", {}).get("ok") is True
    return passed, out

def check_github_connector() -> Tuple[bool, dict]:
    payload = {"type": "github", "token": None}
    out = call_api_post("/test_connectors", payload=payload, timeout=20)
    passed = out.get("ok") and out.get("json", {}).get("ok") is True
    return passed, out

def check_query_sample() -> Tuple[bool, dict]:
    # run a small sample query (GET)
    try:
        r = requests.get(f"{API_BASE.rstrip('/')}/query", params={"q":"install","top_k":3}, timeout=20)
        if r.status_code == 200:
            js = r.json()
            cand = js.get("candidates", [])
            passed = len(cand) > 0
            return passed, {"status_code": r.status_code, "candidates": cand}
        else:
            return False, {"status_code": r.status_code, "text": r.text}
    except Exception as e:
        return False, {"error": str(e)}

# mapping of checks
CHECKS = [
    ("API Health", check_api_health),
    ("Diagnostics (DB/Counts)", check_diagnostics),
    ("pgvector extension", check_pgvector),
    ("Tables & Indexes", check_tables_and_indexes),
    ("Avg chunk size (~700-1200)", check_avg_chunk_size),
    ("Confluence connector", check_confluence_connector),
    ("GitHub connector", check_github_connector),
    ("Sample query (retrieval)", check_query_sample),
]

# store results in session state
if "check_results" not in st.session_state:
    st.session_state["check_results"] = {}

st.subheader("System Checklist")
st.write("Click **Verify** next to each check to run it and update the status. Use **Verify All** to run everything.")

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Verify All"):
        st.info("Running all checks... this may take a few seconds.")
        for name, fn in CHECKS:
            try:
                passed, res = fn()
            except Exception as e:
                passed, res = False, {"error": str(e)}
            st.session_state["check_results"][name] = {"passed": passed, "result": res}
            # add a task record (store the result JSON inside note)
            note_text = "Automated run from UI\n\nResult:\n" + json.dumps({"passed": passed, "result": res}, indent=2)
            add_task(f"Verify: {name}", note=note_text, side_task=False)
            st.success("All checks complete. Results stored in Tasks.")
with col2:
    if st.button("Clear Results"):
        st.session_state["check_results"] = {}
        st.success("Cleared results.")

# render each check with a verify button and status
for name, fn in CHECKS:
    row = st.session_state["check_results"].get(name, {})
    passed = row.get("passed")
    res = row.get("result")
    cols = st.columns([2,1,3])
    with cols[0]:
        st.markdown(f"**{name}**")
    with cols[1]:
        if st.button(f"Verify", key=f"verify_{name}"):
            st.info(f"Running check: {name}")
            try:
                passed, res = fn()
            except Exception as e:
                passed, res = False, {"error": str(e)}
            st.session_state["check_results"][name] = {"passed": passed, "result": res}
            # add a task record (store the result JSON inside note)
            note_text = "Automated run from UI\n\nResult:\n" + json.dumps({"passed": passed, "result": res}, indent=2)
            add_task(f"Verify: {name}", note=note_text, side_task=False)
            if passed:
                st.success(f"{name} passed")
            else:
                st.error(f"{name} failed — see details below.")
    with cols[2]:
        if passed is None:
            st.write("Not verified")
        elif passed:
            st.success("PASS")
        else:
            st.error("FAIL")
        if res:
            # show summary, allow expanding raw result
            st.write(res if isinstance(res, dict) else str(res))
            with st.expander("Show raw JSON result"):
                st.json(res)