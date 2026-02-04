# ui/pages/Document_Inspector.py
import streamlit as st, os, sys, pathlib, json
from dotenv import load_dotenv
load_dotenv()

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

st.set_page_config(page_title="Document Inspector", layout="wide")
st.title("Document Inspector")

st.markdown("Enter a document id to inspect its metadata and chunks (including title chunk & has_vector).")

doc_id = st.number_input("Document ID", min_value=0, value=0, step=1)
token = st.text_input("Admin token (optional)", value=ADMIN_TOKEN, type="password")

if st.button("Inspect Document"):
    if not doc_id:
        st.warning("Enter a document id")
    else:
        try:
            import requests
            r = requests.get(f"{API_BASE}/admin/document/{doc_id}?token={token}", timeout=10)
            if r.status_code != 200:
                st.error(r.text)
            else:
                payload = r.json()
                st.subheader("Document")
                st.json(payload.get("document"))
                st.subheader("Chunks (meta & has_vector)")
                for c in payload.get("chunks", []):
                    st.markdown(f"**Chunk id**: {c.get('id')} — has_vector: {c.get('has_vector')}")
                    st.write("meta:", c.get("meta"))
                    st.code(c.get("sample",""), language="text")
        except Exception as e:
            st.error(f"Failed to fetch document: {e}")
