import requests
from typing import List, Dict, Tuple
import base64

def test_connection(token: str) -> Tuple[bool, str]:
    if not token:
        return False, "missing token"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if r.status_code == 200:
        return True, r.json().get("login")
    return False, f"{r.status_code}: {r.text[:200]}"

def fetch_repo_docs(repo_full: str, token: str, branch: str = "main") -> List[Dict]:
    """Fetch markdown/text files from a repo. Returns list of {path, url, content}"""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    owner, repo = repo_full.split("/")
    # get tree recursively
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1", headers=headers, timeout=30)
    r.raise_for_status()
    tree = r.json().get("tree", [])
    docs = []
    for item in tree:
        if item["type"] == "blob" and any(item["path"].lower().endswith(ext) for ext in [".md", ".txt", ".rst"]):
            # fetch contents
            r2 = requests.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{item['path']}?ref={branch}", headers=headers, timeout=30)
            if r2.status_code != 200:
                continue
            data = r2.json()
            content = ""
            if data.get("encoding") == "base64" and "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            else:
                content = data.get("content", "")
            docs.append({"path": item["path"], "url": data.get("html_url"), "content": content})
    return docs
