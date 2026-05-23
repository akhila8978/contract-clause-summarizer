# Data folder — drop your datasets here

Subfolders are watched by the `/api/rag/reindex` endpoint. Drop PDFs, DOCX, TXT,
or MD files into the appropriate folder, then click **"Reindex /data folder"**
on the Dashboard to ingest them into ChromaDB.

```
data/
├── company_policies/    ← internal policies you want contracts checked against
├── contracts/
│   └── existing/        ← historical signed contracts (per-company subfolders OK)
├── contract_renewals/   ← renewal templates / prior renewals
├── requirements/        ← maintenance requirements, SOWs
├── change_requests/     ← CR documents that affected contracts
└── samples/             ← small seed files so a fresh install works out of the box
```

Indexing uses `text-embedding-3-large` via the GenAILab gateway.
