#!/usr/bin/env python3
"""
tools/generate_cleanup_candidates.py

Scan the repository and generate cleanup_candidates.json (analysis only).
It detects:
 - large tracked files
 - unreferenced scripts (python/shell)
 - logs outside /logs older than threshold
 - duplicate filenames (same basename in multiple paths)
 - docker/make warnings (naive checks)

Outputs: cleanup_candidates.json and cleanup_summary.txt in repo root.

Usage:
  python tools/generate_cleanup_candidates.py

Config via environment variables or CLI args (see code defaults).
"""
import os
import sys
import json
import subprocess
import argparse
import time
from datetime import datetime, timedelta
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run(cmd, cwd=REPO_ROOT):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p

def git_ls_files():
    p = run(["git", "ls-files"])
    if p.returncode != 0:
        print("Error: git ls-files failed:", p.stderr)
        sys.exit(1)
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]

def git_last_commit_info(path):
    # returns dict {commit_date, commit_hash, author}
    p = run(["git", "log", "-1", "--format=%ci|%H|%an", "--", path])
    if p.returncode != 0 or not p.stdout.strip():
        return {"commit_date": None, "commit_hash": None, "author": None}
    parts = p.stdout.strip().split("|")
    return {"commit_date": parts[0], "commit_hash": parts[1], "author": parts[2] if len(parts) > 2 else None}

def file_mtime(path):
    try:
        ts = os.path.getmtime(path)
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    except Exception:
        return None

def human_size(n):
    # bytes -> human readable
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def find_large_files(tracked_files, threshold_bytes):
    out = []
    for f in tracked_files:
        path = os.path.join(REPO_ROOT, f)
        # skip files missing from FS (submodules or deleted)
        if not os.path.isfile(path):
            continue
        size = os.path.getsize(path)
        if size >= threshold_bytes:
            info = git_last_commit_info(f)
            out.append({
                "path": f,
                "size_bytes": size,
                "size_human": human_size(size),
                "last_commit": info.get("commit_hash"),
                "last_commit_date": info.get("commit_date"),
                "last_commit_author": info.get("author"),
                "last_modified": file_mtime(path)
            })
    # sort desc
    out.sort(key=lambda x: x["size_bytes"], reverse=True)
    return out

def find_unreferenced_scripts(tracked_files, script_exts):
    # script_exts: e.g. [".py", ".sh", "Dockerfile", "Makefile"]
    candidates = []
    # build a quick map basename -> list(paths)
    basename_map = defaultdict(list)
    for f in tracked_files:
        basename = os.path.basename(f)
        basename_map[basename].append(f)

    scripts = [f for f in tracked_files if (os.path.splitext(f)[1] in script_exts or os.path.basename(f) in ["Dockerfile","Makefile"])]
    # For each script, run git grep for its basename excluding itself: if no other references, mark as candidate
    for s in scripts:
        base = os.path.basename(s)
        # run git grep for the basename; if the only matches are the file itself -> unreferenced
        p = run(["git", "grep", "-n", "--", base])
        matches = []
        if p.returncode == 0 and p.stdout.strip():
            for line in p.stdout.splitlines():
                try:
                    fname = line.split(":",1)[0]
                    matches.append(fname.strip())
                except Exception:
                    continue
        # remove matches equal to script path
        other_matches = [m for m in matches if os.path.normpath(m) != os.path.normpath(s)]
        if not other_matches:
            info = git_last_commit_info(s)
            candidates.append({
                "path": s,
                "basename": base,
                "last_commit_date": info.get("commit_date"),
                "last_commit": info.get("commit_hash"),
                "last_commit_author": info.get("author"),
                "note": "No references found via git grep (could be false positive if referenced by dynamic name)."
            })
    # sort by last commit (older first)
    def commit_time(x):
        return x.get("last_commit_date") or ""
    candidates.sort(key=commit_time)
    return candidates

def find_old_logs(tracked_files, days_threshold=180):
    out = []
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    for f in tracked_files:
        if not f.lower().endswith(".log"):
            continue
        # skip logs that are inside logs/ (we prefer logs/ motion later)
        if os.path.normpath(f).split(os.sep)[0] == "logs":
            continue
        path = os.path.join(REPO_ROOT, f)
        if not os.path.isfile(path):
            continue
        mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
        if mtime < cutoff:
            size = os.path.getsize(path)
            info = git_last_commit_info(f)
            out.append({
                "path": f,
                "last_modified": mtime.isoformat()+"Z",
                "days_old": (datetime.utcnow() - mtime).days,
                "size_bytes": size,
                "size_human": human_size(size),
                "last_commit": info.get("commit_hash"),
                "last_commit_date": info.get("commit_date")
            })
    out.sort(key=lambda x: x["days_old"], reverse=True)
    return out

