# ui/pages/Failure_Inspector.py
import streamlit as st
import os
import sys
import pathlib
import json
import subprocess
import traceback
from datetime import datetime
from typing import List, Dict, Any

# ensure repo root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# load .env so DB_URL etc are available to Streamlit
from dotenv import load_dotenv
load_dotenv(dotenv_path=str(ROOT / ".env"))

# local imports
try:
    from embeddings.embed_adapter import EmbedAdapter
except Exception as e:
    st.error("Failed to import EmbedAdapter: " + str(e))
    raise

# DB
import psycopg
from psycopg.rows import dict_row

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/milan_rag")
DEFAULT_FUSION_DIR = ROOT / "tools"

st.set_page_config(page_title="Failure Inspector", layout="wide")
st.title("Failure Inspector — Fusion analysis")

st.markdown(
    """
Use this page to inspect failed queries from your fusion evaluation (ANN + FTS).
Workflow:
- Load a fusion analysis JSON (produced by `tools/eval_fusion.py` or `tools/fusion_analysis_*.json`).
- Select a failed query from the list to view details.
- Run per-chunk similarity for the expected document to see whether the query is semantically close to any chunk.
- Optionally re-chunk / re-embed / rerank from the UI (calls your CLI tools).
"""
)

# -------------------------
# Helpers
# -------------------------
def list_fusion_files(folder=DEFAULT_FUSION_DIR):
    if not folder.exists():
        return []
    return sorted([p for p in folder.glob("fusion*.json")] + [p for p in folder.glob("fusion*json")] + [p for p in folder.glob("fusion_eval_*.json")] + [p for p in folder.glob("fusion*")])

def load_fusion(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def connect_db():
    return psycopg.connect(DB_URL, row_factory=dict_row)

def normalize_vector(v):
    # handle vector types: list, memoryview, bytes, str(json)
    if v is None:
        return None
    if isinstance(v, memoryview):
        try:
            arr = list(v.tobytes())
            return arr
        except Exception:
            return None
    if isinstance(v, (bytes, bytearray)):
        try:
            return list(json.loads(v.decode("utf-8")))
        except Exception:
            return None
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return None
    # assume list of floats
    if isinstance(v, list) or isinstance(v, tuple):
        return list(v)
    return None

def compute_similarity_for_doc(query_text: str, doc_id: int, model_name: str = None, batch_size: int = 64):
    """
    Compute per-chunk embedding similarities between query and chunks of doc_id.
    Returns dict with per-chunk sims, max_sim, mean_sim, sample_chunks.
    """
    ea = EmbedAdapter(doc_model=(model_name or os.getenv("DOC_EMBED_MODEL", "all-MiniLM-L6-v2")))
    # embed query
    try:
        qvec = ea.embed_many([query_text], source="confluence", batch_size=batch_size)[0]
    except Exception as e:
        return {"error": f"query embed failed: {e}"}
    # fetch chunks and maybe stored embeddings
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, chunk_text, embedding_vector FROM chunks WHERE document_id = %s ORDER BY id", (doc_id,))
            rows = cur.fetchall()
    if not rows:
        return {"error": "no chunks for document", "num_chunks": 0}
    # try to use stored embeddings if available
    chunk_ids = [r["id"] for r in rows]
    chunk_texts = [r["chunk_text"] or "" for r in rows]
    stored_embeds = []
    for r in rows:
        emb = r.get("embedding_vector")
        stored = normalize_vector(emb)
        stored_embeds.append(stored)
    use_stored = all(e is not None for e in stored_embeds)
    if use_stored:
        # compute similarity with stored embeddings
        import numpy as np
        q = np.array(qvec, dtype=np.float32)
        b = np.array(stored_embeds, dtype=np.float32)
        denom = (np.linalg.norm(q) * np.linalg.norm(b, axis=1))
        denom[denom == 0] = 1e-12
        sims = (b.dot(q) / denom).tolist()
    else:
        # fallback: embed chunks and compute sims
        embeddings = []
        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i+batch_size]
            emb_batch = ea.embed_many(batch, source="confluence", batch_size=batch_size)
            embeddings.extend(emb_batch)
        import numpy as np
        q = np.array(qvec, dtype=np.float32)
        b = np.array(embeddings, dtype=np.float32)
        denom = (np.linalg.norm(q) * np.linalg.norm(b, axis=1))
        denom[denom == 0] = 1e-12
        sims = (b.dot(q) / denom).tolist()

    max_sim = max(sims) if sims else None
    mean_sim = sum(sims)/len(sims) if sims else None
    per_chunk = [{"chunk_id": cid, "sample": txt[:400], "sim": s} for cid, txt, s in zip(chunk_ids, chunk_texts, sims)]
    return {"num_chunks": len(chunk_ids), "max_sim": float(max_sim) if max_sim is not None else None, "mean_sim": float(mean_sim) if mean_sim is not None else None, "per_chunk": per_chunk}

