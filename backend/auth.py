from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Optional
from fastapi import Header, HTTPException

SECRET = os.getenv("DIRECTCREDIT_SECRET", "change-this-in-render")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "24"))

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"{salt}${digest}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(candidate, digest)
    except ValueError:
        return False

def issue_demo_token(user_id: int, role: str) -> str:
    expires = int((datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).timestamp())
    payload = f"{user_id}:{role}:{expires}"
    signature = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"demo.{payload}.{signature}"

def decode_demo_token(token: str) -> Optional[dict]:
    try:
        prefix, payload, signature = token.split(".", 2)
        if prefix != "demo":
            return None
        expected = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        user_id, role, expires = payload.split(":", 2)
        if int(expires) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return {"user_id": int(user_id), "role": role}
    except (ValueError, TypeError):
        return None

def get_current_customer(authorization: Optional[str] = Header(default=None)) -> dict:
    """Resolve the customer identity from the signed bearer session token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Customer authentication required")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_demo_token(token)
    if not claims or claims.get("role") != "customer":
        raise HTTPException(status_code=401, detail="Invalid or expired customer session")
    return claims
