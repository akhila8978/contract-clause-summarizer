from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class Clause(BaseModel):
    section: str
    title: str
    summary: str
    source_excerpt: str
    page: Optional[int] = None
    risk: str = "low"


class KeyDate(BaseModel):
    label: str
    date: str
    page: Optional[int] = None


class Obligation(BaseModel):
    party: str
    obligation: str
    due: Optional[str] = None
    page: Optional[int] = None


class Conflict(BaseModel):
    clause_section: str
    clause_excerpt: str
    policy_excerpt: str
    issue: str
    severity: str
    recommendation: str


class SecurityFinding(BaseModel):
    category: str
    issue: str
    clause_excerpt: Optional[str] = ""
    severity: str
    recommendation: str


class SectionSummary(BaseModel):
    section: str
    summary: str
    bullets: List[str] = []
    risk: str = "low"


class ChatMessageIn(BaseModel):
    contract_id: Optional[str] = None
    session_id: str
    message: str


class RecommendRequest(BaseModel):
    contract_id: str
    clause_section: str
    current_text: str


class ApplyFixRequest(BaseModel):
    contract_id: str
    clause_section: str
    original_text: str
    new_text: str


class FeedbackIn(BaseModel):
    target: str  # e.g. "summary", "recommendation"
    target_id: str
    rating: int  # -1 or 1
    comment: Optional[str] = ""
