# 📄 ContractSense — AI Contract Intelligence Platform

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![AI/NLP](https://img.shields.io/badge/AI%2FNLP-FF6F00?style=flat-square&logo=googlegemini&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Search-8A2BE2?style=flat-square)
![Status](https://img.shields.io/badge/Version-3.0.1-blue?style=flat-square)

> A full-stack AI platform that parses IT outsourcing & maintenance contracts, generates structured summaries, highlights critical clauses and dates, and enables intelligent Q&A — purpose-built for IT teams managing vendor contracts.

---

## 🌟 Key Features

### 🤖 AI-Powered Analysis
- **17-clause extraction** with risk ratings — Critical / High / Medium / Low
- **14 metadata fields** — Vendor, Client, TCV, SLA, Cyber Insurance, Auto-Renewal, Cloud Providers
- **Executive summary** — Board-level contract snapshot, SLA commitments, exit readiness, recommended actions
- **Missing clause detection** — Force Majeure, DR/BCP, Audit Rights, IP Ownership, and more
- **AI clause recommendations** — Per-clause improvement suggestions with one-click apply
- **Policy conflict detection** — Cross-contract conflict identification with governing clause resolution

### 📊 Smart Document Management
- Side-by-side document + summary split view with synchronized navigation
- Editable summary fields with tracked change auditability
- Risk heatmap with severity-ranked flags and remediation guidance
- Compliance task auto-generation with owner, due date, and recurrence

### 💬 Intelligent Q&A
- **RAG-powered legal chatbot** grounded in your uploaded contracts
- **Semantic vector search** across all contracts via ChromaDB
- **Renewal diff** — Compare old vs. new contract versions side by side

### 📤 Export Options
| Format | Contents |
|--------|----------|
| PDF | Full report — metadata, SLA summary, risk heatmap, compliance tasks |
| CSV | All structured fields in spreadsheet format |
| JSON | Complete contract data for system integrations |
| Clipboard | One-click summary copy |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│  Dashboard │ Contract View │ Chat │ Renewals │ Upload │
└────────────────────────┬────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────▼────────────────────────────┐
│                  Backend (FastAPI)                   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │              AI Agent Pipeline               │   │
│  │  Parser → Clause Extractor → Summarizer      │   │
│  │  → Executive Summary → Recommender → QA      │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │  SQLite   │  │  ChromaDB   │  │  LLM Client  │  │
│  │  Storage  │  │Vector Store │  │  (GenAI API) │  │
│  └───────────┘  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
contract-clause-summarizer/
├── backend/
│   ├── agents/
│   │   ├── clause_extractor.py       # 17-clause extraction with risk ratings
│   │   ├── executive_summary_agent.py # Board-level summary generation
│   │   ├── summarizer_agent.py
│   │   ├── qa_agent.py               # RAG-powered Q&A
│   │   ├── policy_conflict_agent.py
│   │   ├── recommender_agent.py
│   │   └── renewal_diff_agent.py
│   ├── api/
│   │   ├── contracts.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── ws.py                     # WebSocket for real-time progress
│   └── services/
│       ├── llm_client.py
│       ├── vector_store.py           # ChromaDB integration
│       └── doc_export.py             # PDF/CSV/JSON export
├── frontend/
│   └── src/app/
│       ├── dashboard/
│       ├── contracts/[id]/           # Contract detail + split view
│       ├── upload/
│       ├── chat/
│       └── renewals/
└── data/
    ├── contracts/
    ├── company_policies/
    └── samples/
```

---

## 🚀 Getting Started

**Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env .env.local   # Set GENAI_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend Setup**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

**Demo Login**
```
Developer role:  dev@example.ai   / developer123
Legal role:      legal@example.ai / legal123
```

---

## 💡 Key Concepts Demonstrated

- Full-stack AI application with Python (FastAPI) + TypeScript (Next.js)
- RAG (Retrieval-Augmented Generation) pipeline with ChromaDB vector store
- Multi-agent AI architecture — 9 specialized agents
- Real-time WebSocket progress tracking
- JWT-based role authentication (Dev vs Legal roles)
- PDF/CSV/JSON export with rich formatting
- NLP-based clause extraction and risk classification

---

## 🔗 Tech Stack

`Python` `FastAPI` `TypeScript` `Next.js` `ChromaDB` `SQLite` `GenAI API` `RAG` `NLP` `WebSocket` `JWT`

---

## 👩‍💻 Author

**Akhila Kurre** — Data Engineer @ TCS

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/akhila-kurre-75582a1bb/)
[![GitHub](https://img.shields.io/badge/GitHub-akhila8978-181717?style=flat-square&logo=github)](https://github.com/akhila8978)