def run_subprocess(cmd: List[str], timeout: int = 3600):
    """Run a subprocess capture output; return dict with returncode and output."""
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return {"rc": proc.returncode, "out": proc.stdout}
    except subprocess.TimeoutExpired as e:
        return {"rc": -1, "out": f"timed out: {e}"}
    except Exception as e:
        return {"rc": -2, "out": str(e)}

# -------------------------
# UI: load fusion analysis
# -------------------------
st.sidebar.header("Load Fusion Analysis")
files = list_fusion_files()
choice = st.sidebar.selectbox("Pick fusion analysis JSON (tools/ folder)", options=[str(p) for p in files] + ["Upload new..."])
fusion_data = None
if choice == "Upload new...":
    uploaded = st.sidebar.file_uploader("Upload fusion JSON", type="json")
    if uploaded:
        tmp = DEFAULT_FUSION_DIR
        tmp.mkdir(parents=True, exist_ok=True)
        fname = tmp / f"fusion_uploaded_{int(datetime.utcnow().timestamp())}.json"
        with open(fname, "wb") as fh:
            fh.write(uploaded.getbuffer())
        choice = str(fname)
        st.sidebar.success("Saved uploaded file: " + str(fname))
if choice and os.path.exists(choice):
    try:
        fusion_data = load_fusion(choice)
        st.sidebar.success(f"Loaded {choice}")
    except Exception as e:
        st.sidebar.error("Failed to load JSON: " + str(e))
        st.stop()
else:
    st.sidebar.info("No fusion analysis selected yet. Run fusion eval first.")

if fusion_data is None:
    st.info("Select a fusion analysis file from the sidebar to begin.")
    st.stop()

# show top summary
num_queries = fusion_data.get("num_queries", 0)
recall = fusion_data.get("recall_at_k", None)
k = fusion_data.get("top_k", None)
st.markdown(f"**Summary:** queries={num_queries}  |  recall@{k}={recall}")

# build failures list
failures = fusion_data.get("details") or fusion_data.get("failures") or fusion_data.get("details", [])
# Normalize: if original eval used "details", use that; if analyzer produced "failures", adapt
# The analyzer we used earlier produced .failures — adapt both:
if "failures" in fusion_data:
    failures = fusion_data["failures"]
elif "details" in fusion_data and isinstance(fusion_data["details"], list):
    # fusion eval had details and 'hit' flag; failures are details where hit==False
    failures = [d for d in fusion_data["details"] if not d.get("hit")]
else:
    # fallback
    failures = fusion_data.get("failures", [])

st.markdown(f"**Failures:** {len(failures)}")

