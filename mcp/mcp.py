# mcp/mcp.py
import json
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import re
import hashlib

MAX_CHUNK_CHARS = 1200  # per chunk cap (tune as needed)

def _trim_text(s: str, limit: int = MAX_CHUNK_CHARS) -> str:
    s = (s or "").strip()
    if len(s) <= limit:
        return s
    return s[:limit].rstrip() + "\n...[truncated]"

def _dedupe_key(title: str, url: str, chunk_text: str) -> str:
    # stable key even if title/url missing; avoids repeated chunks
    base = f"{title or ''}|{url or ''}|{(chunk_text or '')[:200]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

LOG_PATH = Path("mcp_logs.jsonl")

def assemble_mcp_context(query: str, chunks: List[Dict], max_chunks: int = 5, min_score: float = 0.15) -> Dict:
    """
    Build a single string context (and metadata) to feed the LLM.
    chunks: list of dicts with keys: chunk_text, score, title, url
    Returns:
      { "context_str": "...", "metadata": {...} }
    """
    ranked = sorted(chunks, key=lambda x: float(x.get("score") or x.get("fused_score") or 0.0), reverse=True)

    parts = []
    seen = set()
    kept = 0
    kept_chunks = []

    for c in ranked:
        if kept >= max_chunks:
            break

        score = float(c.get("score") or c.get("fused_score") or 0.0)
        if score < min_score:
            continue

        title = c.get("title") or c.get("meta", {}).get("title", "unknown")
        url = c.get("url") or c.get("meta", {}).get("url", "")

        raw = c.get("chunk_text", "") or ""
        chunk_text = _trim_text(raw, MAX_CHUNK_CHARS).strip()
        if not chunk_text:
            continue

        k = _dedupe_key(title, url, chunk_text)
        if k in seen:
            continue
        seen.add(k)

        header = f"SOURCE {kept+1}: {title} | {url}".strip()
        parts.append(header)
        parts.append(chunk_text)
        parts.append("")  # spacer

        kept_chunks.append({"title": title, "url": url, "score": score})
        kept += 1

    context_text = "\n---\n".join(parts)
    instruction = (
        "You are given context chunks below with SOURCE headers. "
        "Answer the query concisely using only the provided context. "
        "If the answer cannot be found, say 'I don't know'. "
        "Include citations using the SOURCE lines."
    )
    full_prompt = f"{instruction}\n\nCONTEXT:\n{context_text}\n\nQUERY: {query}\n\nAnswer:"
    metadata = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "num_chunks": kept,
        "chunks": [
            {
                "title": (c.get("title") or c.get("meta", {}).get("title")),
                "url": (c.get("url") or c.get("meta", {}).get("url")),
                "score": float(c.get("score") or c.get("fused_score") or 0.0),
            }
            for c in ranked[:kept]
        ],
    }
    return {"context_str": full_prompt, "metadata": metadata}

def log_mcp(metadata: Dict, log_path: str = None):
    """Append one JSONL line with metadata for auditing."""
    p = Path(log_path) if log_path else LOG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(metadata) + "\n")
