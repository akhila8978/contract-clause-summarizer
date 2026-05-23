"""Rule-based fallback analyzers.

If the LLM gateway returns empty (e.g. blocked by content filter, network
error, or invalid JSON), these heuristics produce a still-useful result so
the UI never shows a blank contract. They use simple regex/keyword passes
over the raw contract text.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple

# Section keywords -> (section_key, title, default_risk)
SECTION_PATTERNS: List[Tuple[str, str, str, str]] = [
    (r"\bparties?\b|\bbetween\b.*\band\b", "parties", "Parties", "low"),
    (r"\bterm\b|\beffective date\b|\bcommencement\b|\bduration\b", "term", "Term & Effective Date", "low"),
    (r"\bpayment|\bfees?\b|\binvoice\b|\bcompensation\b", "payment", "Payment Terms", "medium"),
    (r"\bsla\b|\bservice level\b|\buptime\b|\bresponse time\b|\bresolution time\b", "sla", "Service Level Agreement", "high"),
    (r"\bliabilit", "liability", "Limitation of Liability", "high"),
    (r"\bindemnif", "indemnity", "Indemnification", "high"),
    (r"\bintellectual property\b|\bip rights?\b|\bownership of\b", "ip", "Intellectual Property", "medium"),
    (r"\bconfidential", "confidentiality", "Confidentiality", "medium"),
    (r"\bdata protection\b|\bgdpr\b|\bdpa\b|\bpersonal data\b", "data_protection", "Data Protection", "high"),
    (r"\bsecurity\b|\bencrypt|\baccess control\b|\baudit\b", "security", "Security", "high"),
    (r"\btermination\b|\bterminate\b", "termination", "Termination", "medium"),
    (r"\brenewal\b|\bauto[- ]?renew", "renewal", "Renewal", "medium"),
    (r"\bgoverning law\b|\bjurisdiction\b", "governing_law", "Governing Law", "low"),
]

DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{4}[/-]\d{1,2}[/-]\d{1,2}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
    r"|\d+\s+(?:days?|weeks?|months?|years?)"
    r")\b",
    re.IGNORECASE,
)

MONEY_RE = re.compile(r"(?:USD|INR|EUR|GBP|Rs\.?|\$|₹|€|£)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)


def _sentences(text: str) -> List[str]:
    # naive sentence split
    parts = re.split(r"(?<=[\.\!\?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def _excerpt(sent: str, limit: int = 280) -> str:
    s = re.sub(r"\s+", " ", sent).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def heuristic_extract(text: str, pages: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Build a clause list + key dates + obligations from raw text."""
    if not text:
        return {"clauses": [], "key_dates": [], "obligations": []}
    sents = _sentences(text)
    page_map = pages or []

    def page_of(snippet: str) -> int | None:
        if not page_map:
            return 1
        for pg in page_map:
            if snippet[:60] and snippet[:60] in pg.get("text", ""):
                return pg.get("page")
        return page_map[0].get("page", 1) if page_map else None

    found: Dict[str, Dict[str, Any]] = {}
    for sent in sents:
        for pat, key, title, default_risk in SECTION_PATTERNS:
            if key in found:
                continue
            if re.search(pat, sent, re.IGNORECASE):
                # build summary from this and the next sentence if short
                idx = sents.index(sent)
                snippet = " ".join(sents[idx : idx + 2])[:600]
                found[key] = {
                    "section": key,
                    "title": title,
                    "summary": _excerpt(snippet, 240),
                    "source_excerpt": _excerpt(sent, 280),
                    "page": page_of(sent),
                    "risk": default_risk,
                }
                break

    # key dates
    key_dates: List[Dict[str, Any]] = []
    seen_dates = set()
    for sent in sents:
        for m in DATE_RE.finditer(sent):
            d = m.group(0)
            if d.lower() in seen_dates:
                continue
            seen_dates.add(d.lower())
            label = "Key date"
            low = sent.lower()
            if "effective" in low:
                label = "Effective date"
            elif "renew" in low:
                label = "Renewal date"
            elif "terminat" in low:
                label = "Termination notice"
            elif "expir" in low:
                label = "Expiry"
            elif "notice" in low:
                label = "Notice period"
            elif "payment" in low or "invoice" in low or "due" in low:
                label = "Payment due"
            key_dates.append({"label": label, "date": d, "page": page_of(sent)})
            if len(key_dates) >= 8:
                break
        if len(key_dates) >= 8:
            break

    # obligations: sentences with "shall"
    obligations: List[Dict[str, Any]] = []
    for sent in sents:
        if re.search(r"\b(shall|must|will|agrees to|is responsible for)\b", sent, re.IGNORECASE):
            low = sent.lower()
            party = "Vendor" if "vendor" in low or "supplier" in low or "service provider" in low else (
                "Customer" if "customer" in low or "client" in low else "Party"
            )
            obligations.append({
                "party": party,
                "obligation": _excerpt(sent, 220),
                "due": None,
                "page": page_of(sent),
            })
            if len(obligations) >= 10:
                break

    return {
        "clauses": list(found.values()),
        "key_dates": key_dates,
        "obligations": obligations,
    }


