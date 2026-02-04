# ui/pages/ANN_Evaluation.py
import streamlit as st
import sys, pathlib, os, json, time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Ensure repo root is importable
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Local helper
try:
    from tools.generate_ground_truth import sample_documents
except Exception:
    # sample_documents may not be available in minimal setups; we'll handle errors when used.
    sample_documents = None

# Tasks API (to add tasks from results)
try:
    from ui.tasks import add_task
except Exception:
    add_task = None

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="ANN Evaluation (Admin)", layout="wide")
st.title("ANN Evaluation (Admin) — App-driven jobs")

st.markdown(
    """
This page **submits ANN evaluation jobs** to the server and shows a list of recent jobs.
Jobs run server-side, and the UI polls / shows job status, logs and results — no long blocking in the Streamlit process.
"""
)

# ---- Form to submit job ----
with st.form("ann_form", clear_on_submit=False):
    st.subheader("Create ANN Eval job")
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        mode = st.selectbox("Ground-truth source", ["generate_sample", "upload_json"], index=0)
        if mode == "generate_sample":
            n = st.number_input("Number of sample queries", min_value=5, max_value=500, value=50)
            words = st.number_input("Words per query (sample)", min_value=5, max_value=200, value=20)
            seed = st.number_input("Random seed (optional)", value=0)
        else:
            uploaded = st.file_uploader("Upload ground_truth.json", type="json")
    with c2:
        top_k = st.number_input("Top-K (recall@K)", min_value=1, max_value=500, value=10)
        ef_search = st.number_input("ef_search (HNSW)", min_value=1, max_value=2048, value=64)
        model_doc = st.text_input("Doc embed model name", value=os.getenv("DOC_EMBED_MODEL","all-MiniLM-L6-v2"))
    with c3:
        num_queries = st.number_input("num_queries (0 = all)", min_value=0, max_value=10000, value=0)
        # rerank options (optional)
        rerank = st.checkbox("Use reranker", value=False)
        rerank_weight = st.slider("Rerank weight", 0.0, 1.0, value=1.0, step=0.05)
    submitted = st.form_submit_button("Submit job")

# Helper to show message
def show_alert(msg, kind="info"):
    if kind == "error":
        st.error(msg)
    elif kind == "success":
        st.success(msg)
    else:
        st.info(msg)

# Submit action (non-blocking)
if submitted:
    # prepare queries file path that the server can read
    queries_for_server = None
    if mode == "generate_sample":
        if sample_documents is None:
            show_alert("sample_documents() not available on this environment.", "error")
            st.stop()
        try:
            st.info("Generating sample queries...")
            queries_list = sample_documents(os.getenv("DB_URL"), n=n, words=words, seed=int(seed) if seed else None)
            if not queries_list:
                show_alert("No queries were generated. Check DB or document content.", "error")
                st.stop()
            tmp_queries = ROOT / "tools" / f"uploaded_ground_truth_{int(datetime.utcnow().timestamp())}.json"
            tmp_queries.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp_queries, "w", encoding="utf-8") as fh:
                json.dump(queries_list, fh, indent=2)
            queries_for_server = str(tmp_queries)
            show_alert(f"Generated {len(queries_list)} sample queries. Submitting job...")
        except Exception as e:
            show_alert(f"Failed to generate queries: {e}", "error")
            st.code(str(e))
            st.stop()
    else:
        if uploaded is None:
            show_alert("Please upload a ground-truth JSON file", "error")
            st.stop()
        tmp = ROOT / "tools" / f"uploaded_ground_truth_{int(datetime.utcnow().timestamp())}.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "wb") as fh:
            fh.write(uploaded.getbuffer())
        queries_for_server = str(tmp)
        show_alert("Uploaded ground-truth saved to: " + str(tmp), "success")

    # Build payload
    payload = {
        "model": model_doc,
        "queries": queries_for_server,
        "top_k": int(top_k),
        "ef_search": int(ef_search),
        "num_queries": int(num_queries)
    }
    if rerank:
        payload["rerank"] = True
        payload["rerank_weight"] = float(rerank_weight)

    # create job via API
    try:
        import requests
        r = requests.post(f"{API_BASE}/admin/ann_eval", json=payload, timeout=30)
        r.raise_for_status()
        job_id = r.json().get("job_id")
        st.success(f"Job created: {job_id}")
        # store last job in session state for quick access
        st.session_state["last_ann_job"] = job_id
    except Exception as e:
        show_alert(f"Failed to create job: {e}", "error")
        st.stop()

# ---- Jobs table & controls ----
st.markdown("---")
st.subheader("Recent ANN jobs")
jobs_container = st.container()

def fetch_jobs():
    try:
        import requests
        r = requests.get(f"{API_BASE}/admin/ann_eval", timeout=10)
        r.raise_for_status()
        return r.json().get("jobs", [])
    except Exception as e:
        st.warning(f"Could not fetch job list: {e}")
        return []

jobs = fetch_jobs()

# Render jobs in a friendly way
if not jobs:
    st.info("No jobs found. Submit a job above.")
