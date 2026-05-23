from __future__ import annotations
import json
from typing import List, Dict, Any
from services.llm_client import run_with_fallback
from utils.sanitizer import sanitize_for_llm
from utils.prompts import SECURITY_SYSTEM
from utils.heuristics import heuristic_security

PRIMARY = "azure/genailab-maas-gpt-4o"
FALLBACK = "azureai/genailab-maas-Llama-3.3-70B-Instruct"


def _parse(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    t = text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i >= 0:
        t = t[i : j + 1]
    try:
        return json.loads(t).get("security_findings", [])
    except Exception:
        return []


async def scan(text: str) -> List[Dict[str, Any]]:
    safe = sanitize_for_llm(text)[:14000]
    msgs = [
        {"role": "system", "content": SECURITY_SYSTEM},
        {"role": "user", "content": f"CONTRACT TEXT:\n{safe}"},
    ]
    raw = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.1, max_tokens=1500)
    out = _parse(raw)
    if not out:
        out = heuristic_security(text)
    return out
