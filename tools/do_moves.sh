#!/usr/bin/env bash
set -euo pipefail
echo "This script will execute the generated moves (git mv / mv / git add etc)."
echo "PLEASE REVIEW tools/do_moves.sh carefully before running."
echo
# --- generated on Sun Nov  9 13:55:47 IST 2025 ---

# --- root-level file moves ---

# Move: .DS_Store -> tools/.DS_Store
mkdir -p 'tools'
if git ls-files --error-unmatch '.DS_Store' >/dev/null 2>&1; then
  echo 'git mv -v ".DS_Store" "tools/.DS_Store"'
  git mv -v ".DS_Store" "tools/.DS_Store"
else
  if [ -f '.DS_Store' ]; then
    echo 'mv -v ".DS_Store" "tools/.DS_Store" && git add -A "tools/.DS_Store"'
    mv -v '.DS_Store' 'tools/.DS_Store'
    git add -A 'tools/.DS_Store'
  else
    echo "# SKIP: source '.DS_Store' not found"
  fi
fi

# Move: .env -> tools/.env
mkdir -p 'tools'
if git ls-files --error-unmatch '.env' >/dev/null 2>&1; then
  echo 'git mv -v ".env" "tools/.env"'
  git mv -v ".env" "tools/.env"
else
  if [ -f '.env' ]; then
    echo 'mv -v ".env" "tools/.env" && git add -A "tools/.env"'
    mv -v '.env' 'tools/.env'
    git add -A 'tools/.env'
  else
    echo "# SKIP: source '.env' not found"
  fi
fi

# Move: .env.bak -> tools/.env.bak
mkdir -p 'tools'
if git ls-files --error-unmatch '.env.bak' >/dev/null 2>&1; then
  echo 'git mv -v ".env.bak" "tools/.env.bak"'
  git mv -v ".env.bak" "tools/.env.bak"
else
  if [ -f '.env.bak' ]; then
    echo 'mv -v ".env.bak" "tools/.env.bak" && git add -A "tools/.env.bak"'
    mv -v '.env.bak' 'tools/.env.bak'
    git add -A 'tools/.env.bak'
  else
    echo "# SKIP: source '.env.bak' not found"
  fi
fi
# keep .gitignore

# Move: .gitignore.bak -> tools/.gitignore.bak
mkdir -p 'tools'
if git ls-files --error-unmatch '.gitignore.bak' >/dev/null 2>&1; then
  echo 'git mv -v ".gitignore.bak" "tools/.gitignore.bak"'
  git mv -v ".gitignore.bak" "tools/.gitignore.bak"
else
  if [ -f '.gitignore.bak' ]; then
    echo 'mv -v ".gitignore.bak" "tools/.gitignore.bak" && git add -A "tools/.gitignore.bak"'
    mv -v '.gitignore.bak' 'tools/.gitignore.bak'
    git add -A 'tools/.gitignore.bak'
  else
    echo "# SKIP: source '.gitignore.bak' not found"
  fi
fi
# keep .pre-commit-config.yaml
# keep .secrets.baseline

# Move: cleanup_candidates.json -> tools/reports/cleanup_candidates.json
mkdir -p 'tools/reports'
if git ls-files --error-unmatch 'cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json"'
  git mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json"
else
  if [ -f 'cleanup_candidates.json' ]; then
    echo 'mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json" && git add -A "tools/reports/cleanup_candidates.json"'
    mv -v 'cleanup_candidates.json' 'tools/reports/cleanup_candidates.json'
    git add -A 'tools/reports/cleanup_candidates.json'
  else
    echo "# SKIP: source 'cleanup_candidates.json' not found"
  fi
fi

# Move: cleanup_summary.txt -> tools/cleanup_summary.txt
mkdir -p 'tools'
if git ls-files --error-unmatch 'cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "cleanup_summary.txt" "tools/cleanup_summary.txt"'
  git mv -v "cleanup_summary.txt" "tools/cleanup_summary.txt"
else
  if [ -f 'cleanup_summary.txt' ]; then
    echo 'mv -v "cleanup_summary.txt" "tools/cleanup_summary.txt" && git add -A "tools/cleanup_summary.txt"'
    mv -v 'cleanup_summary.txt' 'tools/cleanup_summary.txt'
    git add -A 'tools/cleanup_summary.txt'
  else
    echo "# SKIP: source 'cleanup_summary.txt' not found"
  fi
fi

# Move: create_milan_repo.sh -> scripts/create_milan_repo.sh
mkdir -p 'scripts'
if git ls-files --error-unmatch 'create_milan_repo.sh' >/dev/null 2>&1; then
  echo 'git mv -v "create_milan_repo.sh" "scripts/create_milan_repo.sh"'
  git mv -v "create_milan_repo.sh" "scripts/create_milan_repo.sh"
else
  if [ -f 'create_milan_repo.sh' ]; then
    echo 'mv -v "create_milan_repo.sh" "scripts/create_milan_repo.sh" && git add -A "scripts/create_milan_repo.sh"'
    mv -v 'create_milan_repo.sh' 'scripts/create_milan_repo.sh'
    git add -A 'scripts/create_milan_repo.sh'
  else
    echo "# SKIP: source 'create_milan_repo.sh' not found"
  fi
fi

# Move: create-vector-attempt.log -> tools/create-vector-attempt.log
mkdir -p 'tools'
if git ls-files --error-unmatch 'create-vector-attempt.log' >/dev/null 2>&1; then
  echo 'git mv -v "create-vector-attempt.log" "tools/create-vector-attempt.log"'
  git mv -v "create-vector-attempt.log" "tools/create-vector-attempt.log"
else
  if [ -f 'create-vector-attempt.log' ]; then
    echo 'mv -v "create-vector-attempt.log" "tools/create-vector-attempt.log" && git add -A "tools/create-vector-attempt.log"'
    mv -v 'create-vector-attempt.log' 'tools/create-vector-attempt.log'
    git add -A 'tools/create-vector-attempt.log'
  else
    echo "# SKIP: source 'create-vector-attempt.log' not found"
  fi
fi

# Move: db-last-200.log -> tools/db-last-200.log
mkdir -p 'tools'
if git ls-files --error-unmatch 'db-last-200.log' >/dev/null 2>&1; then
  echo 'git mv -v "db-last-200.log" "tools/db-last-200.log"'
  git mv -v "db-last-200.log" "tools/db-last-200.log"
else
  if [ -f 'db-last-200.log' ]; then
    echo 'mv -v "db-last-200.log" "tools/db-last-200.log" && git add -A "tools/db-last-200.log"'
    mv -v 'db-last-200.log' 'tools/db-last-200.log'
    git add -A 'tools/db-last-200.log'
  else
    echo "# SKIP: source 'db-last-200.log' not found"
  fi
fi

# Move: docker-compose.yml -> tools/docker-compose.yml
mkdir -p 'tools'
if git ls-files --error-unmatch 'docker-compose.yml' >/dev/null 2>&1; then
  echo 'git mv -v "docker-compose.yml" "tools/docker-compose.yml"'
  git mv -v "docker-compose.yml" "tools/docker-compose.yml"
else
  if [ -f 'docker-compose.yml' ]; then
    echo 'mv -v "docker-compose.yml" "tools/docker-compose.yml" && git add -A "tools/docker-compose.yml"'
    mv -v 'docker-compose.yml' 'tools/docker-compose.yml'
    git add -A 'tools/docker-compose.yml'
  else
    echo "# SKIP: source 'docker-compose.yml' not found"
  fi
fi

# Move: docker-compose.yml.bak -> tools/docker-compose.yml.bak
mkdir -p 'tools'
if git ls-files --error-unmatch 'docker-compose.yml.bak' >/dev/null 2>&1; then
  echo 'git mv -v "docker-compose.yml.bak" "tools/docker-compose.yml.bak"'
  git mv -v "docker-compose.yml.bak" "tools/docker-compose.yml.bak"
else
  if [ -f 'docker-compose.yml.bak' ]; then
    echo 'mv -v "docker-compose.yml.bak" "tools/docker-compose.yml.bak" && git add -A "tools/docker-compose.yml.bak"'
    mv -v 'docker-compose.yml.bak' 'tools/docker-compose.yml.bak'
    git add -A 'tools/docker-compose.yml.bak'
  else
    echo "# SKIP: source 'docker-compose.yml.bak' not found"
  fi
fi

# Move: enhancements.json -> tools/enhancements.json
mkdir -p 'tools'
if git ls-files --error-unmatch 'enhancements.json' >/dev/null 2>&1; then
  echo 'git mv -v "enhancements.json" "tools/enhancements.json"'
  git mv -v "enhancements.json" "tools/enhancements.json"
else
  if [ -f 'enhancements.json' ]; then
    echo 'mv -v "enhancements.json" "tools/enhancements.json" && git add -A "tools/enhancements.json"'
    mv -v 'enhancements.json' 'tools/enhancements.json'
    git add -A 'tools/enhancements.json'
  else
    echo "# SKIP: source 'enhancements.json' not found"
  fi
fi

# Move: ignored_cleanup_candidates.json -> tools/reports/ignored_cleanup_candidates.json
mkdir -p 'tools/reports'
if git ls-files --error-unmatch 'ignored_cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json"'
  git mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json"
else
  if [ -f 'ignored_cleanup_candidates.json' ]; then
    echo 'mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json" && git add -A "tools/reports/ignored_cleanup_candidates.json"'
    mv -v 'ignored_cleanup_candidates.json' 'tools/reports/ignored_cleanup_candidates.json'
    git add -A 'tools/reports/ignored_cleanup_candidates.json'
  else
    echo "# SKIP: source 'ignored_cleanup_candidates.json' not found"
  fi
fi

# Move: ignored_cleanup_summary.txt -> tools/reports/ignored_cleanup_summary.txt
mkdir -p 'tools/reports'
if git ls-files --error-unmatch 'ignored_cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "ignored_cleanup_summary.txt" "tools/reports/ignored_cleanup_summary.txt"'
  git mv -v "ignored_cleanup_summary.txt" "tools/reports/ignored_cleanup_summary.txt"
else
  if [ -f 'ignored_cleanup_summary.txt' ]; then
    echo 'mv -v "ignored_cleanup_summary.txt" "tools/reports/ignored_cleanup_summary.txt" && git add -A "tools/reports/ignored_cleanup_summary.txt"'
    mv -v 'ignored_cleanup_summary.txt' 'tools/reports/ignored_cleanup_summary.txt'
    git add -A 'tools/reports/ignored_cleanup_summary.txt'
  else
    echo "# SKIP: source 'ignored_cleanup_summary.txt' not found"
  fi
fi

# Move: ingest_mdmig_full.log -> tools/ingest_mdmig_full.log
mkdir -p 'tools'
if git ls-files --error-unmatch 'ingest_mdmig_full.log' >/dev/null 2>&1; then
  echo 'git mv -v "ingest_mdmig_full.log" "tools/ingest_mdmig_full.log"'
  git mv -v "ingest_mdmig_full.log" "tools/ingest_mdmig_full.log"
