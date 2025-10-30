# ui/pages/Tasks_Manager.py
import streamlit as st
import json
import pathlib, sys, os
import streamlit.components.v1 as components
import hashlib
import io, csv
from copy import deepcopy

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Try to use ui.tasks helpers if available; fallback to direct file I/O
try:
    from ui.tasks import load_tasks, save_tasks
except Exception:
    TASKS_FILE = ROOT / "tasks.json"
    def load_tasks():
        if TASKS_FILE.exists():
            return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        return []
    def save_tasks(t):
        TASKS_FILE.write_text(json.dumps(t, indent=2), encoding="utf-8")

st.set_page_config(page_title="Tasks Manager", layout="wide")
st.title("Tasks Manager")

# -------------------------
# Utilities
# -------------------------
def safe_rerun():
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            components.html("<script>window.location.reload()</script>")
            st.stop()
    except Exception:
        components.html("<script>window.location.reload()</script>")
        st.stop()

def uid_for(i, t):
    return hashlib.md5(f"{i}-{t.get('title','')}".encode()).hexdigest()[:8]

def load_or_empty():
    t = load_tasks()
    if t is None:
        return []
    return t

def save_and_reload(tasks):
    save_tasks(tasks)
    safe_rerun()

def is_done(task):
    if isinstance(task.get("done"), bool):
        return task["done"]
    status = str(task.get("status") or "").lower()
    return status in ("done", "completed", "finished", "true")

def set_done_flag(task, val: bool):
    task["done"] = bool(val)
    task["status"] = "done" if val else "todo"

# -------------------------
# Load tasks
# -------------------------
tasks = load_or_empty()

# Sidebar (minimal & consistent)
st.sidebar.header("Tasks Manager")
st.sidebar.markdown(
    "Three views:\n\n"
    "- **All Tasks** — read-only listing (no status), search and view details (Export CSV).\n"
    "- **Completed** — editable completed tasks (mark undone if required).\n"
    "- **Next** — editable planning board for the next sprint (non-side, not completed).\n\n"
    "Use Save in each tab to persist edits to `tasks.json`."
)

total = len(tasks)
completed_cnt = sum(1 for t in tasks if is_done(t))
next_cnt = sum(1 for t in tasks if (not is_done(t)) and (not t.get("side", False)))
side_cnt = sum(1 for t in tasks if t.get("side", False))
st.sidebar.markdown(f"**Stats**\n\nTotal: {total}\n\nCompleted: {completed_cnt}\n\nNext: {next_cnt}\n\nSide: {side_cnt}")

if st.sidebar.button("Reload view"):
    safe_rerun()
if st.sidebar.button("Download tasks.json"):
    st.sidebar.download_button("Download", data=json.dumps(tasks, indent=2), file_name="tasks.json", mime="application/json")

# -------------------------
# Tabs: All | Completed | Next
# -------------------------
tab_all, tab_done, tab_next = st.tabs(["All Tasks", "Completed", "Next tasks"])

# ---------- All Tasks (read-only, search, CSV export) ----------
with tab_all:
    st.header("All Tasks (read-only)")
    st.markdown("This is a plain listing of every task (no status column). Use the search box to filter title or description.")
    q = st.text_input("Search (title or note)", value="", help="Type a substring to filter tasks by title or note.")
    shown = []
    for i, t in enumerate(tasks):
        title = t.get("title","")
        note = t.get("note","")
        if q:
            if q.lower() not in title.lower() and q.lower() not in note.lower():
                continue
        shown.append((i,t))

    st.markdown("### Export")
    if st.button("Export visible tasks to CSV"):
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(["index","title","note","priority","status","side","subtask_count","subtasks"])
        for idx, task in shown:
            subs = task.get("subtasks", [])
            subs_text = " || ".join([f"{'x' if s.get('done') else ' '}: {s.get('title')}" for s in subs])
            writer.writerow([
                idx,
                task.get("title",""),
                task.get("note",""),
                task.get("priority",""),
                "done" if is_done(task) else "todo",
                str(bool(task.get("side", False))),
                len(subs),
                subs_text
            ])
        st.download_button("Download CSV", data=si.getvalue(), file_name="tasks_all_export.csv", mime="text/csv")

    if not shown:
        st.info("No tasks to show (or none match the filter).")
    else:
        for idx, task in shown:
            with st.expander(f"{task.get('title')}", expanded=False):
                st.text_area("Description", value=task.get("note",""), height=140, disabled=True, key=f"all_note_{uid_for(idx,task)}")
                subs = task.get("subtasks", [])
                if subs:
                    st.write("**Subtasks**")
                    for s in subs:
                        st.write(f"- [{'x' if s.get('done') else ' '}] {s.get('title')}")
                else:
                    st.info("No subtasks.")

