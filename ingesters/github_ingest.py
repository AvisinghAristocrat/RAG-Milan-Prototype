# ingesters/github_ingest.py
import re
from typing import List, Dict

def chunk_file(content: str, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    if not content:
        return []
    # Split by paragraphs (blank line)
    paras = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    chunks = []
    current = ""
    for p in paras:
        if not current:
            current = p
        else:
            if len(current) + 1 + len(p) <= chunk_size:
                current += "\n\n" + p
            else:
                chunks.extend(_split_into_windows(current, chunk_size, overlap))
                current = p
    if current:
        chunks.extend(_split_into_windows(current, chunk_size, overlap))
    return [{"text": c} for c in chunks]

def _split_into_windows(text: str, chunk_size:int, overlap:int):
    words = text.split()
    if not words:
        return []
    out = []
    i = 0
    n = len(words)
    while i < n:
        length = 0
        j = i
        window_words = []
        while j < n and (length + len(words[j]) + 1) <= chunk_size:
            window_words.append(words[j])
            length += len(words[j]) + 1
            j += 1
        if not window_words:
            window_words = [words[i]]
            j = i + 1
        out.append(" ".join(window_words))
        # move forward by approximate words to achieve overlap
        step = max(1, int((chunk_size - overlap) / 6))
        i += step
    return out
