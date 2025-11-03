# APP_WORKFLOW.md

## Purpose
This document describes the Milan RAG app high-level architecture, scaled execution plan and conventions for artifacts and jobs. It is intended for developers and operators to understand where artifacts live, how jobs are executed and tracked, and how to run migrations and heavy operations safely.

---

## 1. Architecture & responsibilities

- **Streamlit UI** (`ui/`)  
  - Admin, ingestion, failure inspector, tasks management, revamp checklist.  
  - Triggers ingest / eval / rerank jobs via the API admin endpoints (future).  
  - Hosts lightweight utilities and debug panels.

- **API (retrieval_api.py / FastAPI)**  
  - Provides ingestion endpoints, query endpoints, connectors, diagnostics.  
  - Hosts admin endpoints to create/list jobs (`/admin/jobs`) and attaches job outputs to tasks.  
  - Responsible for DB access, MCP assembly, and audit logging.

- **Storage (Postgres + pgvector)**  
  - Stores `documents`, `chunks` and `ingest_jobs`.  
  - Vector embeddings stored in `embedding_vector` (vector(384)).  
  - FTS via `chunk_tsv` GIN index, ANN via HNSW/IVF indexes.

- **Workers / Jobs** (prototype/production)  
  - Prototype: FastAPI `BackgroundTask` runner (dev).  
  - Production: Dedicated worker pool (RQ/Celery) that executes ingest/eval jobs reliably.

- **Artifacts & Logs**  
  - Job artifacts and evaluation outputs stored under `/data/jobs/<job_uuid>/`.  
  - Logs under `/logs/jobs/<job_uuid>.log`.

---

## 2. Job lifecycle (recommended)
1. **Create**: UI posts `POST /admin/jobs` with `name`, `script`, `args`. API inserts `ingest_jobs` row with `status=pending` and `log_path`, `artifact_dir` set.  
2. **Start**: Job runner picks up the job or FastAPI background task starts process. `status=running`, `started_at` set.  
3. **Run**: Subprocess executes script, writes stdout/stderr to `log_path`. Script writes outputs to `artifact_dir`.  
4. **Finish**: Job exits; runner sets `status=succeeded|failed`, `exit_code`, `finished_at`, and reads `artifact_dir/summary.json` into `result` JSON column.  
5. **Attach**: UI may attach job `result` to `tasks.json` (task result) for audit and stakeholder reporting.

**Artifact conventions**: `artifact_dir/summary.json` must contain top-level keys for reporting (e.g., `num_queries`, `top_k`, `recall_at_k`, `avg_latency_ms`).

---

## 3. Naming conventions & folders

### Data & logs (canonical):
- `/data/jobs/<job_uuid>/summary.json` — job summary
- `/data/jobs/<job_uuid>/ann_eval.json` — ANN eval details
- `/data/jobs/<job_uuid>/fusion_eval.json`
- `/data/ground_truth/*.json` — ground truth files
- `/data/eval/*.json` — evaluation artifacts
- `/data/exports/*.csv` — stakeholder exports
- `/logs/jobs/<job_uuid>.log` — job logs

### Job UUID:
- Always use UUIDv4 string (e.g., `5fa2bd7e-...`) for artifact and log directories.
- Keep artifacts and logs per job in single directories to simplify cleanup.

---

## 4. Migrations & schema changes
- Put all SQL migrations into `/migrations/` with numeric prefixes (001_..., 002_...).  
- Test migrations on a local copy of DB before applying to dev.  
- Keep migration idempotent where possible. For destructive ops (drop columns), create a backout plan.

---

## 5. Security & admin
- Admin endpoints protected by `ADMIN_TOKEN` environment variable; header `x-admin-token` required.  
- Admin endpoints only available locally by default or behind secure network.  
- Secrets stored in `.env` locally; plan to move to Vault or cloud secrets for production.

---

## 6. Development & release workflow
- Active development on `revamp/organize-work`. Merge to `revamp/plan` for plan-level review.  
- For larger changes (reorgs, archive moves, job runner), open PRs from `revamp/organize-work` → `revamp/plan` and then `revamp/plan` → `main`.  
- Keep `revamp/archive/YYYYMMDD` in PR for auditable archival. After finalization, merge to `main`.

---

## 7. Backups & production notes
- Back up Postgres DB regularly.
- For large vector indexes, schedule index rebuilds and monitor memory use; use separate node for vector heavy loads if needed.

---

## 8. Acceptance criteria for readiness (prototype → production)
- Prototype: DB + pgvector installed, ingestion idempotent, Streamlit ingest flows, basic job runner working locally.  
- Production: Secure admin endpoints, async ingestion workers, monitoring & metrics, secrets management, backups, and QA tested migrations.

