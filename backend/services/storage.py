"""In-memory app storage (hackathon style — no DB)."""
from __future__ import annotations
import time
import uuid
from typing import Dict, List, Any

# Each contract: {id, name, company, uploaded_at, pages, sections, conflicts, security, key_dates, obligations, raw_text, page_map, source_filename}
CONTRACTS: Dict[str, Dict[str, Any]] = {}
POLICIES: Dict[str, Dict[str, Any]] = {}
RENEWALS: Dict[str, Dict[str, Any]] = {}
FEEDBACK: List[Dict[str, Any]] = []
CHAT_HISTORY: Dict[str, List[Dict[str, str]]] = {}


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def now() -> float:
    return time.time()
