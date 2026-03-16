import logging
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Header, HTTPException, Request
import jwt
from passlib.context import CryptContext

from config import settings
from database import db

logger = logging.getLogger("security")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, role: str = "user", expiry_hours: int = None) -> str:
    exp = expiry_hours or settings.JWT_EXPIRY_HOURS
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=exp),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(authorization.split(" ")[1])
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")
    if user.get("status") == "banned":
        raise HTTPException(status_code=403, detail="Account banned")
    return user


async def get_optional_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = verify_token(authorization.split(" ")[1])
        return await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    except Exception:
        return None


async def get_admin_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(authorization.split(" ")[1])
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


# --- Security Audit Logger ---

async def audit_log(event: str, details: dict = None, user_id: str = None, ip: str = None):
    """Log security-relevant events to the database for audit trail."""
    entry = {
        "event": event,
        "user_id": user_id,
        "ip": ip or "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    try:
        await db.audit_log.insert_one(entry)
    except Exception:
        pass
    # Also log to stdout for immediate visibility
    logger.info(json.dumps({"audit": event, "user_id": user_id, "ip": ip, **(details or {})}))
