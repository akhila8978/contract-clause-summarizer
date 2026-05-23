from __future__ import annotations
import os
import logging
from pathlib import Path
from fastapi import APIRouter, Depends
from api.auth import require_user
from services.llm_client import embed
from services import vector_store as vs
from agents import parser_agent
from utils.chunker import chunk_clauses

log = logging.getLogger("rag")
router = APIRouter(prefix="/api/rag", tags=["rag"])

DATA_DIR = os.getenv("DATA_DIR", "../data")

FOLDER_MAP = {
    "company_policies": "policies",
    "contracts": "contracts",
    "contract_renewals": "renewals",
    "requirements": "requirements",
    "change_requests": "change_requests",
}


@router.get("/stats")
def stats(user: dict = Depends(require_user)):
    return {k: vs.count(k) for k in vs.COLLECTIONS}


@router.post("/reindex")
async def reindex(user: dict = Depends(require_user)):
    base = Path(DATA_DIR).resolve()
    report = {}
    if not base.exists():
        return {"ok": False, "error": f"data dir not found: {base}"}
    for folder, collection in FOLDER_MAP.items():
        folder_path = base / folder
        count = 0
        if not folder_path.exists():
            report[folder] = {"files": 0, "chunks": 0, "skipped": True}
            continue
        total_chunks = 0
        for p in folder_path.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".pdf", ".docx", ".txt", ".md"):
                try:
                    data = p.read_bytes()
                    text, _ = parser_agent.parse_document(p.name, data)
                    chunks = chunk_clauses(text)
                    if not chunks:
                        continue
                    embs = await embed(chunks)
                    ids = [f"seed_{p.stem}_{i}" for i in range(len(chunks))]
                    metas = [{"source": str(p.relative_to(base)), "title": p.stem} for _ in chunks]
                    vs.add(collection, ids, chunks, embs, metas)
                    total_chunks += len(chunks)
                    count += 1
                except Exception as e:
                    log.warning("reindex %s failed: %s", p, e)
        report[folder] = {"files": count, "chunks": total_chunks}
    return {"ok": True, "report": report, "stats": {k: vs.count(k) for k in vs.COLLECTIONS}}
