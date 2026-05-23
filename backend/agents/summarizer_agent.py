from __future__ import annotations
import json
from typing import Dict, Any, List
from services.llm_client import run_with_fallback
from utils.sanitizer import sanitize_for_llm
from utils.prompts import SECTION_SUMMARY_SYSTEM
from utils.heuristics import heuristic_summaries

PRIMARY = "azureai/genailab-maas-DeepSeek-V3-0324"
FALLBACK = "azure/genailab-maas-gpt-4o-mini"


def _parse(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    t = text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i : j + 1]
    try:
        return json.loads(t).get("section_summaries", [])
    except Exception:
        return []


async def summarize_sections(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not clauses:
        return []
    payload = sanitize_for_llm(json.dumps(clauses)[:14000])
    msgs = [
        {"role": "system", "content": SECTION_SUMMARY_SYSTEM},
        {"role": "user", "content": f"CLAUSES JSON:\n{payload}"},
    ]
    raw = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.2, max_tokens=2000)
    out = _parse(raw)
    # heuristic fallback / fill-in
    if not out or len(out) < len(clauses):
        h = heuristic_summaries(clauses)
        if not out:
            out = h
        else:
            seen = {s.get("section") for s in out}
            for s in h:
                if s.get("section") not in seen:
                    out.append(s)
    # ensure every entry has bullets — if model produced empty bullets, fill from heuristic
    for s in out:
        if not s.get("bullets"):
            match = next((c for c in clauses if c.get("section") == s.get("section")), None)
            if match:
                hs = heuristic_summaries([match])
                if hs:
                    s["bullets"] = hs[0].get("bullets", [])
    return out
