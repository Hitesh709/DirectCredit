from datetime import datetime, timedelta, timezone
import base64, hashlib, hmac, json
from typing import Optional
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .db_models import CustomerRecord

SECRET = settings.directcredit_secret
if not SECRET:
    SECRET = "local-development-only-change-me"


def hash_password(password: str) -> str:
    salt = __import__("os").urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return hmac.compare_digest(candidate, digest)
    except ValueError:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(user_id: int, role: str, token_type: str, hours: int | None = None, session_version: int | None = None) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    token_hours = hours if hours is not None else settings.access_token_hours
    exp = int((datetime.now(timezone.utc) + timedelta(hours=token_hours)).timestamp())
    claims = {"sub": str(user_id), "user_id": user_id, "role": role, "type": token_type, "exp": exp}
    if session_version is not None:
        claims["session_version"] = int(session_version)
    payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    sig = _b64(hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def issue_demo_token(user_id: int, role: str) -> str:
    return issue_token(user_id, role, "access")


def revoke_token(token: str) -> None:
    return None


def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    try:
        header, payload, signature = token.split(".", 2)
        expected = _b64(hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        if expected_type and claims.get("type") != expected_type:
            return None
        return claims
    except Exception:
        return None


def get_current_customer(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Customer authentication required")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_token(token, expected_type="access")
    if not claims or claims.get("role") != "customer" or "session_version" not in claims:
        raise HTTPException(401, "Invalid or expired customer session")
    customer = db.get(CustomerRecord, int(claims["user_id"]))
    if not customer or int(claims["session_version"]) != int(customer.session_version or 1):
        raise HTTPException(401, "Customer session has been revoked")
    return claims
