# ui/app.py
"""
Milan RAG — Streamlit Admin UI (updated)
Tabs: Dashboard | Connectors | Ingest | Verification | Tasks | Admin
- Uses ui/tasks.py for task persistence (supports result attachments)
- Calls API endpoints under API_BASE
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Tuple, Dict, Any, List

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import requests

# tasks helpers
from ui.tasks import load_tasks, add_task, set_done, add_result, update_task, delete_task
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode


st.set_page_config(page_title="Milan RAG — Admin UI", layout="wide")

API_BASE = st.text_input("API base URL", value=os.getenv("API_URL", "http://localhost:8000"), key="api_base")
ADMIN_TOKEN_DEFAULT = os.getenv("ADMIN_TOKEN", "")
ADMIN_TOKEN = st.text_input("ADMIN TOKEN (for admin ops)", value=ADMIN_TOKEN_DEFAULT, type="password", key="admin_token")

st.title("Milan RAG — Admin Console")
st.markdown("Admin UI for connectors, ingestion, verification, migration and tasks.")

# -------------------------
# Helper functions
# -------------------------
def call_api_get(path: str, timeout: int = 10) -> Dict[str, Any]:
    try:
        r = requests.get(f"{API_BASE.rstrip('/')}{path}", timeout=timeout)
        r.raise_for_status()
        return {"ok": True, "status_code": r.status_code, "json": r.json()}
    except Exception as e:
        try:
            text = getattr(e.response, "text", None)
        except Exception:
            text = None
        return {"ok": False, "error": str(e), "response_text": text}

def call_api_post(path: str, payload: dict = None, timeout: int = 20) -> Dict[str, Any]:
    try:
        r = requests.post(f"{API_BASE.rstrip('/')}{path}", json=payload or {}, timeout=timeout)
        r.raise_for_status()
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {"ok": True, "status_code": r.status_code, "json": data}
    except Exception as e:
        try:
            text = getattr(e.response, "text", None)
        except Exception:
            text = None
        return {"ok": False, "error": str(e), "response_text": text}

# -------------------------
# Tabs
# -------------------------
tabs = st.tabs(["Dashboard", "Connectors", "Ingest", "Verification", "Tasks", "Roadmap", "Admin"])

# -------------------------
# Dashboard
# -------------------------
with tabs[0]:
    st.header("System Dashboard")
    st.markdown("Quick system snapshot (powered by /diagnostics).")
    diag = None
    try:
        diag_resp = call_api_get("/diagnostics", timeout=6)
        if diag_resp["ok"]:
            diag = diag_resp["json"]
    except Exception:
        diag = None

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
            payload = {"type":"confluence", "base_url": conf_base or None, "username": conf_user or None, "token": conf_token or None}
            res = call_api_post("/test_connectors", payload=payload, timeout=15)
            if res["ok"]:
                st.success("Confluence test OK")
                st.json(res["json"])
            else:
                st.error(f"Confluence test failed: {res.get('error') or res.get('response_text')}")
    with c2:
        st.subheader("GitHub")
        gh_token = st.text_input("GitHub Token", value=os.getenv("GITHUB_TOKEN", ""), key="gh_token", type="password")
        if st.button("Test GitHub"):
            payload = {"type":"github", "token": gh_token or None}
            res = call_api_post("/test_connectors", payload=payload, timeout=15)
            if res["ok"]:
                st.success("GitHub test OK")
                st.json(res["json"])
            else:
                st.error(f"GitHub test failed: {res.get('error') or res.get('response_text')}")

# -------------------------
# Ingest
# -------------------------
with tabs[2]:
    st.header("Ingest")
    st.markdown("Collect Confluence pages, select, and ingest. GitHub ingest supported.")

    left, right = st.columns([1,1])
    with left:
        st.subheader("Confluence — collect & ingest")
        space = st.text_input("Space Key (or blank for subtree)", key="collect_space")
        page = st.text_input("Page ID (optional)", key="collect_page")
        collect = st.button("Collect Page IDs")
        if collect:
            payload = {"space_key": space or None, "page_id": page or None}
            try:
                r = requests.post(f"{API_BASE.rstrip('/')}/confluence/page_ids", json=payload, timeout=60)
                r.raise_for_status()
                pages = r.json().get("pages", [])
                st.session_state["collected_pages"] = pages
                st.success(f"Collected {len(pages)} pages")
            except Exception as e:
                st.error(f"Collect failed: {e}")

        collected = st.session_state.get("collected_pages", [])
        if collected:
            st.subheader("Collected pages")
            options = [f'{p["id"]} - {p.get("title")}' for p in collected]
            selected = st.multiselect("Select pages to ingest", options, default=options, key="col_select")
            erase_sel = st.checkbox("Erase existing for selected pages", value=False)
            if st.button("Ingest selected pages"):
                sel_ids = [s.split(" - ",1)[0] for s in selected]
                if not sel_ids:
                    st.warning("Select pages to ingest first.")
                else:
                    payload = {"page_ids": sel_ids, "erase_existing": erase_sel}
                    try:
                        r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json=payload, timeout=1200)
                        r.raise_for_status()
                        st.json(r.json())
                        add_task(f"Ingested {len(sel_ids)} pages", note=f"Selected pages", side_task=False, result=r.json())
                    except Exception as e:
                        st.error(f"Ingest failed: {e}")

        st.subheader("Ingest whole space / subtree")
        space2 = st.text_input("Space Key (or blank)", key="ing_space")
        page2 = st.text_input("Page ID (optional)", key="ing_page")
        full_ingest = st.checkbox("Full ingest (entire space/subtree)", value=False)
        max_docs = st.number_input("Max pages (0=all)", min_value=0, value=100, step=50, key="ing_max_docs")
        erase_existing = st.checkbox("Erase existing for this space before ingest", value=False)
        if st.button("Start whole ingest"):
            if not (space2 or page2):
                st.warning("Provide space key or page id.")
            else:
                payload = {
                    "space_key": space2 or None,
                    "page_id": page2 or None,
                    "erase_existing": erase_existing,
                    "max_docs": None if full_ingest or max_docs==0 else int(max_docs)
                }
                try:
                    r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json=payload, timeout=3600)
                    r.raise_for_status()
                    st.json(r.json())
                    add_task(f"Ingest space {space2 or page2}", note="Whole/limited ingest", side_task=False, result=r.json())
                except Exception as e:
                    st.error(f"Ingest failed: {e}")

    with right:
        st.subheader("GitHub ingest")
        repo = st.text_input("Repo (owner/repo)", key="ing_repo")
        branch = st.text_input("Branch", value="main", key="ing_branch")
        if st.button("Ingest GitHub"):
            payload = {"repo": repo, "token": None, "branch": branch}
            try:
                r = requests.post(f"{API_BASE.rstrip('/')}/ingest/github", json=payload, timeout=600)
                r.raise_for_status()
                st.json(r.json())
                add_task(f"Ingest GitHub {repo}", note=f"branch={branch}", side_task=False, result=r.json())
            except Exception as e:
                st.error(f"Ingest failed: {e}")

# -------------------------
# Verification
# -------------------------
with tabs[3]:
    st.header("Verification & Diagnostics")
    st.markdown("Run system checks and store results as Tasks.")

    def check_api_health() -> Tuple[bool, Any]:
        return call_api_get("/health", 5)["ok"], call_api_get("/health", 5)

    def check_diagnostics() -> Tuple[bool, Any]:
        res = call_api_get("/diagnostics", 20)
        return res["ok"], res

    CHECKS = [
        ("API Health", check_api_health),
        ("Diagnostics", check_diagnostics),
    ]

    st.write("Run checks individually or run all.")
    for name, fn in CHECKS:
        cols = st.columns([2,1,3])
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
# Tasks (AgGrid table view)  -- complete replacement for tabs[4]
# -------------------------
with tabs[4]:
    st.header("Tasks — Interactive Table")
    st.markdown("Interactive task table: search, filter, select, mark done, delete, view results, and export.")

    tasks = load_tasks()

    if not tasks:
        st.info("No tasks found. Run diagnostics or add tasks.")
    else:
        # Import required libs locally for safety
        try:
            import pandas as pd
            from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
        except Exception as e:
            st.error("Please install dependencies: pip install streamlit-aggrid pandas")
            st.stop()

        # Build rows with idx + a short result_status for coloring
        rows = []
        for i, t in enumerate(tasks):
            result_status = None
            r = t.get("result")
            if isinstance(r, dict):
                # many job results have 'status' (succeeded/failed)
                status = r.get("status")
                if status:
                    result_status = status
                else:
                    # look for nested summary.status or similar
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

        # Configure the grid
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

        # Row style JS: green for done, red if result_status == 'failed'
        js_row_style = JsCode("""
        function(params) {
            if (!params || !params.data) return {};
            if (params.data.done === true) {
                return {'backgroundColor': '#e6ffe6'}; // light green
            }
            if (params.data.result_status && params.data.result_status.toString().toLowerCase().indexOf('failed') !== -1) {
                return {'backgroundColor': '#fff0f0'}; // light red
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

        # Persist edits done inside the grid (e.g., toggling 'done')
        updated_data = None
        try:
            updated_data = grid_resp.get("data")
        except Exception:
            updated_data = None

        if updated_data is not None:
            # updated_data is a list-of-dicts representing the current grid rows
            cur_tasks = load_tasks()
            for row in updated_data:
                try:
                    idx_val = row.get("idx")
                    if idx_val is None:
                        continue
                    idx = int(idx_val)
                except Exception:
                    continue
                # persist 'done' changes
                desired_done = bool(row.get("done", False))
                if 0 <= idx < len(cur_tasks):
                    if cur_tasks[idx].get("done", False) != desired_done:
                        set_done(idx, desired_done)
            # reload tasks
            tasks = load_tasks()

        # Safely get selected rows (normalize to list of dicts)
        selected = []
        try:
            sel = grid_resp.get("selected_rows")
            if sel is None:
                selected = []
            elif isinstance(sel, list):
                selected = sel
            else:
                # if DataFrame-like or other iterable
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

        # Build selected_idxs safely
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

        # ACTION buttons
        st.markdown("---")
        col_a, col_b, col_c, col_d = st.columns([1,1,1,1])

        if col_a.button("Mark selected DONE"):
            if not selected_idxs:
                st.info("No tasks selected.")
            else:
                for idx in selected_idxs:
                    set_done(idx, True)
                st.success(f"Marked {len(selected_idxs)} tasks done.")
                st.experimental_rerun()

        if col_b.button("Delete selected"):
            if not selected_idxs:
                st.info("No tasks selected.")
            else:
                for idx in sorted(selected_idxs, reverse=True):
                    delete_task(idx)
                st.success(f"Deleted {len(selected_idxs)} tasks.")
                st.experimental_rerun()

        if col_c.button("Show selected result JSON"):
            if not selected_idxs:
                st.info("No tasks selected.")
            elif len(selected_idxs) == 1:
                idx = selected_idxs[0]
                t = tasks[idx]
                st.subheader(f"Result for Task {idx}: {t.get('title')}")
                st.json(t.get("result") or {"note":"No result attached"})
            else:
                for idx in selected_idxs:
                    t = tasks[idx]
                    st.markdown(f"**Task {idx}: {t.get('title')}**")
                    st.json(t.get("result") or {"note":"No result attached"})

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
        # Add new task form (keeps parity with old UI)
        st.subheader("Add a new task")
        with st.form("add_task_form"):
            title = st.text_input("Title")
            note = st.text_area("Note")
            side = st.checkbox("Side task", value=True)
            submitted = st.form_submit_button("Add")
            if submitted and title:
                add_task(title, note, side)
                st.success("Task added")
                st.experimental_rerun()

# -------------------------
# Roadmap / Future Enhancements
# -------------------------
with tabs[5]:
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
with tabs[6]:
    st.header("Admin: Migration & Eval")
    st.markdown("Admin operations. Requires admin token.")
    atoken = st.text_input("Admin Token", type="password", key="admin_token_admin")
    if st.button("Start embedding migration"):
        if not atoken:
            st.error("Admin token required")
        else:
            try:
                r = requests.post(f"{API_BASE.rstrip('/')}/admin/migrate_embeddings", params={"token": atoken}, timeout=10)
                r.raise_for_status()
                job = r.json()
                job_id = job.get("job_id")
                st.info(f"Started migration job {job_id}")
                # poll status
                last_log = ""
                while True:
                    time.sleep(2)
                    s = requests.get(f"{API_BASE.rstrip('/')}/admin/migration_status/{job_id}", params={"token": atoken}, timeout=10)
                    s.raise_for_status()
                    js = s.json()
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
            except Exception as e:
                st.error(f"Failed to start migration: {e}")

    st.markdown("---")
    st.subheader("ANN Eval (server-side if available)")
    ef_choice = st.selectbox("ef_search", [32,64,128,256], index=1)
    top_k = st.number_input("top_k_candidates", min_value=10, value=100)
    gt_file = st.file_uploader("Upload GT JSONL (q + relevant_doc_ids)", type=["jsonl","txt"])
    if st.button("Run ANN Eval"):
        if gt_file is None:
            st.error("Upload GT file first")
        else:
            tmp = Path("tools") / "gt_queries.jsonl"
            tmp.write_bytes(gt_file.getvalue())
            # call server eval endpoint if exists
            try:
                r = requests.post(f"{API_BASE.rstrip('/')}/admin/eval_ann", params={"ef_search": ef_choice, "top_k": top_k}, timeout=10)
                if r.status_code == 404:
                    st.warning("Server eval endpoint not found; run tools/eval_ann.py locally.")
                else:
                    r.raise_for_status()
                    res = r.json()
                    st.json(res)
                    add_task("ANN eval", note=f"ef_search={ef_choice}", side_task=False, result=res)
            except Exception as e:
                st.error(f"Eval failed: {e}")

st.markdown("---")
st.caption("Milan RAG — Admin UI")
