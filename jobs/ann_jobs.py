#!/usr/bin/env python3
# jobs/ann_jobs.py

import os
import json
import uuid
import datetime
from typing import Optional, Dict, Any, List

# Directories for jobs + results; can be overridden via env
JOBS_DIR = os.environ.get("ANN_JOBS_DIR", "data/ann_jobs")
RESULTS_DIR = os.environ.get("ANN_RESULTS_DIR", "data/ann_eval")
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def _job_path(job_id: str) -> str:
    return os.path.join(JOBS_DIR, f"{job_id}.json")

def _result_path(job_id: str) -> str:
    return os.path.join(RESULTS_DIR, f"{job_id}.json")

def now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

def create_job(params: Dict[str, Any]) -> str:
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "status": "queued",
        "params": params,
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "result_path": None,
        "log_path": None
    }
    with open(_job_path(job_id), "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    return job_id

def update_job(job_id: str, **fields) -> Optional[Dict[str, Any]]:
    p = _job_path(job_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        job = json.load(fh)
    job.update(fields)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    return job

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = _job_path(job_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)

def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    jobs = []
    # sort newest first by filename (which contains uuid only, but file mtime order works)
    entries = sorted(
        [os.path.join(JOBS_DIR, f) for f in os.listdir(JOBS_DIR) if f.endswith(".json")],
        key=lambda x: os.path.getmtime(x), reverse=True
    )
    for p in entries[:limit]:
        with open(p, "r", encoding="utf-8") as fh:
            try:
                jobs.append(json.load(fh))
            except Exception:
                # ignore malformed
                continue
    return jobs

def result_path(job_id: str) -> str:
    return _result_path(job_id)

def save_result(job_id: str, result: Dict[str, Any]):
    out = _result_path(job_id)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    update_job(job_id, result_path=out, finished_at=now_iso(), status="succeeded")

def save_log(job_id: str, log_text: str):
    lp = os.path.join(JOBS_DIR, f"{job_id}.log")
    with open(lp, "w", encoding="utf-8") as fh:
        fh.write(log_text)
    update_job(job_id, log_path=lp)
