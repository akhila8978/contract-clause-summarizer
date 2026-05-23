from __future__ import annotations
from typing import Dict, List, Tuple
from pypdf import PdfReader
import io


def extract_pdf(data: bytes) -> Tuple[str, List[Dict]]:
    reader = PdfReader(io.BytesIO(data))
    pages: List[Dict] = []
    full = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page": i + 1, "text": text, "char_start": sum(len(p["text"]) + 2 for p in pages)})
        full.append(text)
    return "\n\n".join(full), pages