else
  if [ -f 'ingest_mdmig_full.log' ]; then
    echo 'mv -v "ingest_mdmig_full.log" "tools/ingest_mdmig_full.log" && git add -A "tools/ingest_mdmig_full.log"'
    mv -v 'ingest_mdmig_full.log' 'tools/ingest_mdmig_full.log'
    git add -A 'tools/ingest_mdmig_full.log'
  else
    echo "# SKIP: source 'ingest_mdmig_full.log' not found"
  fi
fi

# Move: Makefile -> tools/Makefile
mkdir -p 'tools'
if git ls-files --error-unmatch 'Makefile' >/dev/null 2>&1; then
  echo 'git mv -v "Makefile" "tools/Makefile"'
  git mv -v "Makefile" "tools/Makefile"
else
  if [ -f 'Makefile' ]; then
    echo 'mv -v "Makefile" "tools/Makefile" && git add -A "tools/Makefile"'
    mv -v 'Makefile' 'tools/Makefile'
    git add -A 'tools/Makefile'
  else
    echo "# SKIP: source 'Makefile' not found"
  fi
fi

# Move: mcp_logs.jsonl -> tools/mcp_logs.jsonl
mkdir -p 'tools'
if git ls-files --error-unmatch 'mcp_logs.jsonl' >/dev/null 2>&1; then
  echo 'git mv -v "mcp_logs.jsonl" "tools/mcp_logs.jsonl"'
  git mv -v "mcp_logs.jsonl" "tools/mcp_logs.jsonl"
else
  if [ -f 'mcp_logs.jsonl' ]; then
    echo 'mv -v "mcp_logs.jsonl" "tools/mcp_logs.jsonl" && git add -A "tools/mcp_logs.jsonl"'
    mv -v 'mcp_logs.jsonl' 'tools/mcp_logs.jsonl'
    git add -A 'tools/mcp_logs.jsonl'
  else
    echo "# SKIP: source 'mcp_logs.jsonl' not found"
  fi
fi

# Move: pgvector-build.log -> tools/pgvector-build.log
mkdir -p 'tools'
if git ls-files --error-unmatch 'pgvector-build.log' >/dev/null 2>&1; then
  echo 'git mv -v "pgvector-build.log" "tools/pgvector-build.log"'
  git mv -v "pgvector-build.log" "tools/pgvector-build.log"
else
  if [ -f 'pgvector-build.log' ]; then
    echo 'mv -v "pgvector-build.log" "tools/pgvector-build.log" && git add -A "tools/pgvector-build.log"'
    mv -v 'pgvector-build.log' 'tools/pgvector-build.log'
    git add -A 'tools/pgvector-build.log'
  else
    echo "# SKIP: source 'pgvector-build.log' not found"
  fi
fi

# Move: requirements.txt -> tools/requirements.txt
mkdir -p 'tools'
if git ls-files --error-unmatch 'requirements.txt' >/dev/null 2>&1; then
  echo 'git mv -v "requirements.txt" "tools/requirements.txt"'
  git mv -v "requirements.txt" "tools/requirements.txt"
else
  if [ -f 'requirements.txt' ]; then
    echo 'mv -v "requirements.txt" "tools/requirements.txt" && git add -A "tools/requirements.txt"'
    mv -v 'requirements.txt' 'tools/requirements.txt'
    git add -A 'tools/requirements.txt'
  else
    echo "# SKIP: source 'requirements.txt' not found"
  fi
fi

# Move: retrieval_api.py -> tools/retrieval_api.py
mkdir -p 'tools'
if git ls-files --error-unmatch 'retrieval_api.py' >/dev/null 2>&1; then
  echo 'git mv -v "retrieval_api.py" "tools/retrieval_api.py"'
  git mv -v "retrieval_api.py" "tools/retrieval_api.py"
else
  if [ -f 'retrieval_api.py' ]; then
    echo 'mv -v "retrieval_api.py" "tools/retrieval_api.py" && git add -A "tools/retrieval_api.py"'
    mv -v 'retrieval_api.py' 'tools/retrieval_api.py'
    git add -A 'tools/retrieval_api.py'
  else
    echo "# SKIP: source 'retrieval_api.py' not found"
  fi
fi

# Move: revamp_checklist.json -> tools/revamp_checklist.json
mkdir -p 'tools'
if git ls-files --error-unmatch 'revamp_checklist.json' >/dev/null 2>&1; then
  echo 'git mv -v "revamp_checklist.json" "tools/revamp_checklist.json"'
  git mv -v "revamp_checklist.json" "tools/revamp_checklist.json"
else
  if [ -f 'revamp_checklist.json' ]; then
    echo 'mv -v "revamp_checklist.json" "tools/revamp_checklist.json" && git add -A "tools/revamp_checklist.json"'
    mv -v 'revamp_checklist.json' 'tools/revamp_checklist.json'
    git add -A 'tools/revamp_checklist.json'
  else
    echo "# SKIP: source 'revamp_checklist.json' not found"
  fi
fi

# Move: REVAMP_CHECKLIST.md -> tools/REVAMP_CHECKLIST.md
mkdir -p 'tools'
if git ls-files --error-unmatch 'REVAMP_CHECKLIST.md' >/dev/null 2>&1; then
  echo 'git mv -v "REVAMP_CHECKLIST.md" "tools/REVAMP_CHECKLIST.md"'
  git mv -v "REVAMP_CHECKLIST.md" "tools/REVAMP_CHECKLIST.md"
else
  if [ -f 'REVAMP_CHECKLIST.md' ]; then
    echo 'mv -v "REVAMP_CHECKLIST.md" "tools/REVAMP_CHECKLIST.md" && git add -A "tools/REVAMP_CHECKLIST.md"'
    mv -v 'REVAMP_CHECKLIST.md' 'tools/REVAMP_CHECKLIST.md'
    git add -A 'tools/REVAMP_CHECKLIST.md'
  else
    echo "# SKIP: source 'REVAMP_CHECKLIST.md' not found"
  fi
fi

# Move: space. -> tools/space.
mkdir -p 'tools'
if git ls-files --error-unmatch 'space.' >/dev/null 2>&1; then
  echo 'git mv -v "space." "tools/space."'
  git mv -v "space." "tools/space."
else
  if [ -f 'space.' ]; then
    echo 'mv -v "space." "tools/space." && git add -A "tools/space."'
    mv -v 'space.' 'tools/space.'
    git add -A 'tools/space.'
  else
    echo "# SKIP: source 'space.' not found"
  fi
fi
# keep tasks.json

# Move: tasks.json.bak -> tools/tasks.json.bak
mkdir -p 'tools'
if git ls-files --error-unmatch 'tasks.json.bak' >/dev/null 2>&1; then
  echo 'git mv -v "tasks.json.bak" "tools/tasks.json.bak"'
  git mv -v "tasks.json.bak" "tools/tasks.json.bak"
else
  if [ -f 'tasks.json.bak' ]; then
    echo 'mv -v "tasks.json.bak" "tools/tasks.json.bak" && git add -A "tools/tasks.json.bak"'
    mv -v 'tasks.json.bak' 'tools/tasks.json.bak'
    git add -A 'tools/tasks.json.bak'
  else
    echo "# SKIP: source 'tasks.json.bak' not found"
  fi
fi

# Move: This -> tools/This
mkdir -p 'tools'
if git ls-files --error-unmatch 'This' >/dev/null 2>&1; then
  echo 'git mv -v "This" "tools/This"'
  git mv -v "This" "tools/This"
else
  if [ -f 'This' ]; then
    echo 'mv -v "This" "tools/This" && git add -A "tools/This"'
    mv -v 'This' 'tools/This'
    git add -A 'tools/This'
  else
    echo "# SKIP: source 'This' not found"
  fi
fi

# --- stray files deeper in tree (depth <= 3) ---
# NOTE: review .DS_Store (unhandled ext DS_Store) -- skip
# NOTE: review .env (unhandled ext env) -- skip
# NOTE: review .env.bak (unhandled ext bak) -- skip
# NOTE: review .git/COMMIT_EDITMSG (unhandled ext git/COMMIT_EDITMSG) -- skip
# NOTE: review .git/config (unhandled ext git/config) -- skip
# NOTE: review .git/FETCH_HEAD (unhandled ext git/FETCH_HEAD) -- skip
# NOTE: review .git/HEAD (unhandled ext git/HEAD) -- skip
# NOTE: review .git/hooks/pre-commit (unhandled ext git/hooks/pre-commit) -- skip
# NOTE: review .git/index (unhandled ext git/index) -- skip
# NOTE: review .git/info/refs (unhandled ext git/info/refs) -- skip
# NOTE: review .git/logs/HEAD (unhandled ext git/logs/HEAD) -- skip
# NOTE: review .git/ORIG_HEAD (unhandled ext git/ORIG_HEAD) -- skip
# NOTE: review .git/packed-refs (unhandled ext git/packed-refs) -- skip
# NOTE: review .git/sourcetreeconfig (unhandled ext git/sourcetreeconfig) -- skip
# NOTE: review .gitignore (unhandled ext gitignore) -- skip
# NOTE: review .gitignore.bak (unhandled ext bak) -- skip
# NOTE: review .pre-commit-config.yaml (unhandled ext yaml) -- skip
# NOTE: review .secrets.baseline (unhandled ext baseline) -- skip
# NOTE: review .venv/bin/activate (unhandled ext venv/bin/activate) -- skip
# NOTE: review .venv/bin/activate.csh (unhandled ext csh) -- skip
# NOTE: review .venv/bin/activate.fish (unhandled ext fish) -- skip

# Move: .venv/bin/Activate.ps1 -> tools/.venv/bin/Activate.ps1
mkdir -p 'tools/.venv/bin'
if git ls-files --error-unmatch '.venv/bin/Activate.ps1' >/dev/null 2>&1; then
  echo 'git mv -v ".venv/bin/Activate.ps1" "tools/.venv/bin/Activate.ps1"'
  git mv -v ".venv/bin/Activate.ps1" "tools/.venv/bin/Activate.ps1"
else
  if [ -f '.venv/bin/Activate.ps1' ]; then
    echo 'mv -v ".venv/bin/Activate.ps1" "tools/.venv/bin/Activate.ps1" && git add -A "tools/.venv/bin/Activate.ps1"'
    mv -v '.venv/bin/Activate.ps1' 'tools/.venv/bin/Activate.ps1'
    git add -A 'tools/.venv/bin/Activate.ps1'
  else
    echo "# SKIP: source '.venv/bin/Activate.ps1' not found"
  fi
