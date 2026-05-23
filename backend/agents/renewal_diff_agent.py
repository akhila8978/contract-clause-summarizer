from __future__ import annotations
import json
from typing import Dict, Any, List
from services.llm_client import run_with_fallback, embed
from services import vector_store as vs
from utils.sanitizer import sanitize_for_llm
from utils.prompts import RENEWAL_DIFF_SYSTEM

PRIMARY = "azureai/genailab-maas-DeepSeek-R1"
FALLBACK = "azure/genailab-maas-gpt-4o"


def _parse(text: str) -> Dict[str, Any]:
    fallback = {"added": [], "removed": [], "changed": [], "key_dates": [], "risks": [],
                "clarity": {"completeness": 0, "policy_alignment": 0, "unambiguity": 0,
                            "mandatory_fields": 0, "overall_pct": 0}}
    if not text:
        return fallback
    t = text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i >= 0:
        t = t[i : j + 1]
    try:
        d = json.loads(t)
    except Exception:
        return fallback
    for k, v in fallback.items():
        d.setdefault(k, v)
    # compute overall if missing
    c = d.get("clarity", {}) or {}
    if not c.get("overall_pct"):
        pct = (0.30 * float(c.get("completeness", 0))
               + 0.25 * float(c.get("policy_alignment", 0))
               + 0.25 * float(c.get("unambiguity", 0))
               + 0.20 * float(c.get("mandatory_fields", 0))) * 100
        c["overall_pct"] = round(pct, 1)
        d["clarity"] = c
    return d


async def diff(old_text: str, new_text: str) -> Dict[str, Any]:
    # pull a few policy excerpts to ground alignment scoring
    q = await embed([new_text[:2000]])
    pol = vs.query("policies", q, n_results=4)[0]
    policy_blob = "\n---\n".join([p["doc"][:600] for p in pol])
    msgs = [
        {"role": "system", "content": RENEWAL_DIFF_SYSTEM},
        {"role": "user", "content": sanitize_for_llm(
            f"POLICY EXCERPTS:\n{policy_blob}\n\nOLD CONTRACT:\n{old_text[:8000]}\n\nNEW CONTRACT:\n{new_text[:8000]}"
        )},
    ]
    raw = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.1, max_tokens=2500)
    return _parse(raw)