# ---------- Completed (editable) ----------
with tab_done:
    st.header("Completed tasks (editable)")
    completed_idxs = [i for i,t in enumerate(tasks) if is_done(t)]
    if not completed_idxs:
        st.info("No completed tasks.")
    else:
        st.write("Edit completed tasks inline. Press **Save changes (Completed)** to persist edits.")
        if st.button("Save changes (Completed)"):
            for i in completed_idxs:
                t = tasks[i]
                uid = uid_for(i, t)
                t["title"] = st.session_state.get(f"title_{uid}", t.get("title"))
                t["priority"] = st.session_state.get(f"prio_{uid}", t.get("priority","medium"))
                t["note"] = st.session_state.get(f"note_{uid}", t.get("note",""))
                new_subs = []
                for si, s in enumerate(t.get("subtasks", [])):
                    sd = st.session_state.get(f"subdone_{uid}_{si}", s.get("done", False))
                    stitle = st.session_state.get(f"subtitle_{uid}_{si}", s.get("title",""))
                    new_subs.append({"title": stitle, "done": sd})
                t["subtasks"] = new_subs
                set_done_flag(t, True)
            save_and_reload(tasks)

        for i in completed_idxs:
            t = tasks[i]
            uid = uid_for(i,t)
            cols = st.columns([0.04, 3.6, 1.0])
            cols[0].write("")
            cols[1].text_input("Title", value=t.get("title",""), key=f"title_{uid}")
            cols[2].selectbox("Priority", ["low","medium","high"],
                              index=["low","medium","high"].index(t.get("priority","medium")),
                              key=f"prio_{uid}")
            with st.expander("Details & Subtasks", expanded=False):
                st.text_area("Note", value=t.get("note",""), key=f"note_{uid}", height=140)
                subs = t.get("subtasks", [])
                if subs:
                    for si, s in enumerate(subs):
                        scols = st.columns([0.05, 0.85, 0.1])
                        scols[0].checkbox("", value=s.get("done", False), key=f"subdone_{uid}_{si}")
                        scols[1].text_input("", value=s.get("title",""), key=f"subtitle_{uid}_{si}")
                else:
                    st.info("No subtasks.")
        st.markdown("---")
        st.subheader("Completed task actions")
        sel = st.selectbox("Choose completed task index", options=completed_idxs,
                           format_func=lambda x: f"{x} - {tasks[x]['title'][:70]}")
        if sel is not None:
            sel_t = tasks[sel]
            s_uid = uid_for(sel, sel_t)
            c1, c2, c3 = st.columns([1,1,1])
            if c1.button("Mark Undone", key=f"mark_undone_{s_uid}"):
                set_done_flag(tasks[sel], False)
                save_and_reload(tasks)
            if c2.button("Download JSON", key=f"download_done_{s_uid}"):
                st.download_button("Download", data=json.dumps(sel_t, indent=2), file_name=f"completed_task_{sel}.json", mime="application/json")
            if c3.button("Delete task", key=f"delete_done_{s_uid}"):
                tasks.pop(sel)
                save_and_reload(tasks)

