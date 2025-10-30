# ui/pages/Revamp_Checklist.py
import streamlit as st
import json, pathlib, sys, os
from datetime import datetime
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

JSON_PATH = ROOT / "revamp_checklist.json"
MD_PATH = ROOT / "REVAMP_CHECKLIST.md"

st.set_page_config(page_title="Revamp Checklist", layout="wide")
st.title("Revamp Checklist (team)")

def load_checklist():
    if JSON_PATH.exists():
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    return []

def save_checklist(items):
    JSON_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    # regenerate md
    lines = ["# Revamp Checklist", "", "This document tracks the high-level project revamp items.", "", "| # | Item | Description | Status | Notes |", "|---|------|-------------|--------|-------|"]
    for it in items:
        lines.append(f"| {it['id']} | {it['item']} | {it['description']} | {it['status']} | {it.get('notes','')} |")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    st.success("Saved checklist and updated REVAMP_CHECKLIST.md")

items = load_checklist()
if not items:
    st.info("No revamp items found in revamp_checklist.json. Create the file in repo root or paste initial JSON.")
    st.stop()

# show stats
total = len(items)
done = sum(1 for i in items if i.get("status","")=="done")
st.sidebar.markdown(f"**Revamp Summary**\n\nTotal: {total}\n\nDone: {done}\n\nRemaining: {total-done}")

# editable table-like UI
for it in items:
    with st.container():
        st.markdown(f"### {it['id']}. {it['item']}")
        cols = st.columns([3,1,2])
        cols[0].write(it.get("description",""))
        status = cols[1].selectbox("Status", ["todo","in_progress","done"], index=["todo","in_progress","done"].index(it.get("status","todo")), key=f"status_{it['id']}")
        notes = cols[2].text_area("Notes", value=it.get("notes",""), key=f"notes_{it['id']}", height=80)
        it["status"] = status
        it["notes"] = notes
        st.markdown("---")

if st.button("Save changes"):
    save_checklist(items)
