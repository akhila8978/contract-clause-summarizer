from __future__ import annotations
from typing import List, Dict
import re

CLAUSE_HEAD = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?|[A-Z][A-Z \-]{4,})\s", re.MULTILINE)


def chunk_clauses(text: str, max_chars: int = 1500) -> List[str]:
    # split on numbered or upper-cased headings
    parts = CLAUSE_HEAD.split(text)
    chunks: List[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        if len(buf) + len(p) > max_chars and buf:
            chunks.append(buf.strip())
            buf = p
        else:
            buf += "\n" + p
    if buf.strip():
        chunks.append(buf.strip())
    if not chunks:
        # fallback: fixed-window
        for i in range(0, len(text), max_chars):
            chunks.append(text[i : i + max_chars])
    return [c for c in chunks if c.strip()]
