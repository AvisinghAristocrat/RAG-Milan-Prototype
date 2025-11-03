# README_DATA.md

This document describes the repository conventions for data and logs.

## Top-level folders
- `/data` — persistent artifacts and exports
  - `/data/jobs/<job_uuid>/` — job artifacts and outputs (summary.json, eval jsons). Use job_uuid to name folders.
  - `/data/ground_truth/` — ground truth files used by eval scripts.
  - `/data/eval/` — evaluation outputs (recall results, analysis).
  - `/data/exports/` — stakeholder exports (CSV/HTML/PDF).

- `/logs` — runtime logs
  - `/logs/jobs/<job_uuid>.log` — job logs from background jobs and long-running operations.
  - `/logs/migrations/` — optional migration logs.

- `/revamp/archive/<YYYYMMDD>/` — archival folder for files moved during the revamp (created only during reorg PRs).
  - Each archive must include a `backup_manifest.json` containing original file paths and commit hashes.

## Artifact: `summary.json` (recommended)
Each job should write `summary.json` to its artifact dir. Fields (recommended):
```json
{
  "job_uuid": "uuid",
  "name": "ann_eval",
  "num_queries": 50,
  "top_k": 10,
  "recall_at_k": 0.62,
  "avg_latency_ms": 111.16,
  "ef_search": 64,
  "notes": "Optional notes",
  "generated_at": "2025-10-30T12:00:00Z"
}
