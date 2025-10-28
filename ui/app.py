# ui/app.py
import streamlit as st
import requests
import os

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

# -------------------------------------------------------
# Confluence: collect page ids and ingest selected pages
# -------------------------------------------------------
st.header("Confluence: collect page IDs and ingest")

with st.form("collect_pages_form"):
    space = st.text_input("Space Key (or leave blank for page subtree)", key="collect_space")
    page = st.text_input("Page ID (optional)", key="collect_page")
    collect = st.form_submit_button("Collect Page IDs")
    if collect:
        payload = {"space_key": space or None, "page_id": page or None}
        try:
            r = requests.post(f"{API_BASE.rstrip('/')}/confluence/page_ids", json=payload, timeout=60)
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

collected = st.session_state.get("collected_pages", [])
if collected:
    st.subheader("Collected pages")
    options = [f'{p["id"]} - {p.get("title")}' for p in collected]
    selected = st.multiselect("Select pages to ingest (by id - title)", options, default=options)
    if st.button("Ingest selected pages"):
        selected_ids = [s.split(" - ", 1)[0] for s in selected]
        try:
            r = requests.post(f"{API_BASE.rstrip('/')}/ingest/confluence", json={"page_ids": selected_ids}, timeout=600)
            st.json(r.json())
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
