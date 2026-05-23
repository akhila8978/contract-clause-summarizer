from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from api.auth import require_user
from services import storage
from services.ws_manager import ws_manager
from agents import parser_agent, renewal_diff_agent

router = APIRouter(prefix="/api/renewals", tags=["renewals"])


@router.post("/analyze")
async def analyze_renewal(
    old_contract_id: str = Form(...),
    file: UploadFile = File(...),
    session_id: str = Form(""),
    user: dict = Depends(require_user),
):
    old = storage.CONTRACTS.get(old_contract_id)
    if not old:
        raise HTTPException(404, "Old contract not found")
    if session_id:
        await ws_manager.send(session_id, "progress", {"stage": "parsing", "message": "Parsing renewal...", "pct": 20})
    new_text, pages = parser_agent.parse_document(file.filename, await file.read())
    if session_id:
        await ws_manager.send(session_id, "progress", {"stage": "diffing", "message": "Diffing old vs new...", "pct": 60})
    diff = await renewal_diff_agent.diff(old.get("raw_text", ""), new_text)
    rid = storage.new_id("rnw")
    storage.RENEWALS[rid] = {
        "id": rid, "old_contract_id": old_contract_id, "filename": file.filename,
        "uploaded_at": storage.now(), "new_text": new_text, "pages": pages, "diff": diff,
    }
    if session_id:
        await ws_manager.send(session_id, "progress", {"stage": "done", "message": "Renewal analyzed", "pct": 100})
    return {"id": rid, "old_contract_id": old_contract_id, "diff": diff, "filename": file.filename}


@router.get("")
def list_renewals(user: dict = Depends(require_user)):
    out = []
    for r in storage.RENEWALS.values():
        out.append({"id": r["id"], "filename": r["filename"], "old_contract_id": r["old_contract_id"],
                    "uploaded_at": r["uploaded_at"],
                    "clarity": r.get("diff", {}).get("clarity", {})})
    out.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return {"renewals": out}


@router.get("/{rid}")
def get_renewal(rid: str, user: dict = Depends(require_user)):
    r = storage.RENEWALS.get(rid)
    if not r:
        raise HTTPException(404, "Not found")
    return r
