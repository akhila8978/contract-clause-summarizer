from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from api.auth import require_user
from services import storage
from agents import recommender_agent
from models.schemas import RecommendRequest, ApplyFixRequest

router = APIRouter(prefix="/api/clauses", tags=["clauses"])


@router.post("/recommend")
async def recommend(body: RecommendRequest, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(body.contract_id)
    if not c:
        raise HTTPException(404, "Contract not found")
    recs = await recommender_agent.recommend(body.clause_section, body.current_text)
    return {"recommendations": recs}


@router.post("/apply-fix")
async def apply_fix(body: ApplyFixRequest, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(body.contract_id)
    if not c:
        raise HTTPException(404, "Contract not found")
    text = c.get("raw_text", "")
    if body.original_text and body.original_text in text:
        new_text = text.replace(body.original_text, body.new_text, 1)
    else:
        # append as amendment if not found verbatim
        new_text = text + f"\n\n[AMENDMENT — {body.clause_section}]\n{body.new_text}"
    c["raw_text"] = new_text
    # also update matching clause excerpt
    for cl in c.get("clauses", []):
        if cl.get("section") == body.clause_section and cl.get("source_excerpt") == body.original_text:
            cl["source_excerpt"] = body.new_text
            cl["summary"] = (cl.get("summary", "") + " [edited]")
    return {"ok": True, "full_text": new_text}
