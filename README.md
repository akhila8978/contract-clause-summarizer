# ContractSense — Contract Intelligence Platform v3.0
## IT Outsourcing & Application Maintenance Contract Analyzer

### Solution Overview

A web-based AI platform that parses IT maintenance contracts, generates structured summaries, highlights critical clauses and dates, and enables intelligent Q&A — all tailored for IT maintenance teams managing vendor contracts.

---

### Bug Fix — v3.0.1 (this release)

**Issue:** `Unhandled Runtime Error — Objects are not valid as a React child (found: object with keys {vendor, client, term, renewal_mechanics, tcv})`

**Root cause:** When the LLM call fails or returns non-JSON output, the backend's heuristic fallback (`executive_summary_agent.py → _heuristic_summary`) returns `contract_snapshot`, `sla_commitments`, and `exit_readiness` as **plain dictionaries**, and `recommended_actions` as an **array of objects** (`{action, owner, priority, citation}`). The frontend's `EditableBlock` component expected these to be plain strings, so React threw when it tried to render the raw objects as children.

**Fix applied (`frontend/src/app/contracts/[id]/page.tsx`):**
- Added `formatEsValue(val: unknown): string` — converts any value (string, object, array) to a human-readable string before it is passed to `EditableBlock`.
- Added `formatRecommendedAction(a: unknown): string` — handles both plain-string and structured-object recommended-action items.
- All six `EditableBlock` usages for `contract_snapshot`, `sla_commitments`, and `exit_readiness` (summary view + split view) now wrap their `value` prop with `formatEsValue(...)`.
- Both `recommended_actions` map callbacks now type-annotate items as `unknown` and call `formatRecommendedAction(a)` instead of rendering `a` directly.

**No backend changes required.** The fix is fully forward-compatible: if the LLM does return a proper string, `formatEsValue` passes it through unchanged.

---

### Key Features (v3.0)

#### 1. Side-by-Side Document & Summary View
- **Split view mode**: Summary panel on the left, source document on the right
- **Synchronized navigation**: Click any clause or date in the summary to jump to the corresponding page in the document
- **Three view modes**: Summary only, Side-by-Side split, or Document only
- **Page selector dropdown** in split view for quick navigation

#### 2. Editable Summary Fields
- **Inline editing**: Hover any metadata field to reveal an edit button
- **Executive summary editing**: All generated text fields (Contract Snapshot, SLA Commitments, Exit Readiness, Recommended Actions) are fully editable
- **Save changes**: Click Save to persist edits via PATCH `/api/contracts/{id}`
- **Tracked edits**: Edited fields are marked with type `"Edited"` for auditability

#### 3. Export Options
- **PDF export**: Rich multi-section report with metadata table, SLA summary, risk heatmap, scope, obligations, and compliance tasks
- **CSV export**: All structured fields in spreadsheet format
- **JSON export**: Complete structured contract data for system integrations
- **Copy to clipboard**: One-click summary copy for pasting into emails/tickets

#### 4. AI Analysis Features
- **Clause extraction**: 17 contract sections with risk rating (critical/high/medium/low)
- **14 metadata fields**: Vendor, Client, TCV, Currency, Governing Law, Cyber Insurance, Auto-Renewal, Named Applications, Cloud Providers, etc.
- **SLA analysis**: Uptime SLA, P1/P2/P3 response & resolution, service credits, penalty cap, exclusions
- **Maintenance scope**: In-Scope vs Out-of-Scope extraction
- **Risk flags**: Severity-ranked with descriptions and remediation guidance
- **Missing clause detection**: Force Majeure, Cyber Insurance, DR/BCP, Audit Rights, Security Incident Notification, Exit Management, IP Ownership
- **Compliance tasks**: Auto-generated with owner, due date, recurrence
- **Executive summary**: Board-level summary with contract snapshot, SLA commitments, exit readiness, recommended actions
- **Policy conflict detection**: Cross-contract clause conflicts with governing clause identification
- **AI clause recommendations**: Per-clause AI suggestions for improvement with one-click apply

#### 5. Document Management
- **Contract list**: Sortable by risk level, end date, or upload date
- **Search**: Filter by name, company, or vendor
- **Risk indicators**: Critical/high badges on list view
- **Dashboard**: Risk summary stats, contracts needing attention, recently uploaded

#### 6. Additional Features
- **Legal Q&A chatbot**: RAG-powered contract Q&A grounded in your documents
- **Renewal diff**: Compare old vs. new contract versions side by side
- **Policy management**: Upload and manage company policies
- **Vector search**: Semantic search across all contracts (ChromaDB)
- **Real-time progress**: WebSocket-powered upload progress with stage tracking
- **Dark/light mode**: System-aware with manual toggle
- **Role-based access**: JWT authentication (dev and legal roles)

---

### Architecture

```
contract-enhanced/
├── backend/
│   ├── agents/
│   │   ├── clause_extractor.py
│   │   ├── executive_summary_agent.py  ← heuristic fallback returns object fields
│   │   ├── summarizer_agent.py
│   │   ├── security_agent.py
│   │   ├── policy_conflict_agent.py
│   │   ├── recommender_agent.py
│   │   ├── qa_agent.py
│   │   ├── renewal_diff_agent.py
│   │   └── parser_agent.py
│   ├── api/
│   │   ├── contracts.py
│   │   ├── auth.py
│   │   ├── policies.py
│   │   ├── renewals.py
│   │   ├── chat.py
│   │   ├── clauses.py
│   │   ├── rag.py
│   │   └── ws.py
│   ├── services/
│   │   ├── doc_export.py
│   │   ├── llm_client.py
│   │   ├── vector_store.py
│   │   ├── storage.py
│   │   ├── ws_manager.py
│   │   └── seed.py
│   └── utils/
│       ├── prompts.py
│       ├── heuristics.py
│       ├── chunker.py
│       ├── pdf_extract.py
│       └── docx_extract.py
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── dashboard/page.tsx
│       │   ├── contracts/page.tsx
│       │   ├── contracts/[id]/page.tsx  ★ FIXED — formatEsValue + formatRecommendedAction
│       │   ├── upload/page.tsx
│       │   ├── renewals/page.tsx
│       │   ├── policies/page.tsx
│       │   ├── chat/page.tsx
│       │   ├── layout.tsx
│       │   └── globals.css
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── ClientShell.tsx
│       │   ├── StreamingPanel.tsx
│       │   ├── FileDrop.tsx
│       │   ├── RiskBadge.tsx
│       │   └── ClarityMeter.tsx
│       └── lib/
│           ├── api.ts
│           ├── authStore.ts
│           ├── theme.ts
│           └── ws.ts
└── data/
    ├── contracts/
    ├── company_policies/
    └── samples/
```

---

### Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env .env.local   # Set GENAI_API_KEY to your API key
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

**Demo Login**
- `dev@example.ai` / `developer123` (Developer role)
- `legal@example.ai` / `legal123` (Legal role)

---

### Document Precedence
When multiple documents are uploaded, conflicts are resolved by:
1. Amendments / Addenda
2. Change Requests
3. SOW
4. SLA
5. MSA

---

### Success Metrics
- **Summary accuracy**: LLM-based extraction with confidence scores and heuristic fallback
- **User satisfaction**: Editable summaries with one-click save; AI recommendations per clause
- **Review time reduction**: Executive summary, risk heatmap, and compliance task list surface critical information instantly
