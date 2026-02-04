# ingesters/code_repo_reader.py
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from ingesters.chunking import chunk_any_file, guess_language

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".idea", ".vscode",
    "bin", "obj",
    "node_modules", "dist", "build",
    "Library", "Temp", "Logs",
}

DEFAULT_INCLUDE_EXTS = {
    ".cs", ".ts", ".js", ".py", ".java", ".kt", ".go",
    ".cpp", ".c", ".h", ".hpp",
    ".md", ".yml", ".yaml", ".json", ".xml",
}

def read_text_file(path: str) -> Optional[str]:
    # keep it simple + robust
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception:
            return None
    except Exception:
        return None

def iter_repo_files(
    repo_root: str,
    include_exts: Optional[set[str]] = None,
    exclude_dirs: Optional[set[str]] = None,
) -> Iterator[str]:
    include_exts = include_exts or DEFAULT_INCLUDE_EXTS
    exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS

    repo_root = os.path.abspath(repo_root)

    for root, dirs, files in os.walk(repo_root):
        # prune excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for name in files:
            _, ext = os.path.splitext(name.lower())
            if ext not in include_exts:
                continue
            yield os.path.join(root, name)

def build_code_chunks(
    repo_name: str,
    repo_root: str,
) -> List[Dict]:
    """
    Returns records ready for your existing 'insert chunks' step.
    Each record: {chunk_text, meta}
    """
    out: List[Dict] = []
    for path in iter_repo_files(repo_root):
        content = read_text_file(path)
        if not content:
            continue

        rel_path = os.path.relpath(path, start=os.path.abspath(repo_root))
        language = guess_language(path)

        chunks = chunk_any_file(content, file_path=path)
        for c in chunks:
            out.append({
                "chunk_text": c["text"],
                "meta": {
                    "source_type": "code",
                    "repo_name": repo_name,
                    "file_path": rel_path,
                    "language": language,
                }
            })
    return out
