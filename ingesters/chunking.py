# ingesters/chunking.py
from __future__ import annotations
import os
import re
from typing import Dict, List, Optional

# Reuse your existing doc chunker for prose content
from ingesters.github_ingest import chunk_file as chunk_doc_paragraph_windows

LANG_BY_EXT = {
    ".cs": "csharp",
    ".ts": "typescript",
    ".js": "javascript",
    ".py": "python",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".md": "markdown",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
}

CODE_EXTS = set(LANG_BY_EXT.keys())

def guess_language(file_path: str) -> str:
    _, ext = os.path.splitext(file_path.lower())
    return LANG_BY_EXT.get(ext, "text")

def chunk_code_by_lines(
    content: str,
    max_chars: int = 1800,
    overlap_lines: int = 10,
) -> List[Dict]:
    """
    Code chunking: preserve indentation and contiguous blocks.
    Strategy: accumulate lines up to max_chars; slide window by overlap_lines.
    """
    if not content:
        return []

    # Normalize newlines but preserve indentation
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.split("\n")

    chunks: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        buf: List[str] = []
        size = 0
        j = i

        while j < n:
            line = lines[j]
            # +1 for newline
            add = len(line) + 1
            if buf and size + add > max_chars:
                break
            buf.append(line)
            size += add
            j += 1

        # If a single line is longer than max_chars, hard-split it
        if not buf and i < n:
            long_line = lines[i]
            for k in range(0, len(long_line), max_chars):
                chunks.append(long_line[k:k + max_chars])
            i += 1
            continue

        chunk_text = "\n".join(buf).strip()
        if chunk_text:
            chunks.append(chunk_text)

        if j >= n:
            break

        # slide window forward with overlap
        i = max(i + 1, j - overlap_lines)

    return [{"text": c} for c in chunks]

def chunk_any_file(content: str, file_path: str) -> List[Dict]:
    """
    Route to code chunker vs doc chunker.
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext in CODE_EXTS:
        return chunk_code_by_lines(content)
    # fallback for docs/prose
    return chunk_doc_paragraph_windows(content, chunk_size=1000, overlap=150)
