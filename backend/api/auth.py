from __future__ import annotations
import os
import time
import jwt
from fastapi import APIRouter, HTTPException, Depends, Header
from models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET = os.getenv("JWT_SECRET", "dev-secret")
EXPIRY_H = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

USERS = {
    "dev@example.ai": {"password": "developer123", "name": "Dev User", "role": "admin"},
    "dev": {"password": "developer123", "name": "Dev User", "role": "admin"},
    "legal@example.ai": {"password": "legal123", "name": "Legal Reviewer", "role": "reviewer"},
}


def _make_token(username: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + EXPIRY_H * 3600}
    return jwt.encode(payload, SECRET, algorithm="HS256")


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    u = req.username.strip().lower()
    user = USERS.get(u) or USERS.get(u.split("@")[0])
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=_make_token(u), user={"username": u, "name": user["name"], "role": user["role"]})


def require_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@router.get("/me")
def me(user: dict = Depends(require_user)):
    return {"username": user.get("sub")}
