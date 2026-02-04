# ingesters/confluence_ingest.py
import re
import html
from typing import List, Dict
from bs4 import BeautifulSoup

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 150

def _strip_html(html: str) -> str:
    """
    Convert HTML-ish content (Confluence storage/view/export_view) into clean text.
    Keep paragraph structure and list items. Returns empty string if nothing found.
    """
    if not html:
        return ""

    # Remove Confluence XML/macros like <ac:structured-macro> by parsing with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # remove script/style
    for t in soup(["script", "style"]):
        t.decompose()

    # Remove comments
    for c in soup.findAll(text=lambda text: isinstance(text, type(soup.Comment))):
        c.extract()

    # Gather visible blocks: paragraphs, headings, list items, table cells
    blocks = []
    for el in soup.find_all(['p','h1','h2','h3','h4','h5','li','td','div']):
        text = el.get_text(" ", strip=True)
        if text:
            # ignore very short artifacts
            if len(text.strip()) > 0:
                blocks.append(text.strip())

    if not blocks:
        # as a fallback, return all text
        text_all = soup.get_text("\n", strip=True)
        text_all = re.sub(r"\n{2,}", "\n\n", text_all).strip()
        return text_all

    # Join blocks double newline to denote paragraph boundaries
    text = "\n\n".join(blocks)
    # Normalize whitespace
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _sentence_split(text: str) -> List[str]:
    # simple sentence splitter (no heavy dependency)
    sents = re.split(r'(?<=[\.\?\!])\s+', text)
    return [s for s in sents if s.strip()]

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

def chunk_page(html_content: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[Dict]:
    """
    Boundary-aware chunker: splits cleaned text into chunks ~chunk_size chars,
    preferring paragraph boundaries, then sentence boundaries as fallback.
    Returns list of {"text": "..."} dicts.
    """
    text = _strip_html(html_content)
    if not text:
        return []

    # split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    cur = ""
    for para in paragraphs:
        if not cur:
            # start new
            if len(para) <= chunk_size:
                cur = para
            else:
                # paragraph too big: split by sentences
                for sent in _sentence_split(para):
                    if not cur:
                        cur = sent
                    elif len(cur) + 1 + len(sent) <= chunk_size:
                        cur = cur + " " + sent
                    else:
                        chunks.append(cur)
                        cur = sent
        else:
            # try to append paragraph
            if len(cur) + 2 + len(para) <= chunk_size:
                cur = cur + "\n\n" + para
            else:
                # flush current chunk
                chunks.append(cur)
                # start new chunk with paragraph (or split paragraph)
                if len(para) <= chunk_size:
                    cur = para
                else:
                    cur = ""
                    for sent in _sentence_split(para):
                        if not cur:
                            cur = sent
                        elif len(cur) + 1 + len(sent) <= chunk_size:
                            cur = cur + " " + sent
                        else:
                            chunks.append(cur)
                            cur = sent

    if cur:
        chunks.append(cur)

    # Add overlap: create overlapping chunks by merging end of previous with start of next when helpful
    if overlap and len(chunks) > 1:
        out_chunks = []
        for i, ch in enumerate(chunks):
            if i == 0:
                out_chunks.append(ch)
            else:
                prev = out_chunks[-1]
                # take last overlap chars from prev + current chunk start
                prev_tail = prev[-overlap:] if overlap < len(prev) else prev
                merged = (prev_tail + " " + ch).strip()
                # keep both versions: prev (unchanged) and merged as new chunk only if merged length not excessive
                if len(merged) <= chunk_size + overlap:
                    out_chunks.append(ch)  # keep current as-is
                else:
                    out_chunks.append(ch)
        chunks = out_chunks

    # Return as list of dicts for storage.insert_chunk API
    return [{"text": c} for c in chunks]
