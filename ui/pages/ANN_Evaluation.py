# pages/ANN_Evaluation.py
"""
ANN Evaluation (Streamlit Page)

This page lets you:
- generate a ground-truth sample from DB, or upload an existing ground-truth JSON,
- run ANN evaluation (recall@K and latency) by calling the local eval_ann tool,
- display the evaluation summary + details, and
- create a Task in the UI with the evaluation result.
"""

import streamlit as st
import sys, pathlib, os, json
from datetime import datetime
import traceback
from dotenv import load_dotenv
load_dotenv()

# Ensure repo root is importable
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Local imports (make sure these files exist: tools/eval_ann.py & tools/generate_ground_truth.py)
try:
    from tools.generate_ground_truth import sample_documents
    from tools.eval_ann import eval_ann
except Exception as e:
    st.error("Failed to import local tools: " + str(e))
    raise

# Tasks API
try:
    from ui.tasks import add_task
except Exception as e:
    st.error("Failed to import ui.tasks: " + str(e))
    raise

st.set_page_config(page_title="ANN Evaluation", layout="wide")
st.title("ANN Evaluation (Step 14)")

st.markdown(
    """
Use this page to run ANN recall/latency evaluation against your Postgres/pgvector index.

**Notes**
- Generate a ground-truth sample (simple auto-sampling of documents) or upload your human-labeled ground-truth JSON.
- The evaluation runs synchronously and can take time depending on num queries and model.
- Results are automatically attached to the Tasks list for traceability.
"""
)

with st.form("ann_eval_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        mode = st.selectbox("Ground-truth source", ["generate_sample", "upload_json"], index=0)
        if mode == "generate_sample":
            n = st.number_input("Number of sample queries", min_value=5, max_value=500, value=50)
            words = st.number_input("Words per query (sample)", min_value=5, max_value=200, value=20)
            seed = st.number_input("Random seed (optional)", value=0)
        else:
            uploaded = st.file_uploader("Upload ground_truth.json", type="json")
    with col2:
        top_k = st.number_input("Top-K (recall@K)", min_value=1, max_value=500, value=10)
        ef_search = st.number_input("ef_search (HNSW)", min_value=1, max_value=1024, value=64)
        model_doc = st.text_input("Doc embed model name", value=os.getenv("DOC_EMBED_MODEL","all-MiniLM-L6-v2"))
        batch_size = st.number_input("Embed batch size", min_value=1, max_value=512, value=64)

    submitted = st.form_submit_button("Run ANN Evaluation")

if submitted:
    # prepare queries
    queries_list = None
    queries_file = None
    if mode == "generate_sample":
        st.info("Generating sample queries from documents...")
        try:
            queries_list = sample_documents(os.getenv("DB_URL"), n=n, words=words, seed=int(seed) if seed else None)
            if not queries_list:
                st.error("No queries were generated from documents. Check that documents have canonical_text or titles.")
                st.stop()
                st.success(f"Generated {len(queries_list)} sample queries.")
        except Exception as e:
            st.error("Failed to generate sample queries: " + str(e))
            st.code(traceback.format_exc(), language="text")
            st.stop()

    else:
        if uploaded is None:
            st.error("Please upload a ground-truth JSON file")
            st.stop()
        tmp = ROOT / "tools" / f"uploaded_ground_truth_{int(datetime.utcnow().timestamp())}.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "wb") as fh:
            fh.write(uploaded.getbuffer())
        queries_file = str(tmp)
        st.success("Uploaded ground-truth saved to: " + str(tmp))

    # Run evaluation
    st.info("Running ANN evaluation (this runs in the app; it may take some time).")
    try:
        summary = eval_ann(os.getenv("DB_URL"), model_doc, queries_file if queries_file else queries_list,
                           top_k=top_k, ef_search=ef_search, batch_size=int(batch_size), out=None)
    except Exception as e:
        st.error("Evaluation failed: " + str(e))
        raise

    st.subheader("Evaluation Summary")
    st.write(f"Recall@{top_k}: **{summary.get('recall_at_k')}**")
    st.write(f"Avg latency (ms): **{summary.get('avg_latency_ms'):.2f}**")
    st.write(f"Num queries: **{summary.get('num_queries')}**")
    st.json({k: summary[k] for k in ("num_queries","top_k","ef_search","avg_latency_ms","recall_at_k")})

    # Show per-query details (collapsible)
    if st.checkbox("Show detailed per-query results"):
        st.subheader("Per-query results")
        for d in summary.get("details", []):
            with st.expander(f"{d['qid']} (hit={d['hit']}, {d['latency_ms']:.1f} ms)"):
                st.write("Query:", d["query"])
                st.write("Expected:", d["expected"])
                st.write("Returned (top docs):", d["returned"])

    # Save summary to file and add a Task entry
    out_dir = ROOT / "tools"
    out_dir.mkdir(parents=True, exist_ok=True)   # ensure directory exists
    out_name = out_dir / f"ann_eval_{int(datetime.utcnow().timestamp())}.json"
    with open(out_name, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    st.success("Saved evaluation to " + str(out_name))

    # Add task
    try:
        task_title = f"ANN Eval top{top_k} ef{ef_search} ({int(datetime.utcnow().timestamp())})"
        add_task(task_title, note=f"Model={model_doc}, queries={summary.get('num_queries')}, avg_latency_ms={summary.get('avg_latency_ms')}", side_task=False, result=summary)
        st.success("Evaluation added as a Task in the Tasks list.")
    except Exception as e:
        st.warning("Could not add Task automatically: " + str(e))
