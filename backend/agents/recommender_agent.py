from __future__ import annotations
import json
from typing import List, Dict, Any
from services.llm_client import run_with_fallback, embed
from services import vector_store as vs
from utils.sanitizer import sanitize_for_llm
from utils.prompts import RECOMMENDER_SYSTEM

PRIMARY = "azure/genailab-maas-gpt-4o"
FALLBACK = "azureai/genailab-maas-DeepSeek-V3-0324"


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
        return json.loads(t).get("recommendations", [])
    except Exception:
        return []


async def recommend(clause_section: str, current_text: str) -> List[Dict[str, Any]]:
    embs = await embed([f"{clause_section}: {current_text}"])
    policies = vs.query("policies", embs, n_results=3)[0]
    priors = vs.query("contracts", embs, n_results=3)[0]
    policy_blob = "\n---\n".join([p["doc"][:600] for p in policies])
    prior_blob = "\n---\n".join([p["doc"][:600] for p in priors])
    msgs = [
        {"role": "system", "content": RECOMMENDER_SYSTEM},
        {"role": "user", "content": sanitize_for_llm(
            f"CURRENT_CLAUSE ({clause_section}):\n{current_text}\n\n"
            f"POLICY_EXCERPTS:\n{policy_blob}\n\nSIMILAR_PRIOR_CLAUSES:\n{prior_blob}"
        )},
    ]
    raw = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.3, max_tokens=1500)
    return _parse(raw)
