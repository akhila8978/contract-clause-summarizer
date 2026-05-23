"""Pure parsing — no LLM. Returns text and page map."""
from __future__ import annotations
from typing import Tuple, List, Dict
from utils.pdf_extract import extract_pdf
from utils.docx_extract import extract_docx


def parse_document(filename: str, data: bytes) -> Tuple[str, List[Dict]]:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return extract_pdf(data)
    if name.endswith(".docx") or name.endswith(".doc"):
        return extract_docx(data)
    # treat as plain text
    text = data.decode("utf-8", errors="ignore")
    return text, [{"page": 1, "text": text, "char_start": 0}]
