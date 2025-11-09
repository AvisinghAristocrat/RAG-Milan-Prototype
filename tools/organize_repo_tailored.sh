#!/usr/bin/env bash
# tools/organize_repo_tailored.sh
# Generates tools/do_moves.sh to reorganize floating files into canonical layout.
# DOES NOT PERFORM MOVES ITSELF. Review do_moves.sh before executing it.
set -euo pipefail

ROOT="$(pwd)"
ARCH_DIR="revamp/archive/$(date +%Y%m%d)"
OUT="./tools/do_moves.sh"

# Mapping lines: "source|destination"
MAP_CONTENT=$(cat <<'MAP'
create_milan_repo.sh|scripts/create_milan_repo.sh
README_DATA.md|docs/README_DATA.md
APP_WORKFLOW.md|docs/APP_WORKFLOW.md
cleanup_candidates.json|tools/reports/cleanup_candidates.json
ignored_cleanup_candidates.json|tools/reports/ignored_cleanup_candidates.json
ignored_cleanup_summary.txt|tools/reports/ignored_cleanup_summary.txt
cleanup_candidates_review.md|docs/cleanup_candidates_review.md
tools/test_insert_chunk.py|tools/test_insert_chunk.py
tools/collect_pages_ids.py|tools/collect_pages_ids.py
MAP
)

# helper: lookup mapping (returns destination or empty)
get_mapped_dest() {
  local src="$1"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    key="${line%%|*}"
    val="${line#*|}"
    if [ "$key" = "$src" ]; then
      printf "%s" "$val"
      return 0
    fi
  done <<< "$MAP_CONTENT"
  return 1
}

# Prepare output
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
cat > "$OUT" <<'BASHHEAD'
#!/usr/bin/env bash
set -euo pipefail
echo "This script will execute the generated moves (git mv / mv / git add etc)."
echo "PLEASE REVIEW tools/do_moves.sh carefully before running."
echo
BASHHEAD

echo "# --- generated on $(date) ---" >> "$OUT"
echo "" >> "$OUT"

# helper to append commands to OUT (write commands, do NOT run them now)
append_move_cmds() {
  local src="$1"
  local dst="$2"
  local dstdir
  dstdir="$(dirname "$dst")"
  {
    echo ""
    echo "# Move: $src -> $dst"
    echo "mkdir -p '$dstdir'"
    echo "if git ls-files --error-unmatch '$src' >/dev/null 2>&1; then"
    echo "  echo 'git mv -v \"$src\" \"$dst\"'"
    echo "  git mv -v \"$src\" \"$dst\""
    echo "else"
    echo "  if [ -f '$src' ]; then"
    echo "    echo 'mv -v \"$src\" \"$dst\" && git add -A \"$dst\"'"
    echo "    mv -v '$src' '$dst'"
    echo "    git add -A '$dst'"
    echo "  else"
    echo "    echo \"# SKIP: source '$src' not found\""
    echo "  fi"
    echo "fi"
  } >> "$OUT"
}

# 1) Root-level files
echo "# --- root-level file moves ---" >> "$OUT"
# find root-level files (non-dirs)
# portable find usage for mac and linux
while IFS= read -r f; do
  # skip meta files we want to keep
  case "$f" in
    .|..|.git|.gitignore|README.md|LICENSE|.pre-commit-config.yaml|.secrets.baseline|tasks.json)
      echo "# keep $f" >> "$OUT"
      continue
      ;;
  esac
  dest="$(get_mapped_dest "$f" || true)"
  if [ -n "$dest" ]; then
    append_move_cmds "$f" "$dest"
  else
    append_move_cmds "$f" "tools/$f"
  fi
done < <(find . -maxdepth 1 -type f -print | sed 's#^\./##' | sort)

# 2) Stray files (depth <= 3) not in canonical dirs
echo "" >> "$OUT"
echo "# --- stray files deeper in tree (depth <= 3) ---" >> "$OUT"

# build a find-exclusion list of canonical dirs
EXCLUDE="
./.git
./tools
./api
./ui
./connectors
./ingesters
./mcp
./embeddings
./storage
./migrations
./docs
./revamp
./data
./logs
./models
./tests
"

# find files and filter
find . -type f -maxdepth 3 | sed 's#^\./##' | sort | while IFS= read -r file; do
  skip=false
  for ex in $EXCLUDE; do
    # trim whitespace
    ex=$(echo "$ex" | tr -d '[:space:]')
    case "$file" in
      "$ex"/*) skip=true; break ;;
    esac
  done
  $skip && continue
  ext="${file##*.}"
  case "$ext" in
    sh|py|ps1|js)
      append_move_cmds "$file" "tools/$file"
      ;;
    md|txt)
      append_move_cmds "$file" "docs/notes/$file"
      ;;
    json)
      # heuristic: send reports to tools/reports, others to data/curated/misc
      if echo "$file" | grep -Ei "(cleanup|ignored|report|eval|ann|fusion|analysis)" >/dev/null 2>&1; then
        append_move_cmds "$file" "tools/reports/$file"
      else
        append_move_cmds "$file" "data/curated/misc/$file"
      fi
      ;;
    csv)
      append_move_cmds "$file" "$ARCH_DIR/$file"
      ;;
    *)
      # skip/leave for manual review
      echo "# NOTE: review $file (unhandled ext $ext) -- skip" >> "$OUT"
      ;;
  esac
done

# 3) Archive large ignored files from ignored_cleanup_candidates.json
if [ -f ignored_cleanup_candidates.json ]; then
  echo "" >> "$OUT"
  echo "# --- archive large/ignored files from ignored_cleanup_candidates.json ---" >> "$OUT"
  # use Python to safely iterate top_large entries and print commands
  python3 - <<PY >> "$OUT"
import json, os, sys
arch = os.environ.get('ARCH_DIR', '${ARCH_DIR}')
try:
    j = json.load(open('ignored_cleanup_candidates.json'))
except Exception:
    sys.exit(0)
for item in j.get('top_large', []):
    p = item['path']
    # python's print, ensure p is handled safely
    dirp = os.path.dirname(p) or "."
    print('')
    print("# Archive (ignored large): {p}".format(p=p))
    print("mkdir -p {arch}/{dirp}".format(arch=arch, dirp=dirp))
    print('if git ls-files --error-unmatch "{p}" >/dev/null 2>&1; then'.format(p=p))
    print('  echo "git mv -v \\'{p}\\' \\'{arch}/{p}\\'"; git mv -v "{p}" "{arch}/{p}"'.format(p=p, arch=arch))
    print('else')
    print('  if [ -f "{p}" ]; then'.format(p=p))
    print('    echo "mv -v \\'{p}\\' \\'{arch}/{p}\\' && git add -A \\'{arch}/{p}\\'"; mv -v "{p}" "{arch}/{p}"; git add -A "{arch}/{p}"'.format(p=p, arch=arch))
    print('  else')
    print('    echo "# SKIP (not found) {p}"'.format(p=p))
    print('  fi')
    print('fi')
PY
fi

# footer
cat >> "$OUT" <<'BASHFOOT'

echo "Generated moves script completed."
echo "Inspect tools/do_moves.sh. To apply moves, run: bash tools/do_moves.sh"
echo "After applying, run tests, then git add -A && git commit -m 'chore(revamp): reorganize repo files' && git push origin revamp/organize-files"
BASHFOOT

chmod +x "$OUT"
echo "WROTE: $OUT"
echo "Preview (first 80 lines):"
sed -n '1,80p' "$OUT"
