#!/usr/bin/env python3
"""
tools/prepare_archive.py

Usage:
  source .venv/bin/activate
  python tools/prepare_archive.py \
    --cleanup cleanup_candidates.json \
    --date 20251103 \
    --branch revamp/organize-work \
    [--commit]

This will:
 - build files_to_archive.txt, files_to_data.txt, files_to_logs.txt
 - build files_to_move_plan.txt (default move plan for create_milan_repo.sh and test script)
 - create revamp/archive/<DATE>/backup_manifest.json (audit info)
 - optionally commit the generated lists + manifest

IMPORTANT: this does NOT move any files.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

def git_last_commit(path):
    try:
        p = subprocess.run(["git", "log", "-1", "--format=%H|%ci|%an", "--", path],
                           capture_output=True, text=True, check=True)
        return p.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_list(path, lines):
    with open(path, "w", encoding="utf-8") as fh:
        for l in sorted(set([x for x in lines if x])):
            fh.write(l + "\n")

def gather_manifest_entries(paths, archive_root):
    items=[]
    for p in sorted(set([x for x in paths if x])):
        if not os.path.exists(p):
            # still record but warning
            items.append({"orig_path":p, "exists": False})
            continue
        size = os.path.getsize(p)
        mtime = datetime.utcfromtimestamp(os.path.getmtime(p)).isoformat()+"Z"
        commit = git_last_commit(p)
        archive_path = os.path.join(archive_root, p)
        items.append({
            "orig_path": p,
            "archive_path": archive_path,
            "size_bytes": size,
            "size_human": f"{size/1024/1024:.1f} MB",
            "last_commit": commit,
            "last_modified": mtime,
            "exists": True
        })
    return items

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", default="cleanup_candidates.json")
    parser.add_argument("--date", default=None, help="YYYYMMDD (defaults to today)")
    parser.add_argument("--branch", default="revamp/organize-work")
    parser.add_argument("--commit", action="store_true", help="Commit the generated files")
    parser.add_argument("--no-default-moves", action="store_true", help="Don't add default move plan")
    args = parser.parse_args()

    if not os.path.exists(args.cleanup):
        print(f"Error: cleanup file {args.cleanup} not found", file=sys.stderr)
        sys.exit(2)

    if args.date:
        DATE = args.date
    else:
        DATE = datetime.utcnow().strftime("%Y%m%d")
    ARCH_ROOT = os.path.join("revamp", "archive", DATE, "backup")
    ensure_dir(ARCH_ROOT)

    # Load cleanup JSON
    with open(args.cleanup, "r", encoding="utf-8") as fh:
        cj = json.load(fh)

    # Build lists
    large_files = [ item["path"] for item in cj.get("large_files", []) if item.get("path") ]
    unref_scripts = [ item["path"] for item in cj.get("unreferenced_scripts", []) if item.get("path") ]
    duplicates = cj.get("duplicates", [])

    files_to_archive = list(large_files)
    # By default do not archive unreferenced scripts; leave for review.
    # But we will produce a file_to_move_plan with recommended moves:
    files_to_data = []  # none by default
    files_to_logs = []  # none by default

    # Default move plan (we discussed these)
    move_plan = []
    if not args.no_default_moves:
        # move create_milan_repo.sh -> scripts/create_milan_repo.sh (if exists)
        if os.path.exists("create_milan_repo.sh"):
            move_plan.append(("create_milan_repo.sh", "scripts/create_milan_repo.sh"))
        # move test script
        if os.path.exists("tools/test_insert_chunk.py"):
            move_plan.append(("tools/test_insert_chunk.py", "tools/tests/test_insert_chunk.py"))

    # Write lists
    write_list("files_to_archive.txt", files_to_archive)
    write_list("files_to_data.txt", files_to_data)
    write_list("files_to_logs.txt", files_to_logs)

    # Write move plan
    with open("files_to_move_plan.txt", "w", encoding="utf-8") as fh:
        for src, dst in move_plan:
            fh.write(f"{src} -> {dst}\n")

    # Build manifest for archive + move-src
    paths_for_manifest = files_to_archive + [src for src, dst in move_plan]
    manifest_entries = gather_manifest_entries(paths_for_manifest, ARCH_ROOT)
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": DATE,
        "items": manifest_entries,
        "notes": {
            "files_to_archive": len(files_to_archive),
            "move_plan_count": len(move_plan),
            "unreferenced_scripts_count": len(unref_scripts),
            "duplicates_count": len(duplicates)
        },
        "source_cleanup": os.path.abspath(args.cleanup)
    }
    manifest_path = os.path.join("revamp", "archive", DATE, "backup_manifest.json")
    ensure_dir(os.path.dirname(manifest_path))
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Wrote manifest: {manifest_path}")
    print(f"Wrote files_to_archive.txt ({len(files_to_archive)})")
    print(f"Wrote files_to_move_plan.txt ({len(move_plan)})")
    print("If you want different mappings, edit files_to_move_plan.txt or files_to_archive.txt, then run apply script.")

    if args.commit:
        # check branch
        p = subprocess.run(["git","rev-parse","--abbrev-ref","HEAD"], capture_output=True, text=True)
        branch = p.stdout.strip()
        if branch != args.branch:
            print(f"Warning: current branch is '{branch}', expected '{args.branch}'. Aborting commit.", file=sys.stderr)
        else:
            subprocess.run(["git","add","files_to_archive.txt","files_to_data.txt","files_to_logs.txt","files_to_move_plan.txt", manifest_path])
            subprocess.run(["git","commit","-m", f"Add archive manifest + lists for revamp archive {DATE}"])
            print("Committed manifest and lists. Push when ready: git push origin", args.branch)

if __name__ == "__main__":
    main()
