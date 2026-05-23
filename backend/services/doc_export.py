"""Enhanced export: PDF (rich), CSV (full fields), JSON (complete)."""
from __future__ import annotations
import csv
import io
import json
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
_RISK_COLORS = {"critical": colors.HexColor("#7f1d1d"), "high": colors.HexColor("#991b1b"),
                "medium":   colors.HexColor("#92400e"), "low":  colors.HexColor("#166534")}
_RISK_BG     = {"critical": colors.HexColor("#fee2e2"), "high": colors.HexColor("#fee2e2"),
                "medium":   colors.HexColor("#fef3c7"), "low":  colors.HexColor("#dcfce7")}


def _v(obj, fallback="Not Specified"):
    if isinstance(obj, dict):
        return obj.get("value") or fallback
    return str(obj) if obj else fallback


# ─── PDF ──────────────────────────────────────────────────────────────────────
def contract_to_pdf(contract: Dict[str, Any]) -> bytes:
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch,
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
    st   = getSampleStyleSheet()
    flow = []

    h1 = ParagraphStyle("H1", parent=st["Title"],   fontSize=16, spaceAfter=4, textColor=colors.HexColor("#1e3a5f"))
    h2 = ParagraphStyle("H2", parent=st["Heading2"],fontSize=12, spaceAfter=2, textColor=colors.HexColor("#1e3a5f"), spaceBefore=10)
    h3 = ParagraphStyle("H3", parent=st["Heading3"],fontSize=10, spaceAfter=1, textColor=colors.HexColor("#374151"))
    nm = ParagraphStyle("NM", parent=st["Normal"],  fontSize=9,  spaceAfter=2)
    sm = ParagraphStyle("SM", parent=st["Normal"],  fontSize=8,  spaceAfter=1, textColor=colors.HexColor("#6b7280"))

    # Header
    flow.append(Paragraph(f"Contract Analysis Report", h1))
    flow.append(Paragraph(f"{contract.get('name','')}  ·  {contract.get('company','')}", sm))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb"), spaceAfter=8))

    # ── 1. Contract Metadata ──────────────────────────────────────────────────
    meta = contract.get("contract_metadata", {})
    flow.append(Paragraph("1. Contract Metadata", h2))
    meta_rows = [["Field","Value","Confidence","Type"]]
    field_labels = {
        "vendor_name":"Vendor","client_name":"Client","effective_date":"Effective Date",
        "start_date":"Start Date","end_date":"End Date","renewal_notice_period":"Renewal Notice",
        "auto_renewal":"Auto-Renewal","tcv":"TCV","currency":"Currency",
        "governing_law":"Governing Law","jurisdiction":"Jurisdiction",
        "named_applications":"Named Applications","cloud_providers":"Cloud Providers",
        "cyber_insurance":"Cyber Insurance",
    }
    for key, label in field_labels.items():
        obj = meta.get(key, {})
        val  = _v(obj)
        conf = str(obj.get("confidence","")) + "%" if isinstance(obj,dict) else ""
        typ  = obj.get("type","") if isinstance(obj,dict) else ""
        meta_rows.append([label, val[:80], conf, typ])
    t = Table(meta_rows, colWidths=[1.4*inch,3.6*inch,0.8*inch,0.8*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTSIZE",(0,0),(-1,-1),8),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fafc")]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e5e7eb")),("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    flow.append(t); flow.append(Spacer(1,8))

    # ── 2. SLA Summary ────────────────────────────────────────────────────────
    sla = contract.get("sla_summary", {})
    flow.append(Paragraph("2. SLA Summary", h2))
    sla_rows = [
        ["Uptime SLA", sla.get("uptime_sla","Not Specified")],
        ["P1 Response / Resolution", f"{sla.get('p1_response','NS')} / {sla.get('p1_resolution','NS')}"],
        ["P2 Response / Resolution", f"{sla.get('p2_response','NS')} / {sla.get('p2_resolution','NS')}"],
        ["P3 Response / Resolution", f"{sla.get('p3_response','NS')} / {sla.get('p3_resolution','NS')}"],
        ["Service Credits", sla.get("service_credits","Not Specified")],
        ["Penalty Cap", sla.get("penalty_cap","Not Specified")],
        ["Measurement Window", sla.get("measurement_window","Not Specified")],
        ["Exclusions", "; ".join(sla.get("exclusions",[]) or ["None specified"])],
    ]
    t2 = Table(sla_rows, colWidths=[2*inch,4.6*inch])
    t2.setStyle(TableStyle([
        ("FONTSIZE",(0,0),(-1,-1),8),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,colors.HexColor("#f8fafc")]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e5e7eb")),
    ]))
    flow.append(t2); flow.append(Spacer(1,8))

    # ── 3. Maintenance Scope ──────────────────────────────────────────────────
    scope = contract.get("maintenance_scope", {})
    flow.append(Paragraph("3. Maintenance Scope", h2))
    in_scope  = scope.get("in_scope", [])
    out_scope = scope.get("out_of_scope", [])
    scope_rows = [["IN SCOPE","OUT OF SCOPE"]]
    max_r = max(len(in_scope), len(out_scope), 1)
    for i in range(max_r):
        scope_rows.append([
            f"✓ {in_scope[i]}"  if i < len(in_scope)  else "",
            f"✗ {out_scope[i]}" if i < len(out_scope) else "",
        ])
    t3 = Table(scope_rows, colWidths=[3.3*inch,3.3*inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fafc")]),
    ]))
    flow.append(t3); flow.append(Spacer(1,8))

    # ── 4. Risk Flags ─────────────────────────────────────────────────────────
    risk_flags = contract.get("risk_flags", [])
    flow.append(Paragraph("4. Risk Flags", h2))
    if risk_flags:
        rf_rows = [["Severity","Flag","Description","Remediation"]]
        sev_order = {"critical":0,"high":1,"medium":2,"low":3}
        for rf in sorted(risk_flags, key=lambda x: sev_order.get(x.get("severity","low"),3)):
            rf_rows.append([rf.get("severity","").upper(), rf.get("flag","")[:40],
                            rf.get("description","")[:80], rf.get("remediation","")[:80]])
        t4 = Table(rf_rows, colWidths=[0.7*inch,1.4*inch,2.5*inch,2.0*inch])
        t4.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTSIZE",(0,0),(-1,-1),7.5),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fafc")]),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        flow.append(t4)
    else:
        flow.append(Paragraph("No risk flags detected.", nm))
    flow.append(Spacer(1,8))

    # ── 5. Missing Clauses ────────────────────────────────────────────────────
    missing = contract.get("missing_clauses", [])
    flow.append(Paragraph("5. Missing Protections", h2))
    if missing:
        for m in missing:
            flow.append(Paragraph(f"⚠ {m} — clause absent from document", nm))
    else:
        flow.append(Paragraph("All standard clauses present.", nm))
    flow.append(Spacer(1,8))

    # ── 6. Executive Summary ──────────────────────────────────────────────────
    es = contract.get("executive_summary", {})
    flow.append(Paragraph("6. Executive Summary", h2))
    if es:
        snap = es.get("contract_snapshot", {})
        if snap:
            flow.append(Paragraph("Contract Snapshot", h3))
            for k, v in snap.items():
                flow.append(Paragraph(f"<b>{k.replace('_',' ').title()}:</b> {v}", nm))
        top_risks = es.get("top_risks", [])
        if top_risks:
            flow.append(Paragraph("Top Risks", h3))
            for r in top_risks[:5]:
                flow.append(Paragraph(f"[{r.get('severity','').upper()}] {r.get('flag','')}: {r.get('impact','')}", nm))
        actions = es.get("recommended_actions", [])
        if actions:
            flow.append(Paragraph("Recommended Actions", h3))
            for a in actions[:6]:
                flow.append(Paragraph(f"• {a.get('action','')} (Owner: {a.get('owner','')}, Priority: {a.get('priority','')})", nm))
    flow.append(Spacer(1,8))

    # ── 7. Section Summaries ──────────────────────────────────────────────────
    flow.append(Paragraph("7. Section Summaries", h2))
    for s in contract.get("section_summaries", []):
        flow.append(Paragraph(f"{s.get('section','').upper()}  [{s.get('risk','').upper()}]", h3))
        flow.append(Paragraph(s.get("summary",""), nm))
        for b in s.get("bullets", []):
            flow.append(Paragraph(f"  • {b}", sm))
    flow.append(Spacer(1,8))

    # ── 8. Compliance Tasks ───────────────────────────────────────────────────
    tasks = contract.get("compliance_tasks", [])
    flow.append(Paragraph("8. Compliance Tasks", h2))
    if tasks:
        task_rows = [["Task","Owner","Due Date","Recurrence","Citation"]]
        for tk in tasks:
            task_rows.append([tk.get("task","")[:60], tk.get("owner",""), tk.get("due_date",""),
                              tk.get("recurrence",""), tk.get("citation","")[:30]])
        t5 = Table(task_rows, colWidths=[2.5*inch,1.0*inch,0.9*inch,0.9*inch,1.3*inch])
        t5.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTSIZE",(0,0),(-1,-1),7.5),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fafc")]),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        flow.append(t5)
    else:
        flow.append(Paragraph("No compliance tasks extracted.", nm))
    flow.append(Spacer(1,8))

    # ── 9. Policy Conflicts & Security ────────────────────────────────────────
    flow.append(Paragraph("9. Policy Conflicts", h2))
    for cf in contract.get("conflicts", []):
        flow.append(Paragraph(f"[{cf.get('severity','').upper()}] {cf.get('clause_section','')}: {cf.get('issue','')}", nm))
        flow.append(Paragraph(f"  ↳ {cf.get('recommendation','')}", sm))
    if not contract.get("conflicts"):
        flow.append(Paragraph("No policy conflicts detected.", nm))

    flow.append(Paragraph("10. Security & Compliance Findings", h2))
    for sf in contract.get("security", []):
        flow.append(Paragraph(f"[{sf.get('severity','').upper()}] {sf.get('category','')}: {sf.get('issue','')}", nm))
        flow.append(Paragraph(f"  ↳ {sf.get('recommendation','')}", sm))
    if not contract.get("security"):
        flow.append(Paragraph("No security findings.", nm))

    doc.build(flow)
    return buf.getvalue()


