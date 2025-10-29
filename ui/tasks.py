# ui/tasks.py
import json
from pathlib import Path
from typing import List, Dict

TASKS_FILE = Path(__file__).resolve().parent.parent / "tasks.json"

def load_tasks() -> List[Dict]:
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)

def save_tasks(tasks: List[Dict]):
    with open(TASKS_FILE, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2)

def add_task(title: str, note: str = "", side_task: bool = True):
    tasks = load_tasks()
    tasks.append({"title": title, "note": note, "done": False, "side": side_task})
    save_tasks(tasks)

def set_done(idx: int, done: bool):
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks[idx]["done"] = done
    save_tasks(tasks)
