#!/usr/bin/env python3
# collect_pages_ids.py
import argparse
import json
import os
import sys
import requests

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", default=os.getenv("API_URL", "http://localhost:8000"), help="API base URL")
    p.add_argument("--space", help="Confluence space key")
    p.add_argument("--page", help="Confluence page id")
    p.add_argument("--out", default="collected_pages.json", help="Output JSON file")
    args = p.parse_args()

    if not (args.space or args.page):
        print("Provide --space or --page", file=sys.stderr)
        sys.exit(2)

    payload = {"space_key": args.space, "page_id": args.page}
    url = args.api.rstrip("/") + "/confluence/page_ids"
    print(f"Calling {url} with payload {payload}")
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        sys.exit(1)

    data = r.json()
    pages = data.get("pages", [])
    print(f"Collected {len(pages)} pages")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(pages, fh, indent=2)
    print("Saved to", args.out)

if __name__ == "__main__":
    main()
