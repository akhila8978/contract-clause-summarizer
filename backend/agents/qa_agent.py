from __future__ import annotations
from typing import List, Dict
from services.llm_client import run_with_fallback, embed
from services import vector_store as vs
from utils.sanitizer import sanitize_for_llm
from utils.prompts import QA_SYSTEM
from utils.heuristics import heuristic_qa

PRIMARY = "azure/genailab-maas-gpt-4o-mini"
FALLBACK = "azure/genailab-maas-gpt-4o"


async def answer(history: List[Dict[str, str]], question: str, contract_text: str = "") -> str:
    ctx_parts: List[str] = []
    try:
        embs = await embed([question])
        pol = vs.query("policies", embs, n_results=3)[0]
        prior = vs.query("contracts", embs, n_results=2)[0]
        if contract_text:
            ctx_parts.append("CURRENT CONTRACT:\n" + contract_text[:6000])
        if pol:
            ctx_parts.append("POLICY EXCERPTS:\n" + "\n---\n".join([p["doc"][:500] for p in pol]))
        if prior:
            ctx_parts.append("SIMILAR PRIOR CONTRACTS:\n" + "\n---\n".join([p["doc"][:500] for p in prior]))
    except Exception:
        if contract_text:
            ctx_parts.append("CURRENT CONTRACT:\n" + contract_text[:6000])
    context = sanitize_for_llm("\n\n".join(ctx_parts))
    msgs: List[Dict[str, str]] = [{"role": "system", "content": QA_SYSTEM + "\n\nCONTEXT:\n" + context}]
    for m in history[-10:]:
        c = m.get("content", "")
        msgs.append({"role": m.get("role", "user"), "content": sanitize_for_llm(c) if isinstance(c, str) else c})
    msgs.append({"role": "user", "content": sanitize_for_llm(question)})
    out = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.2, max_tokens=900)
    if not out or not out.strip():
        # fallback to extractive QA over the provided context
        base = contract_text or "\n\n".join(ctx_parts)
        return heuristic_qa(question, base)
    return out
