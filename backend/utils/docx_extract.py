from __future__ import annotations
from typing import Dict, List, Tuple
from docx import Document
import io


def extract_docx(data: bytes) -> Tuple[str, List[Dict]]:
    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    text = "\n".join(paragraphs)
    # approximate "pages" by chunking ~3000 chars
    pages: List[Dict] = []
    PAGE = 3000
    i = 0
    p = 1
    while i < len(text):
        chunk = text[i : i + PAGE]
        pages.append({"page": p, "text": chunk, "char_start": i})
        i += PAGE
        p += 1
    if not pages:
        pages = [{"page": 1, "text": "", "char_start": 0}]
    return text, pages
