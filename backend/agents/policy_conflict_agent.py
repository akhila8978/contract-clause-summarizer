from __future__ import annotations
import json
from typing import List, Dict, Any
from services.llm_client import run_with_fallback, embed
from services import vector_store as vs
from utils.sanitizer import sanitize_for_llm
from utils.prompts import POLICY_CONFLICT_SYSTEM
from utils.heuristics import heuristic_conflicts

PRIMARY = "azure/genailab-maas-gpt-4o"
FALLBACK = "azureai/genailab-maas-DeepSeek-R1"


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
        return json.loads(t).get("conflicts", [])
    except Exception:
        return []


async def check_conflicts(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not clauses:
        return []
    findings: List[Dict[str, Any]] = []
    try:
        queries = [f"{c.get('section','')}: {c.get('summary','')}" for c in clauses]
        embs = await embed(queries)
        retrieved = vs.query("policies", embs, n_results=3)
        for clause, hits in zip(clauses, retrieved):
            if not hits:
                continue
            policy_blob = "\n---\n".join([h["doc"][:800] for h in hits])
            msgs = [
                {"role": "system", "content": POLICY_CONFLICT_SYSTEM},
                {"role": "user", "content": sanitize_for_llm(
                    f"CLAUSE (section={clause.get('section')}):\n{clause.get('source_excerpt','')}\n\nPOLICY EXCERPTS:\n{policy_blob}"
                )},
            ]
            raw = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.1, max_tokens=900)
            findings.extend(_parse(raw))
    except Exception:
        pass
    # always also run heuristic checks and merge (dedup by section+issue)
    h = heuristic_conflicts(clauses)
    seen = {(f.get("clause_section"), f.get("issue")) for f in findings}
    for f in h:
        key = (f.get("clause_section"), f.get("issue"))
        if key not in seen:
            findings.append(f)
            seen.add(key)
    return findings
