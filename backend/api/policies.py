from __future__ import annotations
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from api.auth import require_user
from services import storage
from services.llm_client import embed
from services import vector_store as vs
from agents import parser_agent
from utils.chunker import chunk_clauses

log = logging.getLogger("policies")
router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.post("/upload")
async def upload_policy(file: UploadFile = File(...), title: str = Form(""), user: dict = Depends(require_user)):
    data = await file.read()
    text, pages = parser_agent.parse_document(file.filename, data)
    pid = storage.new_id("pol")
    storage.POLICIES[pid] = {
        "id": pid, "title": title or file.filename, "filename": file.filename,
        "uploaded_at": storage.now(), "text": text, "pages": pages,
    }
    chunks = chunk_clauses(text)
    if chunks:
        try:
            embs = await embed(chunks)
            ids = [f"{pid}_c{i}" for i in range(len(chunks))]
            metas = [{"policy_id": pid, "title": title or file.filename} for _ in chunks]
            vs.add("policies", ids, chunks, embs, metas)
        except Exception as e:
            log.warning("Index failed: %s", e)
    return {"id": pid, "title": storage.POLICIES[pid]["title"], "chunks": len(chunks)}


@router.get("")
def list_policies(user: dict = Depends(require_user)):
    out = []
    for p in storage.POLICIES.values():
        out.append({"id": p["id"], "title": p["title"], "filename": p["filename"],
                    "uploaded_at": p["uploaded_at"], "pages": len(p.get("pages", []))})
    out.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return {"policies": out}


@router.get("/{pid}")
def get_policy(pid: str, user: dict = Depends(require_user)):
    p = storage.POLICIES.get(pid)
    if not p:
        raise HTTPException(404, "Not found")
    return p
