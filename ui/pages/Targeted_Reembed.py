# ui/pages/Targeted_Reembed.py (full replacement)

import streamlit as st
import os, sys, pathlib, json, time
from dotenv import load_dotenv
load_dotenv()

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Targeted Re-embed", layout="wide")
st.title("Targeted Title Chunk & Re-embed")

st.markdown(
    """
Use this page to add a short **title chunk** for a document (fast) and optionally re-chunk + re-embed the whole document (background job).
**Admin token** is required for the background re-embed operation. Set the Admin Token in the top bar so it is used automatically.
"""
)

col1, col2 = st.columns(2)
with col1:
    doc_id = st.number_input("Document ID (preferred)", min_value=0, value=0, step=1)
    source = st.text_input("Source (e.g., confluence, github)")
    external_id = st.text_input("External ID (page_id or repo:path)")
with col2:
    create_title = st.checkbox("Create title chunk", value=True)
    erase_existing = st.checkbox("Erase existing title chunk if present", value=False)
    title_len = st.number_input("Title chunk length (chars)", min_value=50, max_value=2000, value=400)
    reembed_full = st.checkbox("Re-embed full document (background job)", value=False)
    model = st.text_input("Model for embedding (optional, e.g., intfloat/multilingual-e5-large-instruct)", value="")

# local helpers (use session_state API base + admin token)
import requests

def _api_post(path, payload=None, timeout=30, admin=False):
    url = f"{st.session_state.get('API_BASE', 'http://localhost:8000')}{path}"
    params = {}
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
        return {"ok": True, "json": r.json()}
    except Exception as e:
        txt = getattr(getattr(e, "response", None), "text", None)
        return {"ok": False, "error": str(e), "response_text": txt}

def _api_get(path, timeout=10, admin=False):
    url = f"{st.session_state.get('API_BASE', 'http://localhost:8000')}{path}"
    params = {}
    if admin:
        token = st.session_state.get("ADMIN_TOKEN")
        if token:
            params["token"] = token
    try:
        r = requests.get(url, params=params or None, timeout=timeout)
        r.raise_for_status()
        return {"ok": True, "json": r.json()}
    except Exception as e:
        txt = getattr(getattr(e, "response", None), "text", None)
        return {"ok": False, "error": str(e), "response_text": txt}

submitted = st.button("Run Targeted Re-embed")

if submitted:
    payload = {
        "document_id": int(doc_id) if doc_id else None,
        "source": source or None,
        "external_id": external_id or None,
        "create_title_chunk": bool(create_title),
        "title_chunk_len": int(title_len),
        "erase_existing_title_chunk": bool(erase_existing),
        "reembed_full": bool(reembed_full),
        "model": model or None,
        "batch_size": 64
    }

    if not payload["document_id"] and not (payload["source"] and payload["external_id"]):
        st.error("Provide a document_id OR source + external_id")
        st.stop()

    if payload["reembed_full"] and not st.session_state.get("ADMIN_TOKEN"):
        st.error("Admin token required for full re-embed. Set it in the top bar.")
        st.stop()

    st.info("Submitting targeted re-embed request...")
    res = _api_post("/admin/targeted_reembed", payload, timeout=120, admin=True)
    if not res["ok"]:
        st.error("Request failed: " + (res.get("response_text") or res.get("error")))
    else:
        st.success("Request submitted")
        st.json(res["json"])
        job = res["json"].get("reembed_job")
        if job:
            st.info(f"Background job created: row id = {job['job_row_id']}")

st.markdown("---")
st.header("Check ingest job status & log")
job_check_col1, job_check_col2 = st.columns([2,1])
with job_check_col1:
    check_job_id = st.number_input("Job Row ID", min_value=0, value=0, step=1, key="check_job_id")
    check_token = st.text_input("Admin token (override session)", value=st.session_state.get("ADMIN_TOKEN",""), type="password", key="check_token")
with job_check_col2:
    if st.button("Check Job"):
        if not check_job_id:
            st.warning("Enter a job id")
        else:
            token_to_use = check_token if check_token else st.session_state.get("ADMIN_TOKEN")
            if not token_to_use:
                st.error("Admin token required to check job. Set in top bar or enter here.")
            else:
                try:
                    r = requests.get(f"{st.session_state['API_BASE']}/admin/ingest_job/{int(check_job_id)}", params={"token": token_to_use}, timeout=10)
                    if r.status_code != 200:
                        st.error(r.text)
                    else:
                        st.json(r.json())
                        log_resp = requests.get(f"{st.session_state['API_BASE']}/admin/ingest_job/{int(check_job_id)}/log", params={"token": token_to_use}, timeout=15)
                        if log_resp.status_code == 200:
                            log_js = log_resp.json()
                            st.subheader("Job log (tail)")
                            st.code(log_js.get("log",""), language="text")
                        else:
                            st.warning("Log not available: " + log_resp.text)
                except Exception as e:
                    st.error(f"Failed to fetch job: {e}")