# -------------------------
# Left column: failures list
# -------------------------
col_left, col_right = st.columns([1, 2])
with col_left:
    st.subheader("Failed queries")
    # prepare list entries: qid + expected doc(s)
    options = []
    for f in failures:
        qid = f.get("qid") or f.get("id") or "?"
        expected = f.get("expected") or f.get("expected_docs") or []
        # expected may be list of doc ids or list of dicts — normalize
        if expected and isinstance(expected[0], dict):
            exp_ids = [ed.get("doc_id") for ed in expected]
        else:
            exp_ids = expected
        label = f"{qid}  expected:{exp_ids}"
        options.append((label, f))
    selected_label = st.selectbox("Select a failure to inspect", options=[o[0] for o in options])
    sel_idx = [i for i, o in enumerate(options) if o[0] == selected_label][0]
    selected = options[sel_idx][1]

    st.markdown("**Actions**")
    if st.button("Run similarity for expected doc"):
        # compute similarity
        try:
            expected_info = selected.get("expected_docs_info") or [{"doc_id": d} for d in (selected.get("expected") or [])]
            # pick the first expected doc to analyze
            doc_info = expected_info[0]
            docid = doc_info.get("doc_id")
            query_text = selected.get("query") or selected.get("q", "")
            simres = compute_similarity_for_doc(query_text, int(docid))
            st.session_state["last_sim"] = simres
            st.success("Computed similarity (scroll right).")
        except Exception as e:
            st.error("Similarity failed: " + str(e))
            st.code(traceback.format_exc())

    if st.button("Re-chunk & Re-embed expected doc (rechunk_documents.py)"):
        expected_info = selected.get("expected_docs_info") or [{"doc_id": d} for d in (selected.get("expected") or [])]
        docid = expected_info[0].get("doc_id")
        # call tools/rechunk_documents.py --doc_ids <docid> --reembed True
        cmd = [sys.executable, str(ROOT / "tools" / "rechunk_documents.py"), "--doc_ids", str(docid), "--reembed", "True"]
        st.info("Launching re-chunk/re-embed job (background)...")
        res = run_subprocess(cmd, timeout=3600)
        if res["rc"] == 0:
            st.success("Rechunk/Reembed completed.")
            st.code(res["out"][:1000])
        else:
            st.warning("Rechunk/Reembed returned rc=" + str(res["rc"]))
            st.code(res["out"][:2000])

    if st.button("Rerank union (rerank_union.py)"):
        # write selected failure to a temporary fusion JSON for reranker
        tmp = ROOT / "tools" / f"rerank_input_{selected.get('qid')}.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        # Create a small fusion-like JSON with details for only this query
        fusion_small = {"num_queries": 1, "details": [selected]}
        tmp.write_text(json.dumps(fusion_small, indent=2), encoding="utf-8")
        cmd = [sys.executable, str(ROOT / "tools" / "rerank_union.py"), "--fusion", str(tmp), "--out", str(tmp.parent / f"rerank_out_{selected.get('qid')}.json")]
        st.info("Running reranker (this may take a while)...")
        res = run_subprocess(cmd, timeout=3600)
        st.code(res["out"][:2000])
        if res["rc"] == 0:
            st.success("Rerank completed; check tools/ for rerank output")

with col_right:
    st.subheader("Failure detail")
    st.write("**Query ID:**", selected.get("qid"))
    st.write("**Query text:**")
    st.code(selected.get("query") or selected.get("q") or "")
    st.write("**ANN (sample):**", selected.get("ann_docs") or selected.get("ann") or [])
    st.write("**FTS (sample):**", selected.get("fts_docs") or selected.get("fts") or [])
    st.write("**Union top_k:**", selected.get("union_top_k") or [])
    st.write("**Expected docs info:**")
    eds = selected.get("expected_docs_info") or []
    if not eds:
        # normalize old format
        eds = [{"doc_id": d} for d in (selected.get("expected") or [])]
    for ed in eds:
        st.markdown(f"**Doc {ed.get('doc_id')} — {ed.get('title','(no title)')}**")
        st.write("Exists:", ed.get("exists"), " Num chunks:", ed.get("num_chunks") or (len(ed.get("chunks") or [])))
        if ed.get("chunks"):
            for c in ed.get("chunks"):
                st.code(f"chunk_id {c['id']} : {c['sample'][:400]}")
    # similarity result from session_state
    last_sim = st.session_state.get("last_sim")
    if last_sim:
        st.subheader("Similarity results (last run)")
        if last_sim.get("error"):
            st.error(last_sim["error"])
        else:
            st.write("num_chunks:", last_sim["num_chunks"])
            st.write("max_sim:", last_sim["max_sim"])
            st.write("mean_sim:", last_sim["mean_sim"])
            # display the per chunk sims in a table
            sims = last_sim.get("per_chunk", [])
            rows = []
            for p in sims:
                rows.append({"chunk_id": p["chunk_id"], "sim": p["sim"], "sample": p["sample"][:200]})
            st.dataframe(rows)
            # Provide copyable JSON & download
            out_json = json.dumps(last_sim, indent=2)
            st.download_button("Download similarity JSON", data=out_json, file_name=f"sim_{selected.get('qid')}.json", mime="application/json")
            st.text_area("Copy similarity JSON", out_json, height=250)

    st.markdown("---")
    st.write("**Raw failure JSON (click to copy)**")
    st.text_area("Failure JSON", json.dumps(selected, indent=2), height=300)

st.markdown("**Notes**: Re-chunk & Re-embed will call your `tools/rechunk_documents.py` script. Rerank will call `tools/rerank_union.py`. Ensure those scripts support the command-line flags used above.")