def find_duplicates(tracked_files):
    by_name = defaultdict(list)
    for f in tracked_files:
        base = os.path.basename(f)
        by_name[base].append(f)
    duplicates = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    dup_list = []
    for name, paths in duplicates.items():
        # add last commit for each path
        items = []
        for p in paths:
            info = git_last_commit_info(p)
            items.append({
                "path": p,
                "last_commit_date": info.get("commit_date"),
                "last_commit": info.get("commit_hash")
            })
        dup_list.append({"basename": name, "paths": items})
    dup_list.sort(key=lambda x: x["basename"])
    return dup_list

def docker_make_warnings(tracked_files):
    # naive checks:
    warnings = []
    for f in tracked_files:
        if os.path.basename(f) in ("docker-compose.yml","docker-compose.yaml"):
            path = os.path.join(REPO_ROOT, f)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                if "version:" in content:
                    warnings.append({"path": f, "warning": "docker-compose 'version' field detected; modern docker-compose ignores this. Consider removing.", "note": "Review file"})
            except Exception:
                continue
        if os.path.basename(f) == "Makefile":
            # look for missing tabs or other common misconfig
            path = os.path.join(REPO_ROOT, f)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
                for i,l in enumerate(lines[:50]):
                    if "Makefile" in l:
                        continue
                # no further checks; placeholder
            except Exception:
                continue
    # also search for specific images / references (example ankane/pgvector)
    p = run(["git", "grep", "-n", "--", "pgvector"])
    if p.returncode == 0 and p.stdout.strip():
        for line in p.stdout.splitlines():
            parts = line.split(":",1)
            warnings.append({"path": parts[0], "warning":"Found 'pgvector' string; review postgres image references for platform compatibility.", "match_line": parts[1] if len(parts)>1 else ""})
    return warnings

def main(args):
    os.chdir(REPO_ROOT)
    print("Repo root:", REPO_ROOT)
    tracked = git_ls_files()
    print(f"Tracked files: {len(tracked)}")

    large = find_large_files(tracked, threshold_bytes=args.large_threshold)
    print(f"Large files found: {len(large)} (threshold {human_size(args.large_threshold)})")

    script_exts = {".py", ".sh", ".ps1", ".psm1", ".rb", ".pl"}
    unref = find_unreferenced_scripts(tracked, script_exts)
    print(f"Unreferenced scripts candidates: {len(unref)}")

    old_logs = find_old_logs(tracked, days_threshold=args.log_days)
    print(f"Old logs outside /logs older than {args.log_days} days: {len(old_logs)}")

    duplicates = find_duplicates(tracked)
    print(f"Duplicate basenames found: {len(duplicates)}")

    docker_warnings = docker_make_warnings(tracked)
    print(f"Docker/Make warnings: {len(docker_warnings)}")

    out = {
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "large_files_threshold_bytes": args.large_threshold,
        "log_days_threshold": args.log_days,
        "counts": {
            "tracked_files": len(tracked),
            "large_files": len(large),
            "unreferenced_scripts": len(unref),
            "old_logs": len(old_logs),
            "duplicates": len(duplicates),
            "docker_make_warnings": len(docker_warnings)
        },
        "large_files": large,
        "unreferenced_scripts": unref,
        "old_logs": old_logs,
        "duplicates": duplicates,
        "docker_make_warnings": docker_warnings
    }

    out_path = os.path.join(REPO_ROOT, "cleanup_candidates.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    summary_path = os.path.join(REPO_ROOT, "cleanup_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("Cleanup candidates summary\n")
        fh.write("=========================\n\n")
        fh.write(f"Generated: {out['generated_at']}\n\n")
        fh.write(f"Tracked files: {len(tracked)}\n")
        fh.write(f"Large files: {len(large)} (threshold {human_size(args.large_threshold)})\n")
        fh.write(f"Unreferenced scripts: {len(unref)}\n")
        fh.write(f"Old logs: {len(old_logs)}\n")
        fh.write(f"Duplicates: {len(duplicates)}\n")
        fh.write(f"Docker/Make warnings: {len(docker_warnings)}\n\n")
        fh.write("Top large files:\n")
        for it in large[:20]:
            fh.write(f" - {it['path']} {it['size_human']} last_commit={it['last_commit_date']}\n")
    print("Wrote:", out_path, summary_path)
    print("Done. Review cleanup_candidates.json and cleanup_summary.txt, then we will review and prepare archive plan.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--large-threshold-mb", type=float, default=10.0, help="Large file threshold in MB (default 10 MB)")
    parser.add_argument("--log-days", type=int, default=180, help="Older-than days threshold for logs (default 180)")
    args = parser.parse_args()
    args.large_threshold = int(args.large_threshold_mb * 1024 * 1024)
    main(args)