# ---------- Next tasks (editable, with confirmation before auto-mark) ----------
with tab_next:
    st.header("Next tasks (editable)")
    next_idxs = [i for i,t in enumerate(tasks) if (not is_done(t)) and (not t.get("side", False))]
    if not next_idxs:
        st.info("No next tasks.")
    else:
        st.write("Edit notes and subtasks inline, then press **Save changes (Next)**. If all subtasks are checked, the task will be a candidate to be auto-marked Done — you will be asked to confirm.")
        pending_key = "pending_next_edits"

        # Build pending edits when Save is clicked; store in session_state for confirmation step.
        if st.button("Save changes (Next)"):
            # Build a deep copy of tasks and apply edits from session_state into pending_tasks
            pending_tasks = deepcopy(tasks)
            for i in next_idxs:
                t = pending_tasks[i]
                uid = uid_for(i, t)
                # apply fields from session_state (fallback to current)
                t["title"] = st.session_state.get(f"title_{uid}", t.get("title"))
                t["note"] = st.session_state.get(f"note_{uid}", t.get("note",""))
                t["priority"] = st.session_state.get(f"prio_{uid}", t.get("priority","medium"))
                new_subs = []
                for si, s in enumerate(t.get("subtasks", [])):
                    sd = st.session_state.get(f"subdone_{uid}_{si}", s.get("done", False))
                    stitle = st.session_state.get(f"subtitle_{uid}_{si}", s.get("title",""))
                    new_subs.append({"title": stitle, "done": sd})
                t["subtasks"] = new_subs
            # store pending in session_state
            st.session_state[pending_key] = pending_tasks
            safe_rerun()

        # If pending edits exist, show confirmation panel
        if st.session_state.get("pending_next_edits"):
            pending_tasks = st.session_state["pending_next_edits"]
            # detect candidates: next tasks with subtasks and all subtasks True, and currently not done
            auto_candidates = []
            for i in next_idxs:
                old_task = tasks[i]
                new_task = pending_tasks[i]
                subs = new_task.get("subtasks", [])
                if len(subs) > 0 and all(s.get("done", False) for s in subs) and not is_done(old_task):
                    auto_candidates.append((i, new_task["title"]))

            st.markdown("### Auto-mark confirmation")
            if auto_candidates:
                st.warning("The following tasks have all subtasks checked and are candidates to be auto-marked Done. Confirm whether you want them to be marked Done when saving.")
                for idx, title in auto_candidates:
                    st.write(f"- {idx}: {title}")
                c1, c2, c3 = st.columns([1,1,1])
                if c1.button("Confirm auto-mark and save"):
                    # Apply pending tasks, auto-mark candidates
                    for i in next_idxs:
                        tasks[i] = pending_tasks[i]
                        # if candidate -> mark done, else mark false (unless it was already done)
                        if any(i == cand[0] for cand in auto_candidates):
                            set_done_flag(tasks[i], True)
                        else:
                            set_done_flag(tasks[i], False)
                    # cleanup and save
                    del st.session_state["pending_next_edits"]
                    save_and_reload(tasks)

                if c2.button("Save without auto-mark"):
                    # Apply pending tasks but don't mark candidates done
                    for i in next_idxs:
                        tasks[i] = pending_tasks[i]
                        set_done_flag(tasks[i], False)
                    del st.session_state["pending_next_edits"]
                    save_and_reload(tasks)

                if c3.button("Cancel"):
                    # discard pending and reload view
                    del st.session_state["pending_next_edits"]
                    st.info("Cancelled pending changes.")
                    safe_rerun()
            else:
                # No auto candidates; just show preview and confirm save
                st.info("No tasks would be auto-marked. Confirm saving the pending edits.")
                c_yes, c_no = st.columns([1,1])
                if c_yes.button("Save pending edits"):
                    for i in next_idxs:
                        tasks[i] = pending_tasks[i]
                        # Mark done only if all subs present and all True
                        subs = tasks[i].get("subtasks", [])
                        if len(subs) > 0 and all(s.get("done", False) for s in subs):
                            set_done_flag(tasks[i], True)
                        else:
                            set_done_flag(tasks[i], False)
                    del st.session_state["pending_next_edits"]
                    save_and_reload(tasks)
                if c_no.button("Cancel"):
                    del st.session_state["pending_next_edits"]
                    st.info("Cancelled pending changes.")
                    safe_rerun()

        # Render current editable rows (so user can continue editing)
        for i in next_idxs:
            t = tasks[i]
            uid = uid_for(i, t)
            cols = st.columns([0.04, 3.6, 1.0])
            cols[0].write("")
            cols[1].text_input("Title", value=t.get("title",""), key=f"title_{uid}")
            cols[2].selectbox("Priority", ["low","medium","high"],
                              index=["low","medium","high"].index(t.get("priority","medium")),
                              key=f"prio_{uid}")
            with st.expander("Details & Subtasks", expanded=False):
                st.text_area("Note", value=t.get("note",""), key=f"note_{uid}", height=140)
                subs = t.get("subtasks", [])
                if subs:
                    for si, s in enumerate(subs):
                        scols = st.columns([0.05, 0.85, 0.1])
                        scols[0].checkbox("", value=s.get("done", False), key=f"subdone_{uid}_{si}")
                        scols[1].text_input("", value=s.get("title",""), key=f"subtitle_{uid}_{si}")
                else:
                    st.info("No subtasks.")
        st.markdown("---")
        st.subheader("Next tasks actions")
        chosen = st.multiselect("Pick tasks (indexes) for bulk operation", options=next_idxs,
                                format_func=lambda x: f"{x} - {tasks[x]['title'][:50]}")
        b1, b2, b3 = st.columns(3)
        if b1.button("Mark selected Done"):
            for idx in chosen:
                set_done_flag(tasks[int(idx)], True)
            save_and_reload(tasks)
        if b2.button("Delete selected"):
            for idx in sorted([int(x) for x in chosen], reverse=True):
                tasks.pop(int(idx))
            save_and_reload(tasks)
        if b3.button("Download selected JSON"):
            rows = [tasks[int(x)] for x in chosen]
            st.download_button("Download", data=json.dumps(rows, indent=2), file_name="next_selected_tasks.json", mime="application/json")