else:
    # Show as table summary (flatten params)
    rows = []
    for j in jobs:
        p = j.get("params") or {}
        rows.append({
            "id": j.get("id"),
            "status": j.get("status"),
            "created_at": j.get("created_at"),
            "started_at": j.get("started_at"),
            "finished_at": j.get("finished_at"),
            "top_k": p.get("top_k"),
            "ef_search": p.get("ef_search"),
            "model": p.get("model")
        })
    st.table(rows)

    # Per-job detail / actions
    st.markdown("**Actions** — refresh / view result / view log")
    detail_col = st.columns([3,1,1,1,1,2])  # layout for list header
    with detail_col[0]:
        st.markdown("**Job ID (click to select)**")
    with detail_col[1]:
        st.markdown("**Status**")
    with detail_col[2]:
        st.markdown("**Started**")
    with detail_col[3]:
        st.markdown("**Finished**")
    with detail_col[4]:
        st.markdown("**Result**")
    with detail_col[5]:
        st.markdown("**Actions**")

    # Container to show selected job details/log/result
    selected_job_details = st.empty()

    for j in jobs:
        jid = j.get("id")
        cols = st.columns([3,1,1,1,1,2])
        with cols[0]:
            if st.button(jid, key=f"sel_{jid}"):
                # when a job id button is clicked, fetch details and display below
                try:
                    import requests
                    job_d = requests.get(f"{API_BASE}/admin/ann_eval/{jid}", timeout=10).json()
                except Exception as e:
                    selected_job_details.error(f"Failed to fetch job {jid}: {e}")
                    job_d = None
                if job_d:
                    selected_job_details.subheader(f"Job {jid} details")
                    selected_job_details.json(job_d)
                    # Show download link if succeeded
                    if job_d.get("status") == "succeeded" and job_d.get("result_path"):
                        try:
                            res = requests.get(f"{API_BASE}/admin/ann_eval/{jid}/result", timeout=30).json()
                            selected_job_details.markdown("**Result (summary)**")
                            selected_job_details.write({
                                "num_queries": res.get("num_queries"),
                                "top_k": res.get("top_k"),
                                "ef_search": res.get("ef_search"),
                                "avg_latency_ms": res.get("avg_latency_ms"),
                                "recall_at_k": res.get("recall_at_k")
                            })
                            selected_job_details.download_button("Download result", json.dumps(res, indent=2), file_name=f"ann_eval_{jid}.json", mime="application/json")
                        except Exception as e:
                            selected_job_details.warning(f"Failed to fetch result: {e}")

                    # Show log
                    try:
                        log_resp = requests.get(f"{API_BASE}/admin/ann_eval/{jid}/log", timeout=10).json()
                        selected_job_details.markdown("**Job log (tail)**")
                        selected_job_details.code(log_resp.get("log",""), language="text")
                    except Exception as e:
                        selected_job_details.warning(f"Could not fetch log: {e}")

        with cols[1]:
            st.write(j.get("status"))
        with cols[2]:
            st.write(j.get("started_at") or "-")
        with cols[3]:
            st.write(j.get("finished_at") or "-")
        with cols[4]:
            if j.get("status") == "succeeded":
                st.success("ready")
            elif j.get("status") == "failed":
                st.error("failed")
            else:
                st.info(j.get("status"))
        with cols[5]:
            # Refresh button
            if st.button("Refresh", key=f"r_{jid}"):
                try:
                    import requests
                    job_d = requests.get(f"{API_BASE}/admin/ann_eval/{jid}", timeout=10).json()
                    st.experimental_set_query_params()  # no-op to force rerun in some versions; harmless fallback
                    st.success(f"Refreshed {jid}: {job_d.get('status')}")
                except Exception as e:
                    st.warning(f"Refresh failed: {e}")
            # View result
            if st.button("View result", key=f"res_{jid}"):
                try:
                    import requests
                    if j.get("status") != "succeeded":
                        st.warning("Result not ready yet.")
                    else:
                        res = requests.get(f"{API_BASE}/admin/ann_eval/{jid}/result", timeout=30).json()
                        st.write(res.get("recall_at_k"), res.get("avg_latency_ms"))
                        st.download_button("Download result", json.dumps(res, indent=2), file_name=f"ann_eval_{jid}.json", mime="application/json")
                except Exception as e:
                    st.warning(f"Failed fetching result: {e}")
            # View log
            if st.button("View log", key=f"log_{jid}"):
                try:
                    import requests
                    log_resp = requests.get(f"{API_BASE}/admin/ann_eval/{jid}/log", timeout=10).json()
                    st.code(log_resp.get("log",""), language="text")
                except Exception as e:
                    st.warning(f"Failed fetching log: {e}")

# small helper to show last job quickly
if "last_ann_job" in st.session_state:
    st.markdown("---")
    st.write(f"Last submitted job: **{st.session_state['last_ann_job']}**")
    if st.button("Open last job details"):
        jid = st.session_state["last_ann_job"]
        try:
            import requests
            job_d = requests.get(f"{API_BASE}/admin/ann_eval/{jid}", timeout=10).json()
            st.json(job_d)
            if job_d.get("status") == "succeeded":
                res = requests.get(f"{API_BASE}/admin/ann_eval/{jid}/result", timeout=30).json()
                st.download_button("Download result", json.dumps(res, indent=2), file_name=f"ann_eval_{jid}.json", mime="application/json")
        except Exception as e:
            st.warning(f"Failed: {e}")