fi
# NOTE: review .venv/bin/coloredlogs (unhandled ext venv/bin/coloredlogs) -- skip
# NOTE: review .venv/bin/detect-secrets (unhandled ext venv/bin/detect-secrets) -- skip
# NOTE: review .venv/bin/detect-secrets-hook (unhandled ext venv/bin/detect-secrets-hook) -- skip
# NOTE: review .venv/bin/dotenv (unhandled ext venv/bin/dotenv) -- skip
# NOTE: review .venv/bin/f2py (unhandled ext venv/bin/f2py) -- skip
# NOTE: review .venv/bin/fastapi (unhandled ext venv/bin/fastapi) -- skip
# NOTE: review .venv/bin/hf (unhandled ext venv/bin/hf) -- skip
# NOTE: review .venv/bin/huggingface-cli (unhandled ext venv/bin/huggingface-cli) -- skip
# NOTE: review .venv/bin/humanfriendly (unhandled ext venv/bin/humanfriendly) -- skip
# NOTE: review .venv/bin/identify-cli (unhandled ext venv/bin/identify-cli) -- skip
# NOTE: review .venv/bin/isympy (unhandled ext venv/bin/isympy) -- skip
# NOTE: review .venv/bin/jsonschema (unhandled ext venv/bin/jsonschema) -- skip
# NOTE: review .venv/bin/nodeenv (unhandled ext venv/bin/nodeenv) -- skip
# NOTE: review .venv/bin/normalizer (unhandled ext venv/bin/normalizer) -- skip
# NOTE: review .venv/bin/numpy-config (unhandled ext venv/bin/numpy-config) -- skip
# NOTE: review .venv/bin/onnxruntime_test (unhandled ext venv/bin/onnxruntime_test) -- skip
# NOTE: review .venv/bin/pip (unhandled ext venv/bin/pip) -- skip
# NOTE: review .venv/bin/pip3 (unhandled ext venv/bin/pip3) -- skip
# NOTE: review .venv/bin/pip3.9 (unhandled ext 9) -- skip
# NOTE: review .venv/bin/pre-commit (unhandled ext venv/bin/pre-commit) -- skip
# NOTE: review .venv/bin/streamlit (unhandled ext venv/bin/streamlit) -- skip
# NOTE: review .venv/bin/streamlit.cmd (unhandled ext cmd) -- skip
# NOTE: review .venv/bin/tiny-agents (unhandled ext venv/bin/tiny-agents) -- skip
# NOTE: review .venv/bin/torchfrtrace (unhandled ext venv/bin/torchfrtrace) -- skip
# NOTE: review .venv/bin/torchrun (unhandled ext venv/bin/torchrun) -- skip
# NOTE: review .venv/bin/tqdm (unhandled ext venv/bin/tqdm) -- skip
# NOTE: review .venv/bin/transformers (unhandled ext venv/bin/transformers) -- skip
# NOTE: review .venv/bin/transformers-cli (unhandled ext venv/bin/transformers-cli) -- skip
# NOTE: review .venv/bin/uvicorn (unhandled ext venv/bin/uvicorn) -- skip
# NOTE: review .venv/bin/virtualenv (unhandled ext venv/bin/virtualenv) -- skip
# NOTE: review .venv/bin/watchfiles (unhandled ext venv/bin/watchfiles) -- skip
# NOTE: review .venv/bin/websockets (unhandled ext venv/bin/websockets) -- skip
# NOTE: review .venv/bin/wheel (unhandled ext venv/bin/wheel) -- skip
# NOTE: review .venv/pyvenv.cfg (unhandled ext cfg) -- skip

# Move: cleanup_candidates.json -> tools/reports/cleanup_candidates.json
mkdir -p 'tools/reports'
if git ls-files --error-unmatch 'cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json"'
  git mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json"
else
  if [ -f 'cleanup_candidates.json' ]; then
    echo 'mv -v "cleanup_candidates.json" "tools/reports/cleanup_candidates.json" && git add -A "tools/reports/cleanup_candidates.json"'
    mv -v 'cleanup_candidates.json' 'tools/reports/cleanup_candidates.json'
    git add -A 'tools/reports/cleanup_candidates.json'
  else
    echo "# SKIP: source 'cleanup_candidates.json' not found"
  fi
fi

# Move: cleanup_summary.txt -> docs/notes/cleanup_summary.txt
mkdir -p 'docs/notes'
if git ls-files --error-unmatch 'cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "cleanup_summary.txt" "docs/notes/cleanup_summary.txt"'
  git mv -v "cleanup_summary.txt" "docs/notes/cleanup_summary.txt"
else
  if [ -f 'cleanup_summary.txt' ]; then
    echo 'mv -v "cleanup_summary.txt" "docs/notes/cleanup_summary.txt" && git add -A "docs/notes/cleanup_summary.txt"'
    mv -v 'cleanup_summary.txt' 'docs/notes/cleanup_summary.txt'
    git add -A 'docs/notes/cleanup_summary.txt'
  else
    echo "# SKIP: source 'cleanup_summary.txt' not found"
  fi
fi

# Move: connectors/confluence.py -> tools/connectors/confluence.py
mkdir -p 'tools/connectors'
if git ls-files --error-unmatch 'connectors/confluence.py' >/dev/null 2>&1; then
  echo 'git mv -v "connectors/confluence.py" "tools/connectors/confluence.py"'
  git mv -v "connectors/confluence.py" "tools/connectors/confluence.py"
else
  if [ -f 'connectors/confluence.py' ]; then
    echo 'mv -v "connectors/confluence.py" "tools/connectors/confluence.py" && git add -A "tools/connectors/confluence.py"'
    mv -v 'connectors/confluence.py' 'tools/connectors/confluence.py'
    git add -A 'tools/connectors/confluence.py'
  else
    echo "# SKIP: source 'connectors/confluence.py' not found"
  fi
fi

# Move: connectors/github.py -> tools/connectors/github.py
mkdir -p 'tools/connectors'
if git ls-files --error-unmatch 'connectors/github.py' >/dev/null 2>&1; then
  echo 'git mv -v "connectors/github.py" "tools/connectors/github.py"'
  git mv -v "connectors/github.py" "tools/connectors/github.py"
else
  if [ -f 'connectors/github.py' ]; then
    echo 'mv -v "connectors/github.py" "tools/connectors/github.py" && git add -A "tools/connectors/github.py"'
    mv -v 'connectors/github.py' 'tools/connectors/github.py'
    git add -A 'tools/connectors/github.py'
  else
    echo "# SKIP: source 'connectors/github.py' not found"
  fi
fi

# Move: create_milan_repo.sh -> tools/create_milan_repo.sh
mkdir -p 'tools'
if git ls-files --error-unmatch 'create_milan_repo.sh' >/dev/null 2>&1; then
  echo 'git mv -v "create_milan_repo.sh" "tools/create_milan_repo.sh"'
  git mv -v "create_milan_repo.sh" "tools/create_milan_repo.sh"
else
  if [ -f 'create_milan_repo.sh' ]; then
    echo 'mv -v "create_milan_repo.sh" "tools/create_milan_repo.sh" && git add -A "tools/create_milan_repo.sh"'
    mv -v 'create_milan_repo.sh' 'tools/create_milan_repo.sh'
    git add -A 'tools/create_milan_repo.sh'
  else
    echo "# SKIP: source 'create_milan_repo.sh' not found"
  fi
fi
# NOTE: review create-vector-attempt.log (unhandled ext log) -- skip
# NOTE: review db-last-200.log (unhandled ext log) -- skip
# NOTE: review docker-compose.yml (unhandled ext yml) -- skip
# NOTE: review docker-compose.yml.bak (unhandled ext bak) -- skip

# Move: embeddings/embed_adapter.py -> tools/embeddings/embed_adapter.py
mkdir -p 'tools/embeddings'
if git ls-files --error-unmatch 'embeddings/embed_adapter.py' >/dev/null 2>&1; then
  echo 'git mv -v "embeddings/embed_adapter.py" "tools/embeddings/embed_adapter.py"'
  git mv -v "embeddings/embed_adapter.py" "tools/embeddings/embed_adapter.py"
else
  if [ -f 'embeddings/embed_adapter.py' ]; then
    echo 'mv -v "embeddings/embed_adapter.py" "tools/embeddings/embed_adapter.py" && git add -A "tools/embeddings/embed_adapter.py"'
    mv -v 'embeddings/embed_adapter.py' 'tools/embeddings/embed_adapter.py'
    git add -A 'tools/embeddings/embed_adapter.py'
  else
    echo "# SKIP: source 'embeddings/embed_adapter.py' not found"
  fi
fi

# Move: embeddings/embedder.py -> tools/embeddings/embedder.py
mkdir -p 'tools/embeddings'
if git ls-files --error-unmatch 'embeddings/embedder.py' >/dev/null 2>&1; then
  echo 'git mv -v "embeddings/embedder.py" "tools/embeddings/embedder.py"'
  git mv -v "embeddings/embedder.py" "tools/embeddings/embedder.py"
else
  if [ -f 'embeddings/embedder.py' ]; then
    echo 'mv -v "embeddings/embedder.py" "tools/embeddings/embedder.py" && git add -A "tools/embeddings/embedder.py"'
    mv -v 'embeddings/embedder.py' 'tools/embeddings/embedder.py'
    git add -A 'tools/embeddings/embedder.py'
  else
    echo "# SKIP: source 'embeddings/embedder.py' not found"
  fi
fi

# Move: enhancements.json -> data/curated/misc/enhancements.json
mkdir -p 'data/curated/misc'
if git ls-files --error-unmatch 'enhancements.json' >/dev/null 2>&1; then
  echo 'git mv -v "enhancements.json" "data/curated/misc/enhancements.json"'
  git mv -v "enhancements.json" "data/curated/misc/enhancements.json"
else
  if [ -f 'enhancements.json' ]; then
    echo 'mv -v "enhancements.json" "data/curated/misc/enhancements.json" && git add -A "data/curated/misc/enhancements.json"'
    mv -v 'enhancements.json' 'data/curated/misc/enhancements.json'
    git add -A 'data/curated/misc/enhancements.json'
  else
    echo "# SKIP: source 'enhancements.json' not found"
  fi
fi

# Move: ignored_cleanup_candidates.json -> tools/reports/ignored_cleanup_candidates.json
mkdir -p 'tools/reports'
if git ls-files --error-unmatch 'ignored_cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json"'
  git mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json"
else
  if [ -f 'ignored_cleanup_candidates.json' ]; then
    echo 'mv -v "ignored_cleanup_candidates.json" "tools/reports/ignored_cleanup_candidates.json" && git add -A "tools/reports/ignored_cleanup_candidates.json"'
    mv -v 'ignored_cleanup_candidates.json' 'tools/reports/ignored_cleanup_candidates.json'
    git add -A 'tools/reports/ignored_cleanup_candidates.json'
  else
    echo "# SKIP: source 'ignored_cleanup_candidates.json' not found"
  fi
fi

# Move: ignored_cleanup_summary.txt -> docs/notes/ignored_cleanup_summary.txt
mkdir -p 'docs/notes'
if git ls-files --error-unmatch 'ignored_cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "ignored_cleanup_summary.txt" "docs/notes/ignored_cleanup_summary.txt"'
  git mv -v "ignored_cleanup_summary.txt" "docs/notes/ignored_cleanup_summary.txt"
else
  if [ -f 'ignored_cleanup_summary.txt' ]; then
    echo 'mv -v "ignored_cleanup_summary.txt" "docs/notes/ignored_cleanup_summary.txt" && git add -A "docs/notes/ignored_cleanup_summary.txt"'
    mv -v 'ignored_cleanup_summary.txt' 'docs/notes/ignored_cleanup_summary.txt'
    git add -A 'docs/notes/ignored_cleanup_summary.txt'
  else
    echo "# SKIP: source 'ignored_cleanup_summary.txt' not found"
  fi
