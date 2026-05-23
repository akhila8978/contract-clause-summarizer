"""Generates structured executive summary from contract analysis data."""
from __future__ import annotations
import json
from typing import Dict, Any
from services.llm_client import run_with_fallback
from utils.sanitizer import sanitize_for_llm
from utils.prompts import EXECUTIVE_SUMMARY_SYSTEM

PRIMARY  = "azureai/genailab-maas-DeepSeek-V3-0324"
FALLBACK = "azure/genailab-maas-gpt-4o"


def _safe_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    text = text.strip().strip("`")
    if text.startswith("json"):
        text = text[4:]
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        text = text[i : j + 1]
    try:
        return json.loads(text)
    except Exception:
        return {}


def _heuristic_summary(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback heuristic executive summary builder."""
    meta  = contract.get("contract_metadata", {})
    sla   = contract.get("sla_summary", {})
    flags = contract.get("risk_flags", [])
    missing = contract.get("missing_clauses", [])

    def _v(field):
        obj = meta.get(field, {})
        return obj.get("value", "Not Specified") if isinstance(obj, dict) else str(obj)

    top_risks = [
        {"rank": i + 1, "flag": f.get("flag", ""), "severity": f.get("severity", ""),
         "impact": f.get("description", ""), "remediation": f.get("remediation", "")}
        for i, f in enumerate(sorted(flags, key=lambda x: {"critical":0,"high":1,"medium":2,"low":3}.get(x.get("severity","low"),3)))
    ]

    return {
        "contract_snapshot": {
            "vendor": _v("vendor_name"), "client": _v("client_name"),
            "term": f"{_v('start_date')} to {_v('end_date')}",
            "renewal_mechanics": _v("renewal_notice_period"),
            "auto_renewal": _v("auto_renewal"), "tcv": _v("tcv"), "currency": _v("currency"),
            "governing_law": _v("governing_law"), "jurisdiction": _v("jurisdiction"),
        },
        "sla_commitments": {
            "uptime": sla.get("uptime_sla", "Not Specified"),
            "p1_timelines": f"Response: {sla.get('p1_response','NS')} / Resolution: {sla.get('p1_resolution','NS')}",
            "p2_timelines": f"Response: {sla.get('p2_response','NS')} / Resolution: {sla.get('p2_resolution','NS')}",
            "penalties": sla.get("service_credits", "Not Specified"),
            "penalty_cap": sla.get("penalty_cap", "Not Specified"),
            "exclusions": sla.get("exclusions", []),
        },
        "operational_dependencies": {
            "client_obligations": [o.get("obligation","") for o in contract.get("obligations",[]) if o.get("party","").lower() in ("client","customer")],
            "vendor_obligations": [o.get("obligation","") for o in contract.get("obligations",[]) if o.get("party","").lower() == "vendor"],
        },
        "top_risks": top_risks[:5],
        "exit_readiness": {
            "kt_obligations": "Not Specified",
            "transition_support": "Not Specified",
            "exit_management": "Exit Management clause " + ("absent — HIGH RISK" if "Exit Management" in missing else "present"),
            "data_return": "Not Specified",
        },
        "missing_protections": [{"clause": m, "risk": "High — unprotected exposure"} for m in missing],
        "recommended_actions": [
            {"action": f.get("remediation",""), "owner": "Legal/Procurement",
             "priority": f.get("severity","medium"), "citation": f.get("citation","")}
            for f in flags if f.get("remediation")
        ][:8],
    }


async def generate(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary; returns the summary dict."""
    # Prepare a condensed payload (avoid sending raw_text)
    payload = {
        "contract_metadata": contract.get("contract_metadata", {}),
        "sla_summary":       contract.get("sla_summary", {}),
        "maintenance_scope": contract.get("maintenance_scope", {}),
        "risk_flags":        contract.get("risk_flags", []),
        "missing_clauses":   contract.get("missing_clauses", []),
        "obligations":       contract.get("obligations", [])[:30],
        "key_dates":         contract.get("key_dates", []),
        "conflicts":         contract.get("conflicts", []),
        "security":          contract.get("security", []),
    }
    safe = sanitize_for_llm(json.dumps(payload))[:14000]
    msgs = [
        {"role": "system", "content": EXECUTIVE_SUMMARY_SYSTEM},
        {"role": "user", "content": f"CONTRACT ANALYSIS:\n{safe}"},
    ]
    raw    = await run_with_fallback(PRIMARY, FALLBACK, msgs, temperature=0.15, max_tokens=2500)
    parsed = _safe_json(raw)
    summary = parsed.get("executive_summary")
    if not summary:
        summary = _heuristic_summary(contract)
    return summary
