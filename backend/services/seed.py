"""Preload demo contracts and policies so the UI has content on first launch.

This runs on FastAPI startup. It uses the heuristic extractor (no LLM calls)
so seeding is instant and never blocked by content filters.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List
from services import storage
from utils.heuristics import (
    heuristic_extract,
    heuristic_summaries,
    heuristic_conflicts,
    heuristic_security,
)

log = logging.getLogger("seed")


SAMPLE_CONTRACTS: List[Dict[str, Any]] = [
    {
        "name": "Acme_MSA_2024.pdf",
        "company": "Acme Corporation",
        "text": """MASTER SERVICES AGREEMENT

Between Acme Corporation ("Customer") and ContosoSoft Pvt. Ltd. ("Vendor"), effective 01 January 2024.

1. TERM. This Agreement commences on the Effective Date and shall continue for an initial term of three (3) years, automatically renewing for successive one-year terms unless either party provides 90 days' written notice of non-renewal prior to expiry.

2. SERVICES. Vendor shall provide application maintenance, support, and minor enhancement services for the Customer's enterprise CRM platform. Vendor shall use commercially reasonable efforts to deliver the services.

3. SERVICE LEVEL AGREEMENT. Vendor commits to 99.0% monthly uptime measured calendar-monthly. Severity-1 incident response within 1 hour; resolution within 8 business hours. Service credits of 5% of monthly fee per 1% missed uptime, capped at 25% of monthly fee.

4. PAYMENT. Customer shall pay Vendor INR 12,00,000 per quarter within sixty (60) days of invoice. Late payment incurs 1.5% monthly interest. All taxes are additional.

5. CONFIDENTIALITY. Each party shall protect the other's Confidential Information with reasonable care and shall not disclose it to any third party for a period of three (3) years after termination.

6. DATA PROTECTION. Vendor shall process Personal Data only as instructed by Customer. Vendor may retain backup copies of Customer Data indefinitely for disaster-recovery purposes.

7. SECURITY. Vendor shall maintain commercially reasonable security controls. Vendor reserves the right to make security changes at its sole discretion without notice to Customer.

8. INTELLECTUAL PROPERTY. All pre-existing IP remains with its original owner. Work product developed under this Agreement is owned by Customer upon full payment.

9. LIMITATION OF LIABILITY. Each party's aggregate liability shall not exceed twelve (12) months of fees paid in the twelve months preceding the claim, except for breaches of confidentiality, IP indemnity, and gross negligence.

10. INDEMNIFICATION. Vendor shall indemnify Customer against third-party claims that the Services infringe any IP right.

11. TERMINATION. Either party may terminate for material breach with 30 days' written notice and a cure period. Customer may not terminate this Agreement for convenience during the initial term.

12. GOVERNING LAW. This Agreement is governed by the laws of India. Disputes shall be resolved by arbitration in Mumbai.
""",
    },
    {
        "name": "Globex_AMC_Renewal_2025.pdf",
        "company": "Globex Industries",
        "text": """ANNUAL MAINTENANCE CONTRACT (RENEWAL)

This renewal is entered into between Globex Industries ("Client") and InitechIT Solutions ("Service Provider"), effective 15 March 2025 for a one-year term.

1. SCOPE. Service Provider shall provide L1/L2/L3 application support for Client's ERP modules: Finance, HR, Procurement.

2. SLA. Service Provider commits to 99.7% monthly uptime. P1 response within 30 minutes; resolution within 4 business hours. P2 response within 2 hours; resolution within 12 business hours. Monthly service credits up to 20% of fees for missed SLAs.

3. PAYMENT TERMS. Annual fee of USD 240,000 payable in advance in two equal installments. Net-30 invoice terms.

4. DATA PROTECTION. Service Provider shall comply with the Client's Data Protection Policy. All Personal Data shall be stored within India and shall be deleted within 30 days of contract termination.

5. SECURITY. All data shall be encrypted at rest using AES-256 and in transit using TLS 1.2 or higher. Service Provider shall notify Client of any security incident within 24 hours of confirmation. Client may audit Service Provider's security controls annually.

6. SUBPROCESSORS. Service Provider shall not engage any subcontractor without Client's prior written consent. All subcontractors shall be bound by equivalent obligations.

7. TERMINATION. Either party may terminate for convenience with 30 days' written notice. Either party may terminate immediately upon material breach not cured within 15 days.

8. LIABILITY. Aggregate liability is capped at the fees paid in the prior 12 months. Carve-outs apply for confidentiality, data protection, and IP indemnity.

9. INTELLECTUAL PROPERTY. All deliverables created specifically for Client are Client's property. Service Provider retains its pre-existing tools and frameworks.

10. CONFIDENTIALITY. Three-year survival post-termination. Standard exclusions apply.