def heuristic_summaries(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for cl in clauses:
        text = cl.get("source_excerpt", "") or cl.get("summary", "")
        sents = _sentences(text)[:3] or [text]
        bullets: List[str] = []
        for s in sents:
            s = _excerpt(s, 180)
            if s and s not in bullets:
                bullets.append(s)
        # add useful structured bullets
        money = MONEY_RE.findall(text)
        if money:
            bullets.append("Financial figure mentioned: " + ", ".join(sorted(set(money))[:3]))
        dates = DATE_RE.findall(text)
        if dates:
            bullets.append("Date/period mentioned: " + ", ".join(sorted({d for d in dates})[:3]))
        out.append({
            "section": cl.get("section", ""),
            "summary": cl.get("summary", "") or _excerpt(text, 220),
            "bullets": bullets[:5],
            "risk": cl.get("risk", "low"),
        })
    return out


# Generic conflict rules: trigger when a clause section's text contains
# RED_RE patterns AND the policy keyword applies.
POLICY_RULES: List[Dict[str, Any]] = [
    {
        "section": "sla",
        "red": r"(99\.[0-4]\s*%|98\s*%|95\s*%|best[- ]effort|reasonable efforts?|commercially reasonable)",
        "issue": "SLA uptime is below the company's 99.5% minimum or uses vague 'reasonable effort' language.",
        "rec": "Require ≥ 99.5% monthly uptime with clearly defined response and resolution SLAs and service credits.",
        "severity": "high",
    },
    {
        "section": "data_protection",
        "red": r"(retain|retention|store|keep)[^.]{0,40}(indefinitely|permanently|forever)",
        "issue": "Data retention period is indefinite, which conflicts with the data-minimisation policy (term + 90 days).",
        "rec": "Cap retention to the contract term + 90 days and require secure deletion thereafter.",
        "severity": "high",
    },
    {
        "section": "security",
        "red": r"(sole discretion|without notice|no\s+(?:audit|encryption)|commercially reasonable security)",
        "issue": "Security provisions are weakened by unilateral discretion or absence of audit/encryption obligations.",
        "rec": "Mandate AES-256 at rest, TLS 1.2+ in transit, and annual independent audit rights for the customer.",
        "severity": "high",
    },
    {
        "section": "liability",
        "red": r"(unlimited liability|liability is unlimited|no (?:cap|limitation) on liability)",
        "issue": "Liability is uncapped, exceeding the company's standard 12-month-fees cap.",
        "rec": "Cap aggregate liability at 12 months of fees paid, with carve-outs for IP indemnity and confidentiality.",
        "severity": "high",
    },
    {
        "section": "termination",
        "red": r"(may not terminate.*for convenience|no termination for convenience|180\s*days?|120\s*days?|90\s*days?\s+(?:written\s+)?notice)",
        "issue": "Termination notice exceeds the 30-day policy or termination for convenience is excluded.",
        "rec": "Allow termination for convenience with 30 days' written notice.",
        "severity": "medium",
    },
    {
        "section": "payment",
        "red": r"(net[\s-]*(?:60|90|120)|sixty\s*\(?60\)?\s*days|ninety\s*\(?90\)?\s*days|advance payment|payable in advance|in advance)",
        "issue": "Payment terms exceed the Net-30 policy or require upfront/advance payment.",
        "rec": "Standardise to Net-30 from invoice date; avoid advance payment requirements.",
        "severity": "medium",
    },
]


def heuristic_conflicts(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for cl in clauses:
        text = (cl.get("source_excerpt", "") + " " + cl.get("summary", "")).lower()
        for rule in POLICY_RULES:
            if rule["section"] != cl.get("section"):
                continue
            if re.search(rule["red"], text, re.IGNORECASE):
                findings.append({
                    "clause_section": cl.get("section", ""),
                    "clause_excerpt": cl.get("source_excerpt", ""),
                    "policy_excerpt": "Company policy",
                    "issue": rule["issue"],
                    "severity": rule["severity"],
                    "recommendation": rule["rec"],
                })
    return findings


SECURITY_CHECKS: List[Dict[str, Any]] = [
    {
        "needle": r"\b(encrypt|aes[- ]?256|tls)\b",
        "absent_category": "Encryption",
        "absent_issue": "No explicit encryption requirement found (at-rest or in-transit).",
        "absent_rec": "Add: 'Data shall be encrypted at rest (AES-256) and in transit (TLS 1.2 or higher).'",
        "severity": "high",
    },
    {
        "needle": r"\b(breach (?:notice|notification)|notify within \d+|incident response)\b",
        "absent_category": "Breach notification",
        "absent_issue": "No breach-notification timeline is specified.",
        "absent_rec": "Require notification within 24-72 hours of confirmed incident.",
        "severity": "high",
    },
    {
        "needle": r"\b(audit|right to inspect|sox|iso 27001)\b",
        "absent_category": "Audit rights",
        "absent_issue": "Customer audit / inspection rights are not granted.",
        "absent_rec": "Grant customer the right to audit security controls at least annually.",
        "severity": "medium",
    },
    {
        "needle": r"\b(subprocessor|sub[- ]?contractor|third[- ]?party)\b",
        "absent_category": "Subprocessors",
        "absent_issue": "Subprocessor / subcontractor obligations are not described.",
        "absent_rec": "Require prior written approval and equivalent obligations for any subprocessor.",
        "severity": "medium",
    },
    {
        "needle": r"\b(retain|retention|deletion)\b",
        "absent_category": "Data retention",
        "absent_issue": "Data retention and deletion policy is not defined.",
        "absent_rec": "Specify retention period and a deletion/return obligation upon termination.",
        "severity": "medium",
    },
]


def heuristic_security(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    low = (text or "").lower()
    for chk in SECURITY_CHECKS:
        if not re.search(chk["needle"], low, re.IGNORECASE):
            out.append({
                "category": chk["absent_category"],
                "issue": chk["absent_issue"],
                "clause_excerpt": "",
                "severity": chk["severity"],
                "recommendation": chk["absent_rec"],
            })
    return out


def heuristic_qa(question: str, contract_text: str) -> str:
    """Tiny extractive QA: return the 2-3 sentences most relevant to the
    question's keywords. Used when the LLM gateway returns nothing."""
    if not contract_text:
        return "I can't find that in the provided documents."
    q_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", question)}
    if not q_words:
        return "Please ask a more specific question."
    sents = _sentences(contract_text)
    scored = []
    for s in sents:
        words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", s)}
        score = len(q_words & words)
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    top = [s for _, s in scored[:3]]
    if not top:
        return "I can't find that in the provided documents."
    return " ".join(_excerpt(s, 320) for s in top)
