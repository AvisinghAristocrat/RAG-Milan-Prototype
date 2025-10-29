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

    # remove <script> and <style> blocks (case-insensitive, multiline)
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", s)

    # replace <br> and common block tags with newlines
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p\s*>", "\n\n", s)
    s = re.sub(r"(?i)</h\d\s*>", "\n\n", s)
    s = re.sub(r"(?i)<li\s*>", "\n- ", s)

    # strip all remaining tags
    s = re.sub(r"<[^>]+>", " ", s)

    # decode HTML entities
    s = html.unescape(s)

    # normalize whitespace and paragraphs
    s = re.sub(r"\r\n?", "\n", s)
    s = re.sub(r"\n\s+\n", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _split_into_windows_by_chars(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Break 'text' (a paragraph or long block) into windows sized by characters,
    preserving whole words and ensuring approximately `overlap` characters
    between adjacent windows.
    """
    words = text.split()
    if not words:
        return []

    n = len(words)
    windows = []
    start = 0

    while start < n:
        # Build window from start to end while char length <= chunk_size
        length = 0
        end = start
        while end < n:
            wlen = len(words[end])
            # add 1 for space if not first word in window
            add = wlen + (1 if end > start else 0)
            if length + add <= chunk_size:
                length += add
                end += 1
            else:
                break

        # If we couldn't add even the first word (very long single word), put that single word
        if end == start:
            windows.append(words[start])
            start += 1
            continue

        window_text = " ".join(words[start:end])
        windows.append(window_text)

        # If we consumed all words, done
        if end >= n:
            break

        # Compute how many words from the end we need to keep to satisfy overlap (in chars)
        k = 0
        cum = 0
        t = end - 1
        while t >= start and cum < overlap:
            # add length of words[t] and a space if k > 0
            if k == 0:
                cum += len(words[t])
            else:
                cum += len(words[t]) + 1
            k += 1
            t -= 1

        # next start ensures overlap of approximately 'overlap' characters
        next_start = end - k
        if next_start <= start:
            # fallback to advance by at least one word so progress is guaranteed
            next_start = start + max(1, int((chunk_size - overlap) / 6))
            if next_start <= start:
                next_start = start + 1

        start = next_start

    return windows

def chunk_text_by_chars(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    """
    Chunk text on words and characters while preferring paragraph boundaries.
    Returns a list of dicts with key "text".
    """
    if not text:
        return []

    # Split into paragraphs; keep paragraphs as units when possible.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if not current:
            current = para
        else:
            # If we can append the paragraph without exceeding the chunk size, do it
            if len(current) + 2 + len(para) <= chunk_size:
                current = current + "\n\n" + para
            else:
                # Emit windows for current
                chunks.extend(_split_into_windows_by_chars(current, chunk_size, overlap))
                current = para

    # Flush the final current paragraph
    if current:
        chunks.extend(_split_into_windows_by_chars(current, chunk_size, overlap))

    # Convert to list of dicts
    return [{"text": c} for c in chunks]

def chunk_page(storage_value: str, chunk_size: int = 1000, overlap: int = 150) -> List[Dict]:
    """
    Public function called by ingest. Returns list of {'text': ...} chunks.
    """
    text = _strip_html(storage_value)
    return chunk_text_by_chars(text, chunk_size=chunk_size, overlap=overlap)