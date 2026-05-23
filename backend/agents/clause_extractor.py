"""Enhanced clause extractor with full metadata, SLA, risk flags, and compliance tasks."""
from __future__ import annotations
import json
from typing import Dict, Any
from services.llm_client import run_with_fallback
from utils.sanitizer import sanitize_for_llm
from utils.prompts import CLAUSE_EXTRACT_SYSTEM, CLAUSE_EXTRACT_EXAMPLES
from utils.heuristics import heuristic_extract

PRIMARY  = "azureai/genailab-maas-DeepSeek-V3-0324"
FALLBACK = "azure/genailab-maas-gpt-4o"

_EMPTY_META = {
    k: {"value": "Not Specified", "source": "", "confidence": 0, "type": "Explicit"}
    for k in [
        "vendor_name","client_name","effective_date","start_date","end_date",
        "renewal_notice_period","auto_renewal","tcv","currency","governing_law",
        "jurisdiction","named_applications","cloud_providers","cyber_insurance",
    ]
}

_EMPTY_SLA = {
    "uptime_sla":"Not Specified","p1_response":"Not Specified","p1_resolution":"Not Specified",
    "p2_response":"Not Specified","p2_resolution":"Not Specified",
    "p3_response":"Not Specified","p3_resolution":"Not Specified",
    "service_credits":"Not Specified","penalty_cap":"Not Specified",
    "measurement_window":"Not Specified","exclusions":[],"escalation_matrix":[],
}

_EXPECTED_CLAUSES = ["Force Majeure","Cyber Insurance","DR/BCP","Audit Rights",
                      "Security Incident Notification","Exit Management","IP Ownership"]


def _safe_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    i = text.find("{")
    j = text.rfind("}")
    if i >= 0 and j > i:
        text = text[i : j + 1]
    try:
        return json.loads(text)
    except Exception:
        return {}


async def extract(text: str, pages=None) -> Dict[str, Any]:
    safe = sanitize_for_llm(text)[:18000]
    msgs = [{"role": "system", "content": CLAUSE_EXTRACT_SYSTEM}]
    msgs.extend(CLAUSE_EXTRACT_EXAMPLES)
    msgs.append({"role": "user", "content": f"CONTRACT TEXT:\n{safe}"})
    raw    = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.1, max_tokens=4000)
    parsed = _safe_json(raw)

    clauses          = parsed.get("clauses") or []
    key_dates        = parsed.get("key_dates") or []
    obligations      = parsed.get("obligations") or []
    contract_meta    = parsed.get("contract_metadata") or _EMPTY_META
    sla_summary      = parsed.get("sla_summary") or _EMPTY_SLA
    maintenance_scope= parsed.get("maintenance_scope") or {"in_scope": [], "out_of_scope": []}
    risk_flags       = parsed.get("risk_flags") or []
    compliance_tasks = parsed.get("compliance_tasks") or []
    missing_raw      = parsed.get("missing_clauses") or []

    # Heuristic fill-in for base clause list
    if len(clauses) < 3 or not key_dates or not obligations:
        h = heuristic_extract(text, pages)
        if len(clauses) < 3:
            seen = {c.get("section") for c in clauses}
            for c in h["clauses"]:
                if c["section"] not in seen:
                    clauses.append(c)
        if not key_dates:
            key_dates = h["key_dates"]
        if not obligations:
            obligations = h["obligations"]

    # Ensure missing_clauses is always a list of strings
    if not missing_raw:
        # Detect from clauses which expected categories are absent
        present_sections = {c.get("section", "").lower() for c in clauses}
        missing_raw = []
        mapping = {
            "Force Majeure": "force_majeure",
            "Cyber Insurance": "security",
            "DR/BCP": "security",
            "Audit Rights": "data_protection",
            "Security Incident Notification": "security",
            "Exit Management": "exit_management",
            "IP Ownership": "ip",
        }
        for label, section_key in mapping.items():
            if section_key not in present_sections:
                missing_raw.append(label)

    # Fill meta defaults for any missing keys
    for k in _EMPTY_META:
        if k not in contract_meta:
            contract_meta[k] = _EMPTY_META[k]

    # Fill SLA defaults
    for k, v in _EMPTY_SLA.items():
        if k not in sla_summary:
            sla_summary[k] = v

    return {
        "clauses":          clauses,
        "key_dates":        key_dates,
        "obligations":      obligations,
        "contract_metadata":contract_meta,
        "sla_summary":      sla_summary,
        "maintenance_scope":maintenance_scope,
        "risk_flags":       risk_flags,
        "missing_clauses":  missing_raw,
        "compliance_tasks": compliance_tasks,
    }
