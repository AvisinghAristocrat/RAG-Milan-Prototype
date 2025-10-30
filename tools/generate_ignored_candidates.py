#!/usr/bin/env python3
"""
tools/generate_ignored_candidates.py

Scan ignored directories (logs / data / models / exports / embeddings / etc)
and produce ignored_cleanup_candidates.json and ignored_cleanup_summary.txt.

Usage:
  python3 tools/generate_ignored_candidates.py \
     --dirs logs data exports models embeddings \
     --large-threshold-mb 50 --log-days 180
"""
import os, sys, json, argparse
from datetime import datetime, timedelta
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def human_size(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def file_info(path):
    try:
        st = os.stat(path)
        return {
            "path": os.path.relpath(path, REPO_ROOT),
            "size_bytes": st.st_size,
            "size_human": human_size(st.st_size),
            "last_modified": datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z"
        }
    except Exception as e:
        return {"path": path, "error": str(e)}

def scan_dirs(dirs, large_threshold_bytes, log_days):
    found = []
    cutoff = datetime.utcnow() - timedelta(days=log_days)
    for d in dirs:
        root = os.path.join(REPO_ROOT, d)
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                try:
                    st = os.stat(full)
                except Exception:
                    continue
                size = st.st_size
                mtime = datetime.utcfromtimestamp(st.st_mtime)
                rec = {
                    "path": os.path.relpath(full, REPO_ROOT),
                    "size_bytes": size,
                    "size_human": human_size(size),
                    "last_modified": mtime.isoformat()+"Z",
                }
                # flag large files
                rec["is_large"] = size >= large_threshold_bytes
                # flag old logs if extension .log or name contains "log"
                rec["is_log"] = fn.lower().endswith(".log") or "log" in fn.lower()
                if rec["is_log"]:
                    rec["is_old_log"] = (mtime < cutoff)
                    rec["days_old"] = (datetime.utcnow() - mtime).days
                else:
                    rec["is_old_log"] = False
                    rec["days_old"] = None
                found.append(rec)
    return found

def find_duplicates(found):
    by_basename = defaultdict(list)
    for rec in found:
        base = os.path.basename(rec["path"])
        by_basename[base].append(rec)
    dups = []
    for base, items in by_basename.items():
        if len(items) > 1:
            dups.append({
                "basename": base,
                "count": len(items),
                "paths": [{"path": i["path"], "size_human": i["size_human"], "last_modified": i["last_modified"]} for i in items]
            })
    return dups

def top_large(found, n=20):
    items = sorted(found, key=lambda r: r["size_bytes"], reverse=True)
    return items[:n]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dirs", nargs="+", default=["logs","data","exports","models","embeddings"], help="Dirs to scan (relative to repo root)")
    parser.add_argument("--large-threshold-mb", type=float, default=50.0, help="Large file threshold in MB")
    parser.add_argument("--log-days", type=int, default=180, help="Days threshold for old logs")
    args = parser.parse_args()

    large_threshold_bytes = int(args.large_threshold_mb * 1024 * 1024)
    print("Repo root:", REPO_ROOT)
    print("Scanning dirs:", args.dirs)
    print("Large threshold (bytes):", large_threshold_bytes)
    all_found = scan_dirs(args.dirs, large_threshold_bytes, args.log_days)
    duplicates = find_duplicates(all_found)
    top = top_large(all_found, n=50)
    stats = {
        "scanned_dirs": args.dirs,
        "total_found": len(all_found),
        "large_threshold_bytes": large_threshold_bytes,
        "large_threshold_human": human_size(large_threshold_bytes),
        "log_days": args.log_days,
        "num_duplicates": len(duplicates)
    }
    out = {
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "stats": stats,
        "items": all_found,
        "duplicates": duplicates,
        "top_large": top
    }
    out_path = os.path.join(REPO_ROOT, "ignored_cleanup_candidates.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    summary = os.path.join(REPO_ROOT, "ignored_cleanup_summary.txt")
    with open(summary, "w", encoding="utf-8") as fh:
        fh.write("Ignored cleanup summary\n")
        fh.write("======================\n\n")
        fh.write(f"Generated: {out['generated_at']}\n\n")
        fh.write(json.dumps(stats, indent=2))
        fh.write("\n\nTop large files:\n")
        for t in top[:30]:
            fh.write(f" - {t['path']} {t['size_human']} last_modified={t['last_modified']}\n")
    print("Wrote:", out_path, summary)
    print("Done - please review ignored_cleanup_candidates.json and ignored_cleanup_summary.txt")

if __name__ == "__main__":
    from datetime import datetime
    main()
