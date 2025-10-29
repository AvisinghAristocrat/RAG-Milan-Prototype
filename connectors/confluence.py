# connectors/confluence.py (replace existing fetch_pages)
import requests
from typing import List, Dict, Tuple, Optional

def test_connection(base_url: str, username: str, token: str) -> Tuple[bool, str]:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/rest/api/space?limit=1", auth=(username, token), timeout=10)
        if r.status_code == 200:
            return True, "ok"
        return False, f"{r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def fetch_pages(base_url: str, username: str, token: str,
                space_key: Optional[str] = None, page_id: Optional[str] = None,
                limit: int = 100, max_docs: Optional[int] = None) -> List[Dict]:
    """
    Paginated fetch of Confluence pages.
    If space_key is provided: fetch all pages in the space using paging (limit per request).
    If page_id is provided: fetch the single page (or use CQL for descendants).
    max_docs: if set, stop after collecting up to max_docs pages (useful for tests).
    """
    sess = requests.Session()
    sess.auth = (username, token)

    pages: List[Dict] = []

    if space_key:
        start = 0
        while True:
            url = (
                f"{base_url.rstrip('/')}/rest/api/content"
                f"?spaceKey={space_key}&limit={limit}&start={start}&expand=body.storage,version"
            )
            r = sess.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            for item in results:
                content = item.get("body", {}).get("storage", {}).get("value", "")
                pages.append({
                    "id": item["id"],
                    "title": item.get("title"),
                    "url": f'{base_url.rstrip("/")}/pages/{item["id"]}',
                    "content": content,
                    "meta": {"version": item.get("version"), "space": space_key}
                })
                # stop early if max_docs requested
                if max_docs is not None and len(pages) >= max_docs:
                    return pages
            # paging: if fewer items than limit, we are done
            if len(results) < limit:
                break
            start += limit
    elif page_id:
        url = f"{base_url.rstrip('/')}/rest/api/content/{page_id}?expand=body.storage"
        r = sess.get(url, timeout=30)
        r.raise_for_status()
        item = r.json()
        content = item.get("body", {}).get("storage", {}).get("value", "")
        pages.append({
            "id": item["id"],
            "title": item.get("title"),
            "url": f'{base_url.rstrip("/")}/pages/{item["id"]}',
            "content": content,
            "meta": {"version": item.get("version")}
        })
    else:
        raise ValueError("space_key or page_id must be provided")
    return pages
