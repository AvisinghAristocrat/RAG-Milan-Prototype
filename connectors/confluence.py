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

# connectors/confluence.py  (partial file - replace fetch_pages and helper)
import requests
from typing import List, Dict, Optional

def _normalize_page(item: Dict, base_url: str) -> Dict:
    """
    Normalize a Confluence content item into the dict expected by ingesters:
      { id, title, url, content, meta }
    content will prefer body.view -> body.export_view -> body.storage
    """
    body = item.get("body", {}) or {}
    # prefer rendered HTML (view / export_view), then storage
    content = ""
    if isinstance(body.get("view"), dict):
        content = body["view"].get("value") or ""
    if not content and isinstance(body.get("export_view"), dict):
        content = body["export_view"].get("value") or ""
    if not content and isinstance(body.get("storage"), dict):
        content = body["storage"].get("value") or ""

    meta = {"version": item.get("version")} if item.get("version") else {}
    page_url = f"{base_url.rstrip('/')}/pages/{item.get('id')}"
    return {
        "id": str(item.get("id")),
        "title": item.get("title"),
        "url": page_url,
        "content": content,
        "meta": meta,
    }


def fetch_pages(base_url: str, username: str, token: str,
                space_key: Optional[str] = None, page_id: Optional[str] = None,
                limit: int = 100, max_docs: Optional[int] = None) -> List[Dict]:
    """
    Return list of pages (id, title, url, content, meta) for a space OR a page subtree.
    If page_id is provided, we return the page itself + all descendants (via CQL ancestor).
    Pagination is handled for large spaces/subtrees.
    """
    sess = requests.Session()
    sess.auth = (username, token)
    sess.headers.update({"Accept": "application/json"})

    pages: List[Dict] = []
    try:
        base = base_url.rstrip("/")

        # If a single page was requested, fetch it first
        if page_id:
            r = sess.get(f"{base}/rest/api/content/{page_id}", params={"expand": "body.storage,body.view,body.export_view,version"}, timeout=30)
            r.raise_for_status()
            pages.append(_normalize_page(r.json(), base))

            # Now fetch descendants via CQL ancestor=PAGE_ID using /rest/api/content/search
            start = 0
            page_size = limit or 50
            while True:
                params = {
                    "cql": f"ancestor={page_id}",
                    "start": start,
                    "limit": page_size,
                    "expand": "body.storage,body.view,body.export_view,version"
                }
                r = sess.get(f"{base}/rest/api/content/search", params=params, timeout=60)
                r.raise_for_status()
                j = r.json()
                results = j.get("results", [])
                for item in results:
                    pages.append(_normalize_page(item, base))
                    if max_docs and len(pages) >= max_docs:
                        return pages[:max_docs]
                size = j.get("size", len(results))
                total = j.get("total", len(results))
                if size == 0 or (start + size) >= total:
                    break
                start += size

        elif space_key:
            # Fetch pages in a space (paginated)
            start = 0
            page_size = limit or 50
            while True:
                params = {
                    "spaceKey": space_key,
                    "start": start,
                    "limit": page_size,
                    "expand": "body.storage,body.view,body.export_view,version"
                }
                r = sess.get(f"{base}/rest/api/content", params=params, timeout=60)
                r.raise_for_status()
                j = r.json()
                results = j.get("results", [])
                for item in results:
                    pages.append(_normalize_page(item, base))
                    if max_docs and len(pages) >= max_docs:
                        return pages[:max_docs]
                size = j.get("size", len(results))
                total = j.get("total", len(results))
                if size == 0 or (start + size) >= total:
                    break
                start += size

        else:
            raise ValueError("Provide space_key or page_id")

    except requests.HTTPError as e:
        # include body to give helpful error messages
        body = e.response.text if e.response is not None else ""
        raise Exception(f"Confluence HTTP error: {e} - {body}")
    except Exception as e:
        raise

    return pages