fi
# NOTE: review ingest_mdmig_full.log (unhandled ext log) -- skip

# Move: ingesters/confluence_ingest.py -> tools/ingesters/confluence_ingest.py
mkdir -p 'tools/ingesters'
if git ls-files --error-unmatch 'ingesters/confluence_ingest.py' >/dev/null 2>&1; then
  echo 'git mv -v "ingesters/confluence_ingest.py" "tools/ingesters/confluence_ingest.py"'
  git mv -v "ingesters/confluence_ingest.py" "tools/ingesters/confluence_ingest.py"
else
  if [ -f 'ingesters/confluence_ingest.py' ]; then
    echo 'mv -v "ingesters/confluence_ingest.py" "tools/ingesters/confluence_ingest.py" && git add -A "tools/ingesters/confluence_ingest.py"'
    mv -v 'ingesters/confluence_ingest.py' 'tools/ingesters/confluence_ingest.py'
    git add -A 'tools/ingesters/confluence_ingest.py'
  else
    echo "# SKIP: source 'ingesters/confluence_ingest.py' not found"
  fi
fi

# Move: ingesters/github_ingest.py -> tools/ingesters/github_ingest.py
mkdir -p 'tools/ingesters'
if git ls-files --error-unmatch 'ingesters/github_ingest.py' >/dev/null 2>&1; then
  echo 'git mv -v "ingesters/github_ingest.py" "tools/ingesters/github_ingest.py"'
  git mv -v "ingesters/github_ingest.py" "tools/ingesters/github_ingest.py"
else
  if [ -f 'ingesters/github_ingest.py' ]; then
    echo 'mv -v "ingesters/github_ingest.py" "tools/ingesters/github_ingest.py" && git add -A "tools/ingesters/github_ingest.py"'
    mv -v 'ingesters/github_ingest.py' 'tools/ingesters/github_ingest.py'
    git add -A 'tools/ingesters/github_ingest.py'
  else
    echo "# SKIP: source 'ingesters/github_ingest.py' not found"
  fi
fi
# NOTE: review init/001-create-vector.sql (unhandled ext sql) -- skip
# NOTE: review logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log (unhandled ext log) -- skip
# NOTE: review logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log (unhandled ext log) -- skip
# NOTE: review logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log (unhandled ext log) -- skip
# NOTE: review logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log (unhandled ext log) -- skip
# NOTE: review logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log (unhandled ext log) -- skip
# NOTE: review Makefile (unhandled ext Makefile) -- skip
# NOTE: review mcp_logs.jsonl (unhandled ext jsonl) -- skip

# Move: mcp/__init__.py -> tools/mcp/__init__.py
mkdir -p 'tools/mcp'
if git ls-files --error-unmatch 'mcp/__init__.py' >/dev/null 2>&1; then
  echo 'git mv -v "mcp/__init__.py" "tools/mcp/__init__.py"'
  git mv -v "mcp/__init__.py" "tools/mcp/__init__.py"
else
  if [ -f 'mcp/__init__.py' ]; then
    echo 'mv -v "mcp/__init__.py" "tools/mcp/__init__.py" && git add -A "tools/mcp/__init__.py"'
    mv -v 'mcp/__init__.py' 'tools/mcp/__init__.py'
    git add -A 'tools/mcp/__init__.py'
  else
    echo "# SKIP: source 'mcp/__init__.py' not found"
  fi
fi

# Move: mcp/mcp.py -> tools/mcp/mcp.py
mkdir -p 'tools/mcp'
if git ls-files --error-unmatch 'mcp/mcp.py' >/dev/null 2>&1; then
  echo 'git mv -v "mcp/mcp.py" "tools/mcp/mcp.py"'
  git mv -v "mcp/mcp.py" "tools/mcp/mcp.py"
else
  if [ -f 'mcp/mcp.py' ]; then
    echo 'mv -v "mcp/mcp.py" "tools/mcp/mcp.py" && git add -A "tools/mcp/mcp.py"'
    mv -v 'mcp/mcp.py' 'tools/mcp/mcp.py'
    git add -A 'tools/mcp/mcp.py'
  else
    echo "# SKIP: source 'mcp/mcp.py' not found"
  fi
fi
# NOTE: review migrations/001_schema.sql (unhandled ext sql) -- skip
# NOTE: review pgvector-build.log (unhandled ext log) -- skip
# NOTE: review postgres-pgvector/Dockerfile (unhandled ext postgres-pgvector/Dockerfile) -- skip
# NOTE: review repo-filter.git/repo-clean/.gitignore (unhandled ext gitignore) -- skip

# Move: repo-filter.git/repo-clean/cleanup_candidates.json -> tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json
mkdir -p 'tools/reports/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json"'
  git mv -v "repo-filter.git/repo-clean/cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json"
