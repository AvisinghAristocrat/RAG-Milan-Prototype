# mcp/mcp.py
import json
from typing import List, Dict
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("mcp_logs.jsonl")

def assemble_mcp_context(query: str, chunks: List[Dict], max_chunks: int = 5) -> Dict:
    """
    Build a single string context (and metadata) to feed the LLM.
    chunks: list of dicts with keys: chunk_text, score, title, url
    Returns:
      { "context_str": "...", "metadata": {...} }
    """
    top = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:max_chunks]
    parts = []
    for i, c in enumerate(top, start=1):
        title = c.get("title") or c.get("meta", {}).get("title", "unknown")
        url = c.get("url") or c.get("meta", {}).get("url", "")
        header = f"SOURCE {i}: {title} | {url}"
        parts.append(header)
        parts.append(c.get("chunk_text", ""))
        parts.append("")  # spacer

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
        "num_chunks": len(top),
        "chunks": [{"title": c.get("title"), "url": c.get("url"), "score": c.get("score")} for c in top]
    }
    return {"context_str": full_prompt, "metadata": metadata}

def log_mcp(metadata: Dict, log_path: str = None):
    """Append one JSONL line with metadata for auditing."""
    p = Path(log_path) if log_path else LOG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(metadata) + "\n")