# ─── CSV ──────────────────────────────────────────────────────────────────────
def contract_to_csv(contract: Dict[str, Any]) -> bytes:
    buf = io.StringIO()
    w   = csv.writer(buf)

    w.writerow(["=== CONTRACT METADATA ==="])
    w.writerow(["Field","Value","Source","Confidence","Type"])
    meta = contract.get("contract_metadata", {})
    for k, obj in meta.items():
        if isinstance(obj, dict):
            w.writerow([k, obj.get("value",""), obj.get("source",""), obj.get("confidence",""), obj.get("type","")])
    w.writerow([])

    w.writerow(["=== SLA SUMMARY ==="])
    sla = contract.get("sla_summary", {})
    for k, v in sla.items():
        if not isinstance(v, list):
            w.writerow([k, v])
        else:
            w.writerow([k, "; ".join(v)])
    w.writerow([])

    w.writerow(["=== MAINTENANCE SCOPE ==="])
    scope = contract.get("maintenance_scope", {})
    w.writerow(["IN SCOPE"] + scope.get("in_scope",[]))
    w.writerow(["OUT OF SCOPE"] + scope.get("out_of_scope",[]))
    w.writerow([])

    w.writerow(["=== RISK FLAGS ==="])
    w.writerow(["Severity","Flag","Description","Citation","Remediation"])
    for rf in contract.get("risk_flags",[]):
        w.writerow([rf.get("severity"), rf.get("flag"), rf.get("description"), rf.get("citation"), rf.get("remediation")])
    w.writerow([])

    w.writerow(["=== MISSING CLAUSES ==="])
    for m in contract.get("missing_clauses",[]):
        w.writerow([m])
    w.writerow([])

    w.writerow(["=== COMPLIANCE TASKS ==="])
    w.writerow(["Task","Owner","Due Date","Recurrence","Citation"])
    for tk in contract.get("compliance_tasks",[]):
        w.writerow([tk.get("task"), tk.get("owner"), tk.get("due_date"), tk.get("recurrence"), tk.get("citation")])
    w.writerow([])

    w.writerow(["=== KEY DATES ==="])
    w.writerow(["Label","Date","Page"])
    for d in contract.get("key_dates",[]):
        w.writerow([d.get("label"), d.get("date"), d.get("page")])
    w.writerow([])

    w.writerow(["=== OBLIGATIONS ==="])
    w.writerow(["Party","Obligation","Due","Page"])
    for o in contract.get("obligations",[]):
        w.writerow([o.get("party"), o.get("obligation"), o.get("due"), o.get("page")])
    w.writerow([])

    w.writerow(["=== CLAUSES ==="])
    w.writerow(["Section","Title","Summary","Risk","Risk Reason","Page"])
    for c in contract.get("clauses",[]):
        w.writerow([c.get("section"), c.get("title"), c.get("summary"),
                    c.get("risk"), c.get("risk_reason",""), c.get("page")])
    w.writerow([])

    w.writerow(["=== POLICY CONFLICTS ==="])
    w.writerow(["Section","Issue","Severity","Recommendation"])
    for cf in contract.get("conflicts",[]):
        w.writerow([cf.get("clause_section"), cf.get("issue"), cf.get("severity"), cf.get("recommendation")])
    w.writerow([])

    w.writerow(["=== SECURITY FINDINGS ==="])
    w.writerow(["Category","Issue","Severity","Recommendation"])
    for sf in contract.get("security",[]):
        w.writerow([sf.get("category"), sf.get("issue"), sf.get("severity"), sf.get("recommendation")])

    return buf.getvalue().encode("utf-8")


# ─── JSON ─────────────────────────────────────────────────────────────────────
def contract_to_json(contract: Dict[str, Any]) -> bytes:
    export = {k: v for k, v in contract.items() if k != "raw_text"}
    return json.dumps(export, indent=2, default=str).encode("utf-8")
