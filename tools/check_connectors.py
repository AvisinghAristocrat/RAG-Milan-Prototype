#!/usr/bin/env python3
# tools/check_connectors.py
import os, sys, json
import requests

def check_github(token):
    if not token:
        return ("MISSING", "GITHUB_TOKEN not set")
    headers = {"Authorization": f"token {token}", "Accept":"application/json"}
    try:
        r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return ("OK", f"user={data.get('login')}")
        else:
            return ("FAIL", f"status={r.status_code} msg={r.text[:200]}")
    except Exception as e:
        return ("ERROR", str(e))

def check_confluence(base_url, username, token):
    if not base_url or not username or not token:
        return ("MISSING", "CONFLUENCE_BASE_URL/USERNAME/TOKEN not set")
    url = base_url.rstrip("/") + "/rest/api/space?limit=1"
    try:
        r = requests.get(url, auth=(username, token), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return ("OK", f"spaces_found={len(data.get('results', []))}")
        else:
            return ("FAIL", f"status={r.status_code} msg={r.text[:200]}")
    except Exception as e:
        return ("ERROR", str(e))

def check_gdrive(creds_path):
    if not creds_path:
        return ("MISSING", "GDRIVE_CREDENTIALS_JSON not set")
    if not os.path.exists(creds_path):
        return ("FAIL", f"file not found: {creds_path}")
    try:
        with open(creds_path, "r") as fh:
            js = json.load(fh)
        email = js.get("client_email") or js.get("installed",{}).get("client_email")
        return ("OK", f"creds_present client_email={email}")
    except Exception as e:
        return ("ERROR", str(e))

def main():
    GH = os.environ.get("GITHUB_TOKEN")
    CONF_BASE = os.environ.get("CONFLUENCE_BASE_URL")
    CONF_USER = os.environ.get("CONFLUENCE_USERNAME")
    CONF_TOKEN = os.environ.get("CONFLUENCE_TOKEN")
    GDRIVE = os.environ.get("GDRIVE_CREDENTIALS_JSON")

    print("GitHub: ", *check_github(GH))
    print("Confluence:", *check_confluence(CONF_BASE, CONF_USER, CONF_TOKEN))
    print("Google Drive:", *check_gdrive(GDRIVE))

if __name__ == "__main__":
    main()