11. GOVERNING LAW. Governed by the laws of Karnataka, India. Bengaluru courts have exclusive jurisdiction.
""",
    },
    {
        "name": "Initrode_SupportContract.pdf",
        "company": "Initrode Ltd",
        "text": """IT SUPPORT CONTRACT

Between Initrode Ltd ("Customer") and Vandelay Systems ("Vendor"), dated 10 June 2024, for a term of two (2) years.

1. SERVICES. Vendor provides 24x7 support for Customer's internal web portal and integration middleware.

2. SLA. 99.5% monthly uptime. P1 response 1 hour, resolution 6 business hours.

3. PAYMENT. EUR 8,000 monthly, due Net-90 from invoice date.

4. CONFIDENTIALITY. Standard 5-year confidentiality survival post-termination.

5. SECURITY. Vendor shall apply industry-standard practices. No specific encryption or breach notification timeline is mandated.

6. LIABILITY. Vendor's liability is UNLIMITED for any negligence claim.

7. TERMINATION. 180 days' written notice required for termination for convenience.

8. INTELLECTUAL PROPERTY. All work product remains property of Vendor; Customer receives a perpetual license.

9. GOVERNING LAW. Laws of England and Wales.
""",
    },
]


SAMPLE_POLICIES: List[Dict[str, Any]] = [
    {
        "title": "IT Maintenance SLA Policy",
        "filename": "maintenance_sla_policy.txt",
        "text": """COMPANY POLICY — IT MAINTENANCE SLAs (v3.2)

1. Minimum monthly uptime for production systems: 99.5%.
2. Severity-1 incidents: response within 30 minutes, resolution within 4 business hours.
3. Severity-2 incidents: response within 2 hours, resolution within 12 business hours.
4. Service credits must be specified; minimum 5% of monthly fee per 1% missed uptime.
5. Termination for convenience must be permitted with at most 30 days' notice.
6. Payment terms must be Net-30 or shorter. Advance payments are discouraged.
7. Liability shall be capped at 12 months of fees, with carve-outs for confidentiality, IP indemnity, and data protection.
""",
    },
    {
        "title": "Data Protection & Security Policy",
        "filename": "security_policy.txt",
        "text": """COMPANY POLICY — DATA PROTECTION & SECURITY (v4.1)

1. All customer and personal data shall be encrypted at rest (AES-256) and in transit (TLS 1.2 or higher).
2. Security incident notification: within 24 hours of confirmed incident, within 72 hours at the latest.
3. Customer audit rights: annual independent audit and right to inspect on 10 business days' notice.
4. Subprocessors: require prior written approval; flow-down equivalent obligations.
5. Data retention: limited to the contract term plus 90 days; secure deletion thereafter.
6. Vendors shall maintain ISO 27001 or SOC 2 Type II certification.
7. Personal data shall be stored within approved jurisdictions only.
""",
    },
]


def _build_pages(text: str, page_size: int = 1800) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    i = 0
    p = 1
    while i < len(text):
        chunk = text[i : i + page_size]
        pages.append({"page": p, "text": chunk, "char_start": i})
        i += page_size
        p += 1
    if not pages:
        pages = [{"page": 1, "text": text, "char_start": 0}]
    return pages


def _build_contract(sample: Dict[str, Any]) -> Dict[str, Any]:
    text = sample["text"]
    pages = _build_pages(text)
    extracted = heuristic_extract(text, pages)
    clauses = extracted["clauses"]
    summaries = heuristic_summaries(clauses)
    conflicts = heuristic_conflicts(clauses)
    security = heuristic_security(text)
    cid = storage.new_id("ctr")
    return {
        "id": cid,
        "name": sample["name"],
        "company": sample["company"],
        "uploaded_at": storage.now(),
        "uploaded_by": "demo",
        "pages": pages,
        "raw_text": text,
        "clauses": clauses,
        "section_summaries": summaries,
        "conflicts": conflicts,
        "security": security,
        "key_dates": extracted["key_dates"],
        "obligations": extracted["obligations"],
        "is_demo": True,
    }


def _build_policy(sample: Dict[str, Any]) -> Dict[str, Any]:
    text = sample["text"]
    pages = _build_pages(text)
    pid = storage.new_id("pol")
    return {
        "id": pid,
        "title": sample["title"],
        "filename": sample["filename"],
        "uploaded_at": storage.now(),
        "text": text,
        "pages": pages,
        "is_demo": True,
    }


def seed_if_empty() -> None:
    """Populate storage with demo data if no contracts/policies exist yet."""
    if not storage.CONTRACTS:
        for s in SAMPLE_CONTRACTS:
            c = _build_contract(s)
            storage.CONTRACTS[c["id"]] = c
        log.info("Seeded %d demo contracts", len(SAMPLE_CONTRACTS))
    if not storage.POLICIES:
        for s in SAMPLE_POLICIES:
            p = _build_policy(s)
            storage.POLICIES[p["id"]] = p
        log.info("Seeded %d demo policies", len(SAMPLE_POLICIES))
