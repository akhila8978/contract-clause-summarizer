from __future__ import annotations
import logging
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, contracts, policies, renewals, chat, clauses, rag, ws
from services.seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Contract Clause Summarizer", version="2.0.0")

origins = [
    "http://localhost:3000", "http://localhost:3001", "http://localhost:3002",
    "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    try:
        seed_if_empty()
    except Exception as e:
        logging.getLogger("startup").warning("Seeding failed: %s", e)


@app.get("/")
def root():
    return {"app": "Contract Clause Summarizer", "status": "ok"}


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(policies.router)
app.include_router(renewals.router)
app.include_router(chat.router)
app.include_router(clauses.router)
app.include_router(rag.router)
app.include_router(ws.router)
