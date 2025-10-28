# ingesters/confluence_ingest.py
import re
import html
from typing import List, Dict

def _strip_html(storage_value: str) -> str:
    """
    Convert Confluence storage format (XHTML) to plain text:
     - preserve paragraphs as newlines
     - remove tags, scripts, styles, and decode entities
    """
    if not storage_value:
        return ""
    s = storage_value

    # remove <script> and <style> blocks
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", s)

    # replace <br> and block tags with newlines
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p\s*>", "\n\n", s)
    s = re.sub(r"(?i)</h\d\s*>", "\n\n", s)
    s = re.sub(r"(?i)<li\s*>", "\n- ", s)

    # strip all remaining tags
    s = re.sub(r"<[^>]+>", " ", s)

    # decode HTML entities
    s = html.unescape(s)

    # collapse multiple whitespace/newlines
    s = re.sub(r"\n\s+\n", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def chunk_text_by_chars(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    """
    Chunk text on words but respecting chunk_size characters (approx).
    Prefer paragraph boundaries when available.
    """
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if not current:
            current = para
        else:
            # if adding paragraph exceeds size, flush current as one chunk (or split)
            if len(current) + 1 + len(para) <= chunk_size:
                current += "\n\n" + para
            else:
                # flush current into chunk(s)
                chunks.extend(_split_into_windows(current, chunk_size, overlap))
                current = para
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
        window_words = []
        length = 0
        j = i
        while j < n and (length + len(words[j]) + 1) <= chunk_size:
            window_words.append(words[j])
            length += len(words[j]) + 1
            j += 1
        if not window_words:
            # single large word fallback
            window_words = [words[i]]
            j = i + 1
        out.append(" ".join(window_words))
        # step by chunk_size - overlap words (approx)
        # compute step by characters: advance until we regained overlap
        # simpler: advance by number of words approximating overlap
        if j >= n:
            break
        # approximate words to step by: find k words to step to maintain overlap
        step = max(1, int((chunk_size - overlap) / 6))  # rough words estimate
        i += step
    return out

def chunk_page(storage_value: str, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    text = _strip_html(storage_value)
    return chunk_text_by_chars(text, chunk_size=chunk_size, overlap=overlap)