else
  if [ -f 'repo-filter.git/repo-clean/cleanup_candidates.json' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json" && git add -A "tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json"'
    mv -v 'repo-filter.git/repo-clean/cleanup_candidates.json' 'tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json'
    git add -A 'tools/reports/repo-filter.git/repo-clean/cleanup_candidates.json'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/cleanup_candidates.json' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/cleanup_summary.txt -> docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt
mkdir -p 'docs/notes/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt"'
  git mv -v "repo-filter.git/repo-clean/cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt"
else
  if [ -f 'repo-filter.git/repo-clean/cleanup_summary.txt' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt" && git add -A "docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt"'
    mv -v 'repo-filter.git/repo-clean/cleanup_summary.txt' 'docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt'
    git add -A 'docs/notes/repo-filter.git/repo-clean/cleanup_summary.txt'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/cleanup_summary.txt' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/create_milan_repo.sh -> tools/repo-filter.git/repo-clean/create_milan_repo.sh
mkdir -p 'tools/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/create_milan_repo.sh' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/create_milan_repo.sh" "tools/repo-filter.git/repo-clean/create_milan_repo.sh"'
  git mv -v "repo-filter.git/repo-clean/create_milan_repo.sh" "tools/repo-filter.git/repo-clean/create_milan_repo.sh"
else
  if [ -f 'repo-filter.git/repo-clean/create_milan_repo.sh' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/create_milan_repo.sh" "tools/repo-filter.git/repo-clean/create_milan_repo.sh" && git add -A "tools/repo-filter.git/repo-clean/create_milan_repo.sh"'
    mv -v 'repo-filter.git/repo-clean/create_milan_repo.sh' 'tools/repo-filter.git/repo-clean/create_milan_repo.sh'
    git add -A 'tools/repo-filter.git/repo-clean/create_milan_repo.sh'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/create_milan_repo.sh' not found"
  fi
fi
# NOTE: review repo-filter.git/repo-clean/docker-compose.yml (unhandled ext yml) -- skip

# Move: repo-filter.git/repo-clean/enhancements.json -> data/curated/misc/repo-filter.git/repo-clean/enhancements.json
mkdir -p 'data/curated/misc/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/enhancements.json' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/enhancements.json" "data/curated/misc/repo-filter.git/repo-clean/enhancements.json"'
  git mv -v "repo-filter.git/repo-clean/enhancements.json" "data/curated/misc/repo-filter.git/repo-clean/enhancements.json"
else
  if [ -f 'repo-filter.git/repo-clean/enhancements.json' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/enhancements.json" "data/curated/misc/repo-filter.git/repo-clean/enhancements.json" && git add -A "data/curated/misc/repo-filter.git/repo-clean/enhancements.json"'
    mv -v 'repo-filter.git/repo-clean/enhancements.json' 'data/curated/misc/repo-filter.git/repo-clean/enhancements.json'
    git add -A 'data/curated/misc/repo-filter.git/repo-clean/enhancements.json'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/enhancements.json' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/ignored_cleanup_candidates.json -> tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json
mkdir -p 'tools/reports/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/ignored_cleanup_candidates.json' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/ignored_cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json"'
  git mv -v "repo-filter.git/repo-clean/ignored_cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json"
else
  if [ -f 'repo-filter.git/repo-clean/ignored_cleanup_candidates.json' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/ignored_cleanup_candidates.json" "tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json" && git add -A "tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json"'
    mv -v 'repo-filter.git/repo-clean/ignored_cleanup_candidates.json' 'tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json'
    git add -A 'tools/reports/repo-filter.git/repo-clean/ignored_cleanup_candidates.json'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/ignored_cleanup_candidates.json' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/ignored_cleanup_summary.txt -> docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt
mkdir -p 'docs/notes/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/ignored_cleanup_summary.txt' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/ignored_cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt"'
  git mv -v "repo-filter.git/repo-clean/ignored_cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt"
else
  if [ -f 'repo-filter.git/repo-clean/ignored_cleanup_summary.txt' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/ignored_cleanup_summary.txt" "docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt" && git add -A "docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt"'
    mv -v 'repo-filter.git/repo-clean/ignored_cleanup_summary.txt' 'docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt'
    git add -A 'docs/notes/repo-filter.git/repo-clean/ignored_cleanup_summary.txt'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/ignored_cleanup_summary.txt' not found"
  fi
fi
# NOTE: review repo-filter.git/repo-clean/Makefile (unhandled ext git/repo-clean/Makefile) -- skip

# Move: repo-filter.git/repo-clean/requirements.txt -> docs/notes/repo-filter.git/repo-clean/requirements.txt
mkdir -p 'docs/notes/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/requirements.txt' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/requirements.txt" "docs/notes/repo-filter.git/repo-clean/requirements.txt"'
  git mv -v "repo-filter.git/repo-clean/requirements.txt" "docs/notes/repo-filter.git/repo-clean/requirements.txt"
else
  if [ -f 'repo-filter.git/repo-clean/requirements.txt' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/requirements.txt" "docs/notes/repo-filter.git/repo-clean/requirements.txt" && git add -A "docs/notes/repo-filter.git/repo-clean/requirements.txt"'
    mv -v 'repo-filter.git/repo-clean/requirements.txt' 'docs/notes/repo-filter.git/repo-clean/requirements.txt'
    git add -A 'docs/notes/repo-filter.git/repo-clean/requirements.txt'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/requirements.txt' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/retrieval_api.py -> tools/repo-filter.git/repo-clean/retrieval_api.py
mkdir -p 'tools/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/retrieval_api.py' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/retrieval_api.py" "tools/repo-filter.git/repo-clean/retrieval_api.py"'
  git mv -v "repo-filter.git/repo-clean/retrieval_api.py" "tools/repo-filter.git/repo-clean/retrieval_api.py"
else
  if [ -f 'repo-filter.git/repo-clean/retrieval_api.py' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/retrieval_api.py" "tools/repo-filter.git/repo-clean/retrieval_api.py" && git add -A "tools/repo-filter.git/repo-clean/retrieval_api.py"'
    mv -v 'repo-filter.git/repo-clean/retrieval_api.py' 'tools/repo-filter.git/repo-clean/retrieval_api.py'
    git add -A 'tools/repo-filter.git/repo-clean/retrieval_api.py'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/retrieval_api.py' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/revamp_checklist.json -> data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json
mkdir -p 'data/curated/misc/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/revamp_checklist.json' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/revamp_checklist.json" "data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json"'
  git mv -v "repo-filter.git/repo-clean/revamp_checklist.json" "data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json"
else
  if [ -f 'repo-filter.git/repo-clean/revamp_checklist.json' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/revamp_checklist.json" "data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json" && git add -A "data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json"'
    mv -v 'repo-filter.git/repo-clean/revamp_checklist.json' 'data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json'
    git add -A 'data/curated/misc/repo-filter.git/repo-clean/revamp_checklist.json'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/revamp_checklist.json' not found"
  fi
fi

# Move: repo-filter.git/repo-clean/REVAMP_CHECKLIST.md -> docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md
mkdir -p 'docs/notes/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/REVAMP_CHECKLIST.md' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/REVAMP_CHECKLIST.md" "docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md"'
  git mv -v "repo-filter.git/repo-clean/REVAMP_CHECKLIST.md" "docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md"
else
  if [ -f 'repo-filter.git/repo-clean/REVAMP_CHECKLIST.md' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/REVAMP_CHECKLIST.md" "docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md" && git add -A "docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md"'
    mv -v 'repo-filter.git/repo-clean/REVAMP_CHECKLIST.md' 'docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md'
    git add -A 'docs/notes/repo-filter.git/repo-clean/REVAMP_CHECKLIST.md'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/REVAMP_CHECKLIST.md' not found"
  fi
fi
# NOTE: review repo-filter.git/repo-clean/space. (unhandled ext ) -- skip

# Move: repo-filter.git/repo-clean/tasks.json -> data/curated/misc/repo-filter.git/repo-clean/tasks.json
mkdir -p 'data/curated/misc/repo-filter.git/repo-clean'
if git ls-files --error-unmatch 'repo-filter.git/repo-clean/tasks.json' >/dev/null 2>&1; then
  echo 'git mv -v "repo-filter.git/repo-clean/tasks.json" "data/curated/misc/repo-filter.git/repo-clean/tasks.json"'
  git mv -v "repo-filter.git/repo-clean/tasks.json" "data/curated/misc/repo-filter.git/repo-clean/tasks.json"
else
  if [ -f 'repo-filter.git/repo-clean/tasks.json' ]; then
    echo 'mv -v "repo-filter.git/repo-clean/tasks.json" "data/curated/misc/repo-filter.git/repo-clean/tasks.json" && git add -A "data/curated/misc/repo-filter.git/repo-clean/tasks.json"'
    mv -v 'repo-filter.git/repo-clean/tasks.json' 'data/curated/misc/repo-filter.git/repo-clean/tasks.json'
    git add -A 'data/curated/misc/repo-filter.git/repo-clean/tasks.json'
  else
    echo "# SKIP: source 'repo-filter.git/repo-clean/tasks.json' not found"
  fi
fi
# NOTE: review repo-filter.git/repo-clean/This (unhandled ext git/repo-clean/This) -- skip

# Move: requirements.txt -> docs/notes/requirements.txt
mkdir -p 'docs/notes'
if git ls-files --error-unmatch 'requirements.txt' >/dev/null 2>&1; then
  echo 'git mv -v "requirements.txt" "docs/notes/requirements.txt"'
  git mv -v "requirements.txt" "docs/notes/requirements.txt"
else
  if [ -f 'requirements.txt' ]; then
    echo 'mv -v "requirements.txt" "docs/notes/requirements.txt" && git add -A "docs/notes/requirements.txt"'
    mv -v 'requirements.txt' 'docs/notes/requirements.txt'
    git add -A 'docs/notes/requirements.txt'
  else
    echo "# SKIP: source 'requirements.txt' not found"
  fi
fi

# Move: retrieval_api.py -> tools/retrieval_api.py
mkdir -p 'tools'
if git ls-files --error-unmatch 'retrieval_api.py' >/dev/null 2>&1; then
  echo 'git mv -v "retrieval_api.py" "tools/retrieval_api.py"'
  git mv -v "retrieval_api.py" "tools/retrieval_api.py"
else
  if [ -f 'retrieval_api.py' ]; then
    echo 'mv -v "retrieval_api.py" "tools/retrieval_api.py" && git add -A "tools/retrieval_api.py"'
    mv -v 'retrieval_api.py' 'tools/retrieval_api.py'
    git add -A 'tools/retrieval_api.py'
  else
    echo "# SKIP: source 'retrieval_api.py' not found"
  fi
fi

# Move: revamp_checklist.json -> data/curated/misc/revamp_checklist.json
mkdir -p 'data/curated/misc'
if git ls-files --error-unmatch 'revamp_checklist.json' >/dev/null 2>&1; then
  echo 'git mv -v "revamp_checklist.json" "data/curated/misc/revamp_checklist.json"'
  git mv -v "revamp_checklist.json" "data/curated/misc/revamp_checklist.json"
else
  if [ -f 'revamp_checklist.json' ]; then
    echo 'mv -v "revamp_checklist.json" "data/curated/misc/revamp_checklist.json" && git add -A "data/curated/misc/revamp_checklist.json"'
    mv -v 'revamp_checklist.json' 'data/curated/misc/revamp_checklist.json'
    git add -A 'data/curated/misc/revamp_checklist.json'
  else
    echo "# SKIP: source 'revamp_checklist.json' not found"
  fi
fi

# Move: REVAMP_CHECKLIST.md -> docs/notes/REVAMP_CHECKLIST.md
mkdir -p 'docs/notes'
if git ls-files --error-unmatch 'REVAMP_CHECKLIST.md' >/dev/null 2>&1; then
  echo 'git mv -v "REVAMP_CHECKLIST.md" "docs/notes/REVAMP_CHECKLIST.md"'
  git mv -v "REVAMP_CHECKLIST.md" "docs/notes/REVAMP_CHECKLIST.md"
else
  if [ -f 'REVAMP_CHECKLIST.md' ]; then
    echo 'mv -v "REVAMP_CHECKLIST.md" "docs/notes/REVAMP_CHECKLIST.md" && git add -A "docs/notes/REVAMP_CHECKLIST.md"'
    mv -v 'REVAMP_CHECKLIST.md' 'docs/notes/REVAMP_CHECKLIST.md'
    git add -A 'docs/notes/REVAMP_CHECKLIST.md'
  else
    echo "# SKIP: source 'REVAMP_CHECKLIST.md' not found"
  fi
fi

# Move: revamp/archive/README.md -> docs/notes/revamp/archive/README.md
mkdir -p 'docs/notes/revamp/archive'
if git ls-files --error-unmatch 'revamp/archive/README.md' >/dev/null 2>&1; then
  echo 'git mv -v "revamp/archive/README.md" "docs/notes/revamp/archive/README.md"'
  git mv -v "revamp/archive/README.md" "docs/notes/revamp/archive/README.md"
else
  if [ -f 'revamp/archive/README.md' ]; then
    echo 'mv -v "revamp/archive/README.md" "docs/notes/revamp/archive/README.md" && git add -A "docs/notes/revamp/archive/README.md"'
    mv -v 'revamp/archive/README.md' 'docs/notes/revamp/archive/README.md'
    git add -A 'docs/notes/revamp/archive/README.md'
  else
    echo "# SKIP: source 'revamp/archive/README.md' not found"
  fi
fi
# NOTE: review space. (unhandled ext ) -- skip

# Move: storage/__init__.py -> tools/storage/__init__.py
mkdir -p 'tools/storage'
if git ls-files --error-unmatch 'storage/__init__.py' >/dev/null 2>&1; then
  echo 'git mv -v "storage/__init__.py" "tools/storage/__init__.py"'
  git mv -v "storage/__init__.py" "tools/storage/__init__.py"
else
  if [ -f 'storage/__init__.py' ]; then
    echo 'mv -v "storage/__init__.py" "tools/storage/__init__.py" && git add -A "tools/storage/__init__.py"'
    mv -v 'storage/__init__.py' 'tools/storage/__init__.py'
    git add -A 'tools/storage/__init__.py'
  else
    echo "# SKIP: source 'storage/__init__.py' not found"
  fi
fi

# Move: storage/postgres.py -> tools/storage/postgres.py
mkdir -p 'tools/storage'
if git ls-files --error-unmatch 'storage/postgres.py' >/dev/null 2>&1; then
  echo 'git mv -v "storage/postgres.py" "tools/storage/postgres.py"'
  git mv -v "storage/postgres.py" "tools/storage/postgres.py"
else
  if [ -f 'storage/postgres.py' ]; then
    echo 'mv -v "storage/postgres.py" "tools/storage/postgres.py" && git add -A "tools/storage/postgres.py"'
    mv -v 'storage/postgres.py' 'tools/storage/postgres.py'
    git add -A 'tools/storage/postgres.py'
  else
    echo "# SKIP: source 'storage/postgres.py' not found"
  fi
fi

# Move: tasks.json -> data/curated/misc/tasks.json
mkdir -p 'data/curated/misc'
if git ls-files --error-unmatch 'tasks.json' >/dev/null 2>&1; then
  echo 'git mv -v "tasks.json" "data/curated/misc/tasks.json"'
  git mv -v "tasks.json" "data/curated/misc/tasks.json"
else
  if [ -f 'tasks.json' ]; then
    echo 'mv -v "tasks.json" "data/curated/misc/tasks.json" && git add -A "data/curated/misc/tasks.json"'
    mv -v 'tasks.json' 'data/curated/misc/tasks.json'
    git add -A 'data/curated/misc/tasks.json'
  else
    echo "# SKIP: source 'tasks.json' not found"
  fi
fi
# NOTE: review tasks.json.bak (unhandled ext bak) -- skip
# NOTE: review This (unhandled ext This) -- skip

# Move: tools/__init__.py -> tools/tools/__init__.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/__init__.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/__init__.py" "tools/tools/__init__.py"'
  git mv -v "tools/__init__.py" "tools/tools/__init__.py"
else
  if [ -f 'tools/__init__.py' ]; then
    echo 'mv -v "tools/__init__.py" "tools/tools/__init__.py" && git add -A "tools/tools/__init__.py"'
    mv -v 'tools/__init__.py' 'tools/tools/__init__.py'
    git add -A 'tools/tools/__init__.py'
  else
    echo "# SKIP: source 'tools/__init__.py' not found"
  fi
fi
# NOTE: review tools/.DS_Store (unhandled ext DS_Store) -- skip

# Move: tools/analyze_misses.py -> tools/tools/analyze_misses.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/analyze_misses.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/analyze_misses.py" "tools/tools/analyze_misses.py"'
  git mv -v "tools/analyze_misses.py" "tools/tools/analyze_misses.py"
else
  if [ -f 'tools/analyze_misses.py' ]; then
    echo 'mv -v "tools/analyze_misses.py" "tools/tools/analyze_misses.py" && git add -A "tools/tools/analyze_misses.py"'
    mv -v 'tools/analyze_misses.py' 'tools/tools/analyze_misses.py'
    git add -A 'tools/tools/analyze_misses.py'
  else
    echo "# SKIP: source 'tools/analyze_misses.py' not found"
  fi
fi

# Move: tools/ann_eval_1761706585.json -> tools/reports/tools/ann_eval_1761706585.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/ann_eval_1761706585.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ann_eval_1761706585.json" "tools/reports/tools/ann_eval_1761706585.json"'
  git mv -v "tools/ann_eval_1761706585.json" "tools/reports/tools/ann_eval_1761706585.json"
else
  if [ -f 'tools/ann_eval_1761706585.json' ]; then
    echo 'mv -v "tools/ann_eval_1761706585.json" "tools/reports/tools/ann_eval_1761706585.json" && git add -A "tools/reports/tools/ann_eval_1761706585.json"'
    mv -v 'tools/ann_eval_1761706585.json' 'tools/reports/tools/ann_eval_1761706585.json'
    git add -A 'tools/reports/tools/ann_eval_1761706585.json'
  else
    echo "# SKIP: source 'tools/ann_eval_1761706585.json' not found"
  fi
fi

# Move: tools/ann_eval_1761706599.json -> tools/reports/tools/ann_eval_1761706599.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/ann_eval_1761706599.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ann_eval_1761706599.json" "tools/reports/tools/ann_eval_1761706599.json"'
  git mv -v "tools/ann_eval_1761706599.json" "tools/reports/tools/ann_eval_1761706599.json"
else
  if [ -f 'tools/ann_eval_1761706599.json' ]; then
    echo 'mv -v "tools/ann_eval_1761706599.json" "tools/reports/tools/ann_eval_1761706599.json" && git add -A "tools/reports/tools/ann_eval_1761706599.json"'
    mv -v 'tools/ann_eval_1761706599.json' 'tools/reports/tools/ann_eval_1761706599.json'
    git add -A 'tools/reports/tools/ann_eval_1761706599.json'
  else
    echo "# SKIP: source 'tools/ann_eval_1761706599.json' not found"
  fi
fi

# Move: tools/ann_eval_ef128.json -> tools/reports/tools/ann_eval_ef128.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/ann_eval_ef128.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ann_eval_ef128.json" "tools/reports/tools/ann_eval_ef128.json"'
  git mv -v "tools/ann_eval_ef128.json" "tools/reports/tools/ann_eval_ef128.json"
else
  if [ -f 'tools/ann_eval_ef128.json' ]; then
    echo 'mv -v "tools/ann_eval_ef128.json" "tools/reports/tools/ann_eval_ef128.json" && git add -A "tools/reports/tools/ann_eval_ef128.json"'
    mv -v 'tools/ann_eval_ef128.json' 'tools/reports/tools/ann_eval_ef128.json'
    git add -A 'tools/reports/tools/ann_eval_ef128.json'
  else
    echo "# SKIP: source 'tools/ann_eval_ef128.json' not found"
  fi
fi

# Move: tools/ann_eval_ef256.json -> tools/reports/tools/ann_eval_ef256.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/ann_eval_ef256.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ann_eval_ef256.json" "tools/reports/tools/ann_eval_ef256.json"'
  git mv -v "tools/ann_eval_ef256.json" "tools/reports/tools/ann_eval_ef256.json"
else
  if [ -f 'tools/ann_eval_ef256.json' ]; then
    echo 'mv -v "tools/ann_eval_ef256.json" "tools/reports/tools/ann_eval_ef256.json" && git add -A "tools/reports/tools/ann_eval_ef256.json"'
    mv -v 'tools/ann_eval_ef256.json' 'tools/reports/tools/ann_eval_ef256.json'
    git add -A 'tools/reports/tools/ann_eval_ef256.json'
  else
    echo "# SKIP: source 'tools/ann_eval_ef256.json' not found"
  fi
fi

# Move: tools/ann_eval_ef64.json -> tools/reports/tools/ann_eval_ef64.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/ann_eval_ef64.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ann_eval_ef64.json" "tools/reports/tools/ann_eval_ef64.json"'
  git mv -v "tools/ann_eval_ef64.json" "tools/reports/tools/ann_eval_ef64.json"
else
  if [ -f 'tools/ann_eval_ef64.json' ]; then
    echo 'mv -v "tools/ann_eval_ef64.json" "tools/reports/tools/ann_eval_ef64.json" && git add -A "tools/reports/tools/ann_eval_ef64.json"'
    mv -v 'tools/ann_eval_ef64.json' 'tools/reports/tools/ann_eval_ef64.json'
    git add -A 'tools/reports/tools/ann_eval_ef64.json'
  else
    echo "# SKIP: source 'tools/ann_eval_ef64.json' not found"
  fi
fi

# Move: tools/check_connectors.py -> tools/tools/check_connectors.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/check_connectors.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/check_connectors.py" "tools/tools/check_connectors.py"'
  git mv -v "tools/check_connectors.py" "tools/tools/check_connectors.py"
else
  if [ -f 'tools/check_connectors.py' ]; then
    echo 'mv -v "tools/check_connectors.py" "tools/tools/check_connectors.py" && git add -A "tools/tools/check_connectors.py"'
    mv -v 'tools/check_connectors.py' 'tools/tools/check_connectors.py'
    git add -A 'tools/tools/check_connectors.py'
  else
    echo "# SKIP: source 'tools/check_connectors.py' not found"
  fi
fi

# Move: tools/check_similarity.py -> tools/tools/check_similarity.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/check_similarity.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/check_similarity.py" "tools/tools/check_similarity.py"'
  git mv -v "tools/check_similarity.py" "tools/tools/check_similarity.py"
else
  if [ -f 'tools/check_similarity.py' ]; then
    echo 'mv -v "tools/check_similarity.py" "tools/tools/check_similarity.py" && git add -A "tools/tools/check_similarity.py"'
    mv -v 'tools/check_similarity.py' 'tools/tools/check_similarity.py'
    git add -A 'tools/tools/check_similarity.py'
  else
    echo "# SKIP: source 'tools/check_similarity.py' not found"
  fi
fi

# Move: tools/collect_pages_ids.py -> tools/tools/collect_pages_ids.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/collect_pages_ids.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/collect_pages_ids.py" "tools/tools/collect_pages_ids.py"'
  git mv -v "tools/collect_pages_ids.py" "tools/tools/collect_pages_ids.py"
else
  if [ -f 'tools/collect_pages_ids.py' ]; then
    echo 'mv -v "tools/collect_pages_ids.py" "tools/tools/collect_pages_ids.py" && git add -A "tools/tools/collect_pages_ids.py"'
    mv -v 'tools/collect_pages_ids.py' 'tools/tools/collect_pages_ids.py'
    git add -A 'tools/tools/collect_pages_ids.py'
  else
    echo "# SKIP: source 'tools/collect_pages_ids.py' not found"
  fi
fi

# Move: tools/do_moves.sh -> tools/tools/do_moves.sh
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/do_moves.sh' >/dev/null 2>&1; then
  echo 'git mv -v "tools/do_moves.sh" "tools/tools/do_moves.sh"'
  git mv -v "tools/do_moves.sh" "tools/tools/do_moves.sh"
else
  if [ -f 'tools/do_moves.sh' ]; then
    echo 'mv -v "tools/do_moves.sh" "tools/tools/do_moves.sh" && git add -A "tools/tools/do_moves.sh"'
    mv -v 'tools/do_moves.sh' 'tools/tools/do_moves.sh'
    git add -A 'tools/tools/do_moves.sh'
  else
    echo "# SKIP: source 'tools/do_moves.sh' not found"
  fi
fi

# Move: tools/eval_ann.py -> tools/tools/eval_ann.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/eval_ann.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/eval_ann.py" "tools/tools/eval_ann.py"'
  git mv -v "tools/eval_ann.py" "tools/tools/eval_ann.py"
else
  if [ -f 'tools/eval_ann.py' ]; then
    echo 'mv -v "tools/eval_ann.py" "tools/tools/eval_ann.py" && git add -A "tools/tools/eval_ann.py"'
    mv -v 'tools/eval_ann.py' 'tools/tools/eval_ann.py'
    git add -A 'tools/tools/eval_ann.py'
  else
    echo "# SKIP: source 'tools/eval_ann.py' not found"
  fi
fi

# Move: tools/eval_fusion.py -> tools/tools/eval_fusion.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/eval_fusion.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/eval_fusion.py" "tools/tools/eval_fusion.py"'
  git mv -v "tools/eval_fusion.py" "tools/tools/eval_fusion.py"
else
  if [ -f 'tools/eval_fusion.py' ]; then
    echo 'mv -v "tools/eval_fusion.py" "tools/tools/eval_fusion.py" && git add -A "tools/tools/eval_fusion.py"'
    mv -v 'tools/eval_fusion.py' 'tools/tools/eval_fusion.py'
    git add -A 'tools/tools/eval_fusion.py'
  else
    echo "# SKIP: source 'tools/eval_fusion.py' not found"
  fi
fi

# Move: tools/fusion_analysis_ef64.json -> tools/reports/tools/fusion_analysis_ef64.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/fusion_analysis_ef64.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/fusion_analysis_ef64.json" "tools/reports/tools/fusion_analysis_ef64.json"'
  git mv -v "tools/fusion_analysis_ef64.json" "tools/reports/tools/fusion_analysis_ef64.json"
else
  if [ -f 'tools/fusion_analysis_ef64.json' ]; then
    echo 'mv -v "tools/fusion_analysis_ef64.json" "tools/reports/tools/fusion_analysis_ef64.json" && git add -A "tools/reports/tools/fusion_analysis_ef64.json"'
    mv -v 'tools/fusion_analysis_ef64.json' 'tools/reports/tools/fusion_analysis_ef64.json'
    git add -A 'tools/reports/tools/fusion_analysis_ef64.json'
  else
    echo "# SKIP: source 'tools/fusion_analysis_ef64.json' not found"
  fi
fi

# Move: tools/fusion_eval_ef128.json -> tools/reports/tools/fusion_eval_ef128.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/fusion_eval_ef128.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/fusion_eval_ef128.json" "tools/reports/tools/fusion_eval_ef128.json"'
  git mv -v "tools/fusion_eval_ef128.json" "tools/reports/tools/fusion_eval_ef128.json"
else
  if [ -f 'tools/fusion_eval_ef128.json' ]; then
    echo 'mv -v "tools/fusion_eval_ef128.json" "tools/reports/tools/fusion_eval_ef128.json" && git add -A "tools/reports/tools/fusion_eval_ef128.json"'
    mv -v 'tools/fusion_eval_ef128.json' 'tools/reports/tools/fusion_eval_ef128.json'
    git add -A 'tools/reports/tools/fusion_eval_ef128.json'
  else
    echo "# SKIP: source 'tools/fusion_eval_ef128.json' not found"
  fi
fi

# Move: tools/fusion_eval_ef64.json -> tools/reports/tools/fusion_eval_ef64.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/fusion_eval_ef64.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/fusion_eval_ef64.json" "tools/reports/tools/fusion_eval_ef64.json"'
  git mv -v "tools/fusion_eval_ef64.json" "tools/reports/tools/fusion_eval_ef64.json"
else
  if [ -f 'tools/fusion_eval_ef64.json' ]; then
    echo 'mv -v "tools/fusion_eval_ef64.json" "tools/reports/tools/fusion_eval_ef64.json" && git add -A "tools/reports/tools/fusion_eval_ef64.json"'
    mv -v 'tools/fusion_eval_ef64.json' 'tools/reports/tools/fusion_eval_ef64.json'
    git add -A 'tools/reports/tools/fusion_eval_ef64.json'
  else
    echo "# SKIP: source 'tools/fusion_eval_ef64.json' not found"
  fi
fi

# Move: tools/fusion_eval_k300.json -> tools/reports/tools/fusion_eval_k300.json
mkdir -p 'tools/reports/tools'
if git ls-files --error-unmatch 'tools/fusion_eval_k300.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/fusion_eval_k300.json" "tools/reports/tools/fusion_eval_k300.json"'
  git mv -v "tools/fusion_eval_k300.json" "tools/reports/tools/fusion_eval_k300.json"
else
  if [ -f 'tools/fusion_eval_k300.json' ]; then
    echo 'mv -v "tools/fusion_eval_k300.json" "tools/reports/tools/fusion_eval_k300.json" && git add -A "tools/reports/tools/fusion_eval_k300.json"'
    mv -v 'tools/fusion_eval_k300.json' 'tools/reports/tools/fusion_eval_k300.json'
    git add -A 'tools/reports/tools/fusion_eval_k300.json'
  else
    echo "# SKIP: source 'tools/fusion_eval_k300.json' not found"
  fi
fi

# Move: tools/generate_cleanup_candidates.py -> tools/tools/generate_cleanup_candidates.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/generate_cleanup_candidates.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/generate_cleanup_candidates.py" "tools/tools/generate_cleanup_candidates.py"'
  git mv -v "tools/generate_cleanup_candidates.py" "tools/tools/generate_cleanup_candidates.py"
else
  if [ -f 'tools/generate_cleanup_candidates.py' ]; then
    echo 'mv -v "tools/generate_cleanup_candidates.py" "tools/tools/generate_cleanup_candidates.py" && git add -A "tools/tools/generate_cleanup_candidates.py"'
    mv -v 'tools/generate_cleanup_candidates.py' 'tools/tools/generate_cleanup_candidates.py'
    git add -A 'tools/tools/generate_cleanup_candidates.py'
  else
    echo "# SKIP: source 'tools/generate_cleanup_candidates.py' not found"
  fi
fi

# Move: tools/generate_ground_truth.py -> tools/tools/generate_ground_truth.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/generate_ground_truth.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/generate_ground_truth.py" "tools/tools/generate_ground_truth.py"'
  git mv -v "tools/generate_ground_truth.py" "tools/tools/generate_ground_truth.py"
else
  if [ -f 'tools/generate_ground_truth.py' ]; then
    echo 'mv -v "tools/generate_ground_truth.py" "tools/tools/generate_ground_truth.py" && git add -A "tools/tools/generate_ground_truth.py"'
    mv -v 'tools/generate_ground_truth.py' 'tools/tools/generate_ground_truth.py'
    git add -A 'tools/tools/generate_ground_truth.py'
  else
    echo "# SKIP: source 'tools/generate_ground_truth.py' not found"
  fi
fi

# Move: tools/generate_ignored_candidates.py -> tools/tools/generate_ignored_candidates.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/generate_ignored_candidates.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/generate_ignored_candidates.py" "tools/tools/generate_ignored_candidates.py"'
  git mv -v "tools/generate_ignored_candidates.py" "tools/tools/generate_ignored_candidates.py"
else
  if [ -f 'tools/generate_ignored_candidates.py' ]; then
    echo 'mv -v "tools/generate_ignored_candidates.py" "tools/tools/generate_ignored_candidates.py" && git add -A "tools/tools/generate_ignored_candidates.py"'
    mv -v 'tools/generate_ignored_candidates.py' 'tools/tools/generate_ignored_candidates.py'
    git add -A 'tools/tools/generate_ignored_candidates.py'
  else
    echo "# SKIP: source 'tools/generate_ignored_candidates.py' not found"
  fi
fi

# Move: tools/ground_truth.json -> data/curated/misc/tools/ground_truth.json
mkdir -p 'data/curated/misc/tools'
if git ls-files --error-unmatch 'tools/ground_truth.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/ground_truth.json" "data/curated/misc/tools/ground_truth.json"'
  git mv -v "tools/ground_truth.json" "data/curated/misc/tools/ground_truth.json"
else
  if [ -f 'tools/ground_truth.json' ]; then
    echo 'mv -v "tools/ground_truth.json" "data/curated/misc/tools/ground_truth.json" && git add -A "data/curated/misc/tools/ground_truth.json"'
    mv -v 'tools/ground_truth.json' 'data/curated/misc/tools/ground_truth.json'
    git add -A 'data/curated/misc/tools/ground_truth.json'
  else
    echo "# SKIP: source 'tools/ground_truth.json' not found"
  fi
fi

# Move: tools/migrate_embeddings.py -> tools/tools/migrate_embeddings.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/migrate_embeddings.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/migrate_embeddings.py" "tools/tools/migrate_embeddings.py"'
  git mv -v "tools/migrate_embeddings.py" "tools/tools/migrate_embeddings.py"
else
  if [ -f 'tools/migrate_embeddings.py' ]; then
    echo 'mv -v "tools/migrate_embeddings.py" "tools/tools/migrate_embeddings.py" && git add -A "tools/tools/migrate_embeddings.py"'
    mv -v 'tools/migrate_embeddings.py' 'tools/tools/migrate_embeddings.py'
    git add -A 'tools/tools/migrate_embeddings.py'
  else
    echo "# SKIP: source 'tools/migrate_embeddings.py' not found"
  fi
fi

# Move: tools/organize_repo_tailored.sh -> tools/tools/organize_repo_tailored.sh
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/organize_repo_tailored.sh' >/dev/null 2>&1; then
  echo 'git mv -v "tools/organize_repo_tailored.sh" "tools/tools/organize_repo_tailored.sh"'
  git mv -v "tools/organize_repo_tailored.sh" "tools/tools/organize_repo_tailored.sh"
else
  if [ -f 'tools/organize_repo_tailored.sh' ]; then
    echo 'mv -v "tools/organize_repo_tailored.sh" "tools/tools/organize_repo_tailored.sh" && git add -A "tools/tools/organize_repo_tailored.sh"'
    mv -v 'tools/organize_repo_tailored.sh' 'tools/tools/organize_repo_tailored.sh'
    git add -A 'tools/tools/organize_repo_tailored.sh'
  else
    echo "# SKIP: source 'tools/organize_repo_tailored.sh' not found"
  fi
fi

# Move: tools/quick_failure_summary.py -> tools/tools/quick_failure_summary.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/quick_failure_summary.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/quick_failure_summary.py" "tools/tools/quick_failure_summary.py"'
  git mv -v "tools/quick_failure_summary.py" "tools/tools/quick_failure_summary.py"
else
  if [ -f 'tools/quick_failure_summary.py' ]; then
    echo 'mv -v "tools/quick_failure_summary.py" "tools/tools/quick_failure_summary.py" && git add -A "tools/tools/quick_failure_summary.py"'
    mv -v 'tools/quick_failure_summary.py' 'tools/tools/quick_failure_summary.py'
    git add -A 'tools/tools/quick_failure_summary.py'
  else
    echo "# SKIP: source 'tools/quick_failure_summary.py' not found"
  fi
fi

# Move: tools/rechunk_documents.py -> tools/tools/rechunk_documents.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/rechunk_documents.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/rechunk_documents.py" "tools/tools/rechunk_documents.py"'
  git mv -v "tools/rechunk_documents.py" "tools/tools/rechunk_documents.py"
else
  if [ -f 'tools/rechunk_documents.py' ]; then
    echo 'mv -v "tools/rechunk_documents.py" "tools/tools/rechunk_documents.py" && git add -A "tools/tools/rechunk_documents.py"'
    mv -v 'tools/rechunk_documents.py' 'tools/tools/rechunk_documents.py'
    git add -A 'tools/tools/rechunk_documents.py'
  else
    echo "# SKIP: source 'tools/rechunk_documents.py' not found"
  fi
fi

# Move: tools/rerank_union.py -> tools/tools/rerank_union.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/rerank_union.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/rerank_union.py" "tools/tools/rerank_union.py"'
  git mv -v "tools/rerank_union.py" "tools/tools/rerank_union.py"
else
  if [ -f 'tools/rerank_union.py' ]; then
    echo 'mv -v "tools/rerank_union.py" "tools/tools/rerank_union.py" && git add -A "tools/tools/rerank_union.py"'
    mv -v 'tools/rerank_union.py' 'tools/tools/rerank_union.py'
    git add -A 'tools/tools/rerank_union.py'
  else
    echo "# SKIP: source 'tools/rerank_union.py' not found"
  fi
fi

# Move: tools/similarity_ef64.json -> data/curated/misc/tools/similarity_ef64.json
mkdir -p 'data/curated/misc/tools'
if git ls-files --error-unmatch 'tools/similarity_ef64.json' >/dev/null 2>&1; then
  echo 'git mv -v "tools/similarity_ef64.json" "data/curated/misc/tools/similarity_ef64.json"'
  git mv -v "tools/similarity_ef64.json" "data/curated/misc/tools/similarity_ef64.json"
else
  if [ -f 'tools/similarity_ef64.json' ]; then
    echo 'mv -v "tools/similarity_ef64.json" "data/curated/misc/tools/similarity_ef64.json" && git add -A "data/curated/misc/tools/similarity_ef64.json"'
    mv -v 'tools/similarity_ef64.json' 'data/curated/misc/tools/similarity_ef64.json'
    git add -A 'data/curated/misc/tools/similarity_ef64.json'
  else
    echo "# SKIP: source 'tools/similarity_ef64.json' not found"
  fi
fi

# Move: tools/test_insert_chunk.py -> tools/tools/test_insert_chunk.py
mkdir -p 'tools/tools'
if git ls-files --error-unmatch 'tools/test_insert_chunk.py' >/dev/null 2>&1; then
  echo 'git mv -v "tools/test_insert_chunk.py" "tools/tools/test_insert_chunk.py"'
  git mv -v "tools/test_insert_chunk.py" "tools/tools/test_insert_chunk.py"
else
  if [ -f 'tools/test_insert_chunk.py' ]; then
    echo 'mv -v "tools/test_insert_chunk.py" "tools/tools/test_insert_chunk.py" && git add -A "tools/tools/test_insert_chunk.py"'
    mv -v 'tools/test_insert_chunk.py' 'tools/tools/test_insert_chunk.py'
    git add -A 'tools/tools/test_insert_chunk.py'
  else
    echo "# SKIP: source 'tools/test_insert_chunk.py' not found"
  fi
fi

# Move: ui/__init__.py -> tools/ui/__init__.py
mkdir -p 'tools/ui'
if git ls-files --error-unmatch 'ui/__init__.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/__init__.py" "tools/ui/__init__.py"'
  git mv -v "ui/__init__.py" "tools/ui/__init__.py"
else
  if [ -f 'ui/__init__.py' ]; then
    echo 'mv -v "ui/__init__.py" "tools/ui/__init__.py" && git add -A "tools/ui/__init__.py"'
    mv -v 'ui/__init__.py' 'tools/ui/__init__.py'
    git add -A 'tools/ui/__init__.py'
  else
    echo "# SKIP: source 'ui/__init__.py' not found"
  fi
fi
# NOTE: review ui/.DS_Store (unhandled ext DS_Store) -- skip

# Move: ui/app.py -> tools/ui/app.py
mkdir -p 'tools/ui'
if git ls-files --error-unmatch 'ui/app.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/app.py" "tools/ui/app.py"'
  git mv -v "ui/app.py" "tools/ui/app.py"
else
  if [ -f 'ui/app.py' ]; then
    echo 'mv -v "ui/app.py" "tools/ui/app.py" && git add -A "tools/ui/app.py"'
    mv -v 'ui/app.py' 'tools/ui/app.py'
    git add -A 'tools/ui/app.py'
  else
    echo "# SKIP: source 'ui/app.py' not found"
  fi
fi
# NOTE: review ui/pages/.DS_Store (unhandled ext DS_Store) -- skip

# Move: ui/pages/ANN_Evaluation.py -> tools/ui/pages/ANN_Evaluation.py
mkdir -p 'tools/ui/pages'
if git ls-files --error-unmatch 'ui/pages/ANN_Evaluation.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/pages/ANN_Evaluation.py" "tools/ui/pages/ANN_Evaluation.py"'
  git mv -v "ui/pages/ANN_Evaluation.py" "tools/ui/pages/ANN_Evaluation.py"
else
  if [ -f 'ui/pages/ANN_Evaluation.py' ]; then
    echo 'mv -v "ui/pages/ANN_Evaluation.py" "tools/ui/pages/ANN_Evaluation.py" && git add -A "tools/ui/pages/ANN_Evaluation.py"'
    mv -v 'ui/pages/ANN_Evaluation.py' 'tools/ui/pages/ANN_Evaluation.py'
    git add -A 'tools/ui/pages/ANN_Evaluation.py'
  else
    echo "# SKIP: source 'ui/pages/ANN_Evaluation.py' not found"
  fi
fi

# Move: ui/pages/Failure_Inspector.py -> tools/ui/pages/Failure_Inspector.py
mkdir -p 'tools/ui/pages'
if git ls-files --error-unmatch 'ui/pages/Failure_Inspector.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/pages/Failure_Inspector.py" "tools/ui/pages/Failure_Inspector.py"'
  git mv -v "ui/pages/Failure_Inspector.py" "tools/ui/pages/Failure_Inspector.py"
else
  if [ -f 'ui/pages/Failure_Inspector.py' ]; then
    echo 'mv -v "ui/pages/Failure_Inspector.py" "tools/ui/pages/Failure_Inspector.py" && git add -A "tools/ui/pages/Failure_Inspector.py"'
    mv -v 'ui/pages/Failure_Inspector.py' 'tools/ui/pages/Failure_Inspector.py'
    git add -A 'tools/ui/pages/Failure_Inspector.py'
  else
    echo "# SKIP: source 'ui/pages/Failure_Inspector.py' not found"
  fi
fi

# Move: ui/pages/Revamp_Checklist.py -> tools/ui/pages/Revamp_Checklist.py
mkdir -p 'tools/ui/pages'
if git ls-files --error-unmatch 'ui/pages/Revamp_Checklist.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/pages/Revamp_Checklist.py" "tools/ui/pages/Revamp_Checklist.py"'
  git mv -v "ui/pages/Revamp_Checklist.py" "tools/ui/pages/Revamp_Checklist.py"
else
  if [ -f 'ui/pages/Revamp_Checklist.py' ]; then
    echo 'mv -v "ui/pages/Revamp_Checklist.py" "tools/ui/pages/Revamp_Checklist.py" && git add -A "tools/ui/pages/Revamp_Checklist.py"'
    mv -v 'ui/pages/Revamp_Checklist.py' 'tools/ui/pages/Revamp_Checklist.py'
    git add -A 'tools/ui/pages/Revamp_Checklist.py'
  else
    echo "# SKIP: source 'ui/pages/Revamp_Checklist.py' not found"
  fi
fi

# Move: ui/pages/Tasks_Manager.py -> tools/ui/pages/Tasks_Manager.py
mkdir -p 'tools/ui/pages'
if git ls-files --error-unmatch 'ui/pages/Tasks_Manager.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/pages/Tasks_Manager.py" "tools/ui/pages/Tasks_Manager.py"'
  git mv -v "ui/pages/Tasks_Manager.py" "tools/ui/pages/Tasks_Manager.py"
else
  if [ -f 'ui/pages/Tasks_Manager.py' ]; then
    echo 'mv -v "ui/pages/Tasks_Manager.py" "tools/ui/pages/Tasks_Manager.py" && git add -A "tools/ui/pages/Tasks_Manager.py"'
    mv -v 'ui/pages/Tasks_Manager.py' 'tools/ui/pages/Tasks_Manager.py'
    git add -A 'tools/ui/pages/Tasks_Manager.py'
  else
    echo "# SKIP: source 'ui/pages/Tasks_Manager.py' not found"
  fi
fi

# Move: ui/tasks.py -> tools/ui/tasks.py
mkdir -p 'tools/ui'
if git ls-files --error-unmatch 'ui/tasks.py' >/dev/null 2>&1; then
  echo 'git mv -v "ui/tasks.py" "tools/ui/tasks.py"'
  git mv -v "ui/tasks.py" "tools/ui/tasks.py"
else
  if [ -f 'ui/tasks.py' ]; then
    echo 'mv -v "ui/tasks.py" "tools/ui/tasks.py" && git add -A "tools/ui/tasks.py"'
    mv -v 'ui/tasks.py' 'tools/ui/tasks.py'
    git add -A 'tools/ui/tasks.py'
  else
    echo "# SKIP: source 'ui/tasks.py' not found"
  fi
fi

# --- archive large/ignored files from ignored_cleanup_candidates.json ---

# Archive (ignored large): embeddings/embed_adapter.py
mkdir -p revamp/archive/20251109/embeddings
if git ls-files --error-unmatch "embeddings/embed_adapter.py" >/dev/null 2>&1; then
  echo "git mv -v 'embeddings/embed_adapter.py' 'revamp/archive/20251109/embeddings/embed_adapter.py'"; git mv -v "embeddings/embed_adapter.py" "revamp/archive/20251109/embeddings/embed_adapter.py"
else
  if [ -f "embeddings/embed_adapter.py" ]; then
    echo "mv -v 'embeddings/embed_adapter.py' 'revamp/archive/20251109/embeddings/embed_adapter.py' && git add -A 'revamp/archive/20251109/embeddings/embed_adapter.py'"; mv -v "embeddings/embed_adapter.py" "revamp/archive/20251109/embeddings/embed_adapter.py"; git add -A "revamp/archive/20251109/embeddings/embed_adapter.py"
  else
    echo "# SKIP (not found) embeddings/embed_adapter.py"
  fi
fi

# Archive (ignored large): logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log
mkdir -p revamp/archive/20251109/logs
if git ls-files --error-unmatch "logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log" >/dev/null 2>&1; then
  echo "git mv -v 'logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log' 'revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log'"; git mv -v "logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log" "revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log"
else
  if [ -f "logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log" ]; then
    echo "mv -v 'logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log' 'revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log' && git add -A 'revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log'"; mv -v "logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log" "revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log"; git add -A "revamp/archive/20251109/logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log"
  else
    echo "# SKIP (not found) logs/migrate_bb314e8f-3dfa-4230-8e71-0f095f9f3c2e.log"
  fi
fi

# Archive (ignored large): embeddings/embedder.py
mkdir -p revamp/archive/20251109/embeddings
if git ls-files --error-unmatch "embeddings/embedder.py" >/dev/null 2>&1; then
  echo "git mv -v 'embeddings/embedder.py' 'revamp/archive/20251109/embeddings/embedder.py'"; git mv -v "embeddings/embedder.py" "revamp/archive/20251109/embeddings/embedder.py"
else
  if [ -f "embeddings/embedder.py" ]; then
    echo "mv -v 'embeddings/embedder.py' 'revamp/archive/20251109/embeddings/embedder.py' && git add -A 'revamp/archive/20251109/embeddings/embedder.py'"; mv -v "embeddings/embedder.py" "revamp/archive/20251109/embeddings/embedder.py"; git add -A "revamp/archive/20251109/embeddings/embedder.py"
  else
    echo "# SKIP (not found) embeddings/embedder.py"
  fi
fi

# Archive (ignored large): logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log
mkdir -p revamp/archive/20251109/logs
if git ls-files --error-unmatch "logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log" >/dev/null 2>&1; then
  echo "git mv -v 'logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log' 'revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log'"; git mv -v "logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log" "revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log"
else
  if [ -f "logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log" ]; then
    echo "mv -v 'logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log' 'revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log' && git add -A 'revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log'"; mv -v "logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log" "revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log"; git add -A "revamp/archive/20251109/logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log"
  else
    echo "# SKIP (not found) logs/migrate_30c5d1d3-fec3-4bf4-adeb-274b2eb5e053.log"
  fi
fi

# Archive (ignored large): logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log
mkdir -p revamp/archive/20251109/logs
if git ls-files --error-unmatch "logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log" >/dev/null 2>&1; then
  echo "git mv -v 'logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log' 'revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log'"; git mv -v "logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log" "revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log"
else
  if [ -f "logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log" ]; then
    echo "mv -v 'logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log' 'revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log' && git add -A 'revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log'"; mv -v "logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log" "revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log"; git add -A "revamp/archive/20251109/logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log"
  else
    echo "# SKIP (not found) logs/migrate_71d40d4b-93e4-4db9-98ce-8601abe21188.log"
  fi
fi

# Archive (ignored large): logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log
mkdir -p revamp/archive/20251109/logs
if git ls-files --error-unmatch "logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log" >/dev/null 2>&1; then
  echo "git mv -v 'logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log' 'revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log'"; git mv -v "logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log" "revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log"
else
  if [ -f "logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log" ]; then
    echo "mv -v 'logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log' 'revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log' && git add -A 'revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log'"; mv -v "logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log" "revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log"; git add -A "revamp/archive/20251109/logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log"
  else
    echo "# SKIP (not found) logs/migrate_c7f4dfb1-0c7d-4b7b-9048-31cbe1d0d915.log"
  fi
fi

# Archive (ignored large): logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log
mkdir -p revamp/archive/20251109/logs
if git ls-files --error-unmatch "logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log" >/dev/null 2>&1; then
  echo "git mv -v 'logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log' 'revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log'"; git mv -v "logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log" "revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log"
else
  if [ -f "logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log" ]; then
    echo "mv -v 'logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log' 'revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log' && git add -A 'revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log'"; mv -v "logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log" "revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log"; git add -A "revamp/archive/20251109/logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log"
  else
    echo "# SKIP (not found) logs/migrate_bed39551-8669-4306-810a-a294fcd9b863.log"
  fi
fi

echo "Generated moves script completed."
echo "Inspect tools/do_moves.sh. To apply moves, run: bash tools/do_moves.sh"
echo "After applying, run tests, then git add -A && git commit -m 'chore(revamp): reorganize repo files' && git push origin revamp/organize-files"
