# ui/tasks.py
import json
from pathlib import Path
from typing import List, Dict, Any

TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks.json"

def _ensure_file():
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")

def load_tasks() -> List[Dict[str, Any]]:
    """
    Load tasks from tasks.json. Returns a list of task dicts.
    Each task is:
      {
        "title": str,
        "note": str,
        "done": bool,
        "side": bool,
        "result": optional dict
      }
    """
    _ensure_file()
    with open(TASKS_FILE, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
            if not isinstance(data, list):
                return []
            return data
        except Exception:
            return []

def save_tasks(tasks: List[Dict[str, Any]]):
    _ensure_file()
    with open(TASKS_FILE, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2, ensure_ascii=False)

def add_task(title: str, note: str = "", side_task: bool = True, result: Dict[str, Any] = None):
    """
    Add a new task. Optional `result` can contain JSON/dict with check output or job result.
    """
    tasks = load_tasks()
    tasks.append({
        "title": title,
        "note": note,
        "done": False,
        "side": side_task,
        "result": result
    })
    save_tasks(tasks)

def set_done(idx: int, done: bool):
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks[idx]["done"] = done
        save_tasks(tasks)

def add_result(idx: int, result: Dict[str, Any]):
    """
    Attach a result JSON to the task at index `idx`.
    """
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks[idx]["result"] = result
        save_tasks(tasks)

def update_task(idx: int, title: str = None, note: str = None, side: bool = None, done: bool = None, result: Dict[str, Any] = None):
    """
    Update fields for a task at `idx`. Only non-None args are applied.
    """
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        t = tasks[idx]
        if title is not None: t["title"] = title
        if note is not None: t["note"] = note
        if side is not None: t["side"] = side
        if done is not None: t["done"] = done
        if result is not None: t["result"] = result
        save_tasks(tasks)

def delete_task(idx: int):
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks.pop(idx)
        save_tasks(tasks)
