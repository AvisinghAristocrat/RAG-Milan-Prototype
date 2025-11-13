#!/usr/bin/env python3
"""
tools/apply_archive.py

Usage:
  source .venv/bin/activate
  python tools/apply_archive.py --date 20251103 --branch revamp/organize-work --dry-run
  python tools/apply_archive.py --date 20251103 --branch revamp/organize-work --apply

This script:
 - verifies git branch and working tree is clean (unless --allow-dirty)
 - reads files_to_archive.txt and files_to_move_plan.txt
 - prints dry-run commands by default
 - with --apply executes git mv commands and commits the result

SAFETY: this will not delete anything and uses 'git mv' to preserve history.
"""
import argparse
import os
import subprocess
import sys

def run(cmd, check=True):
    print("> " + " ".join(cmd))
    return subprocess.run(cmd, check=(check))

def check_clean(allow_dirty=False):
    p = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True, check=True)
    if p.stdout.strip() and not allow_dirty:
        print("Git working tree is not clean. Please commit/stash changes or run with --allow-dirty.", file=sys.stderr)
        print(p.stdout)
        sys.exit(2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--branch", default="revamp/organize-work")
    parser.add_argument("--dry-run", action="store_true", help="Only show planned git mv commands")
    parser.add_argument("--apply", action="store_true", help="Apply the moves (git mv + commit)")
    parser.add_argument("--yes", action="store_true", help="Assume YES for confirmations")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow a dirty working tree")
    args = parser.parse_args()

    DATE = args.date
    ARCH_ROOT = os.path.join("revamp","archive",DATE,"backup")

    # check branch
    p = subprocess.run(["git","rev-parse","--abbrev-ref","HEAD"], capture_output=True, text=True, check=True)
    cur_branch = p.stdout.strip()
    if cur_branch != args.branch:
        print(f"Warning: current git branch is '{cur_branch}', expected '{args.branch}'")
        # continue but warn

    check_clean(allow_dirty=args.allow_dirty)

    # read lists
    if not os.path.exists("files_to_archive.txt") and not os.path.exists("files_to_move_plan.txt"):
        print("Error: files_to_archive.txt and files_to_move_plan.txt not found. Run tools/prepare_archive.py first.", file=sys.stderr)
        sys.exit(1)

    with open("files_to_archive.txt","r",encoding="utf-8") as fh:
        archives = [l.strip() for l in fh if l.strip()]

    move_plan = []
    if os.path.exists("files_to_move_plan.txt"):
        with open("files_to_move_plan.txt","r",encoding="utf-8") as fh:
            for line in fh:
                if "->" in line:
                    src,dst = [p.strip() for p in line.split("->",1)]
                    move_plan.append((src,dst))

    # build commands
    archive_cmds=[]
    for f in archives:
        dst = os.path.join(ARCH_ROOT, f)
        archive_cmds.append( (f, dst) )

    move_cmds = move_plan

    # Dry-run output
    print("===== DRY-RUN: planned operations =====")
    if archive_cmds:
        print("Archive moves (git mv source -> revamp/archive/...):")
        for src, dst in archive_cmds:
            print(f"mkdir -p \"{os.path.dirname(dst)}\" && git mv \"{src}\" \"{dst}\"")
    else:
        print("No archive moves.")

    if move_cmds:
        print("\nMove plan (git mv source -> dest):")
        for src, dst in move_cmds:
            print(f"mkdir -p \"{os.path.dirname(dst)}\" && git mv \"{src}\" \"{dst}\"")
    else:
        print("No move plan entries.")

    if args.dry_run and not args.apply:
        print("\nDry-run complete. To apply run with --apply")
        sys.exit(0)

    if not args.apply:
        print("\nNo --apply flag specified. Exiting.")
        sys.exit(0)

    # confirm
    if not args.yes:
        ans = input("Proceed to apply moves? Type YES to proceed: ").strip()
        if ans != "YES":
            print("Aborting.")
            sys.exit(0)

    # Apply archive moves
    for src, dst in archive_cmds:
        if not os.path.exists(src):
            print(f"Warning: source missing: {src} - skipping")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        run(["git","mv", src, dst])

    # Apply move plan
    for src, dst in move_cmds:
        if not os.path.exists(src):
            print(f"Warning: source missing: {src} - skipping")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        run(["git","mv", src, dst])

    # Commit
    commit_msg = f"Revamp: archive and reorganize files (archive date: {DATE})"
    run(["git","add","-A"])
    run(["git","commit","-m", commit_msg])

    print("Applied moves and committed. Push to origin when ready:")
    print(f"  git push origin {args.branch}")

if __name__ == "__main__":
    main()
