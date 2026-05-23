from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from api.auth import require_user
from services import storage
from models.schemas import ChatMessageIn, FeedbackIn
from agents import qa_agent

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(body: ChatMessageIn, user: dict = Depends(require_user)):
    history = storage.CHAT_HISTORY.setdefault(body.session_id, [])
    contract_text = ""
    if body.contract_id:
        c = storage.CONTRACTS.get(body.contract_id)
        if not c:
            raise HTTPException(404, "Contract not found")
        contract_text = c.get("raw_text", "")
    answer = await qa_agent.answer(history, body.message, contract_text)
    history.append({"role": "user", "content": body.message})
    history.append({"role": "assistant", "content": answer})
    return {"answer": answer, "history": history}


@router.get("/chat/{session_id}")
def history(session_id: str, user: dict = Depends(require_user)):
    return {"history": storage.CHAT_HISTORY.get(session_id, [])}


@router.post("/feedback")
def feedback(body: FeedbackIn, user: dict = Depends(require_user)):
    storage.FEEDBACK.append({**body.model_dump(), "user": user.get("sub"), "ts": storage.now()})
    return {"ok": True, "count": len(storage.FEEDBACK)}
