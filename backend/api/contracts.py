"""Enhanced contracts API — full metadata, SLA, risk flags, executive summary, multi-export."""
from __future__ import annotations
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Response
from api.auth import require_user
from services import storage
from services.ws_manager import ws_manager
from services.llm_client import embed
from services import vector_store as vs
from services.doc_export import contract_to_pdf, contract_to_csv, contract_to_json
from agents import (
    parser_agent, clause_extractor, summarizer_agent,
    policy_conflict_agent, security_agent, executive_summary_agent,
)
from utils.chunker import chunk_clauses

log    = logging.getLogger("contracts")
router = APIRouter(prefix="/api/contracts", tags=["contracts"])

PRIORITY_ORDER = ["amendment", "addendum", "change_request", "sow", "sla", "msa", "master"]


async def _notify(session_id: Optional[str], stage: str, message: str, pct: int):
    if session_id:
        await ws_manager.send(session_id, "progress", {"stage": stage, "message": message, "pct": pct})


def _detect_doc_type(filename: str) -> str:
    fn = filename.lower()
    for kw in PRIORITY_ORDER:
        if kw in fn:
            return kw
    return "contract"


@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    company: str     = Form("Unknown"),
    session_id: str  = Form(""),
    user: dict       = Depends(require_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")

    doc_type = _detect_doc_type(file.filename or "")

    await _notify(session_id, "parsing", "Extracting text…", 10)
    text, pages = parser_agent.parse_document(file.filename, data)
    if not text.strip():
        raise HTTPException(400, "No text extractable from this document")

    await _notify(session_id, "extracting", "AI clause extraction & metadata…", 25)
    extract_task  = clause_extractor.extract(text, pages)
    security_task = security_agent.scan(text)
    extracted, security = await asyncio.gather(extract_task, security_task)
    clauses = extracted.get("clauses", [])

    await _notify(session_id, "summarizing", "Summarising sections & policy checks…", 50)
    summary_task  = summarizer_agent.summarize_sections(clauses)
    conflict_task = policy_conflict_agent.check_conflicts(clauses)
    summaries, conflicts = await asyncio.gather(summary_task, conflict_task)

    await _notify(session_id, "executive", "Generating executive summary…", 70)
    partial_contract = {
        "contract_metadata": extracted.get("contract_metadata", {}),
        "sla_summary":       extracted.get("sla_summary", {}),
        "maintenance_scope": extracted.get("maintenance_scope", {}),
        "risk_flags":        extracted.get("risk_flags", []),
        "missing_clauses":   extracted.get("missing_clauses", []),
        "obligations":       extracted.get("obligations", []),
        "key_dates":         extracted.get("key_dates", []),
        "conflicts":         conflicts,
        "security":          security,
    }
    exec_summary = await executive_summary_agent.generate(partial_contract)

    await _notify(session_id, "indexing", "Indexing for retrieval…", 88)
    cid    = storage.new_id("ctr")
    chunks = chunk_clauses(text)
    if chunks:
        try:
            embs = await embed(chunks)
            ids   = [f"{cid}_c{i}" for i in range(len(chunks))]
            metas = [{"contract_id": cid, "company": company, "source": file.filename} for _ in chunks]
            vs.add("contracts", ids, chunks, embs, metas)
        except Exception as e:
            log.warning("Index failed: %s", e)

    contract = {
        "id":               cid,
        "name":             file.filename,
        "company":          company,
        "doc_type":         doc_type,
        "uploaded_at":      storage.now(),
        "uploaded_by":      user.get("sub"),
        "pages":            pages,
        "raw_text":         text,
        # Clause data
        "clauses":          clauses,
        "section_summaries":summaries,
        "conflicts":        conflicts,
        "security":         security,
        "key_dates":        extracted.get("key_dates", []),
        "obligations":      extracted.get("obligations", []),
        # Enhanced fields
        "contract_metadata":extracted.get("contract_metadata", {}),
        "sla_summary":      extracted.get("sla_summary", {}),
        "maintenance_scope":extracted.get("maintenance_scope", {}),
        "risk_flags":       extracted.get("risk_flags", []),
        "missing_clauses":  extracted.get("missing_clauses", []),
        "compliance_tasks": extracted.get("compliance_tasks", []),
        "executive_summary":exec_summary,
    }
    storage.CONTRACTS[cid] = contract
    await _notify(session_id, "done", "Analysis complete", 100)
    out = {k: v for k, v in contract.items() if k != "raw_text"}
    return out


@router.get("")
def list_contracts(user: dict = Depends(require_user)):
    out = []
    for c in storage.CONTRACTS.values():
        meta      = c.get("contract_metadata", {})
        vendor    = meta.get("vendor_name", {})
        tcv       = meta.get("tcv", {})
        end_date  = meta.get("end_date", {})
        out.append({
            "id":             c["id"],
            "name":           c["name"],
            "company":        c["company"],
            "doc_type":       c.get("doc_type", "contract"),
            "uploaded_at":    c["uploaded_at"],
            "conflict_count": len(c.get("conflicts", [])),
            "security_count": len(c.get("security", [])),
            "risk_flag_count":len(c.get("risk_flags", [])),
            "missing_count":  len(c.get("missing_clauses", [])),
            "high_risk":      sum(1 for x in c.get("risk_flags", []) if x.get("severity") in ("critical","high")),
            "vendor":         vendor.get("value","") if isinstance(vendor, dict) else "",
            "tcv":            tcv.get("value","") if isinstance(tcv, dict) else "",
            "end_date":       end_date.get("value","") if isinstance(end_date, dict) else "",
        })
    out.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return {"contracts": out}


@router.get("/{cid}")
def get_contract(cid: str, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    return {k: v for k, v in c.items() if k != "raw_text"}


@router.get("/{cid}/text")
def get_text(cid: str, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    return {"text": c.get("raw_text", ""), "pages": c.get("pages", [])}


@router.get("/{cid}/export/pdf")
def export_pdf(cid: str, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    pdf = contract_to_pdf(c)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={cid}.pdf"})


@router.get("/{cid}/export/csv")
def export_csv(cid: str, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    csv_bytes = contract_to_csv(c)
    return Response(csv_bytes, media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={cid}.csv"})


@router.get("/{cid}/export/json")
def export_json(cid: str, user: dict = Depends(require_user)):
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    j = contract_to_json(c)
    return Response(j, media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={cid}.json"})


@router.patch("/{cid}")
async def patch_contract(cid: str, body: dict, user: dict = Depends(require_user)):
    """Allow partial updates to contract data (edited summaries, metadata)."""
    c = storage.CONTRACTS.get(cid)
    if not c:
        raise HTTPException(404, "Not found")
    # Deep merge for nested dicts
    for key, value in body.items():
        if isinstance(value, dict) and isinstance(c.get(key), dict):
            c[key] = {**c[key], **value}
        else:
            c[key] = value
    storage.CONTRACTS[cid] = c
    return {"ok": True}
