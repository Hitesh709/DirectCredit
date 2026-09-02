"""Task 8: immutable-style audit event service for loan lifecycle traceability."""
from __future__ import annotations

import json
from uuid import uuid4
from sqlalchemy.orm import Session
from .db_models import AuditEventRecord

SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "refresh_token", "authorization", "aadhaar", "aadhaar_number", "otp", "secret", "api_key"}

def _redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value

def record_event(db: Session, *, actor_type: str, action: str, entity_type: str, entity_id=None,
                 actor_id=None, customer_id=None, loan_id=None, request_id=None,
                 source="api", outcome="success", reason_code=None, details=None,
                 ip_address=None, user_agent=None) -> AuditEventRecord:
    event = AuditEventRecord(
        event_id=str(uuid4()), actor_type=str(actor_type), actor_id=str(actor_id) if actor_id is not None else None,
        action=str(action), entity_type=str(entity_type), entity_id=str(entity_id) if entity_id is not None else None,
        customer_id=customer_id, loan_id=loan_id, request_id=request_id, source=str(source),
        outcome=str(outcome), reason_code=reason_code,
        details=json.dumps(_redact(details), ensure_ascii=False, default=str) if details is not None else None,
        ip_address=ip_address, user_agent=user_agent,
    )
    db.add(event)
    db.flush()
    return event

def audit_request_context(request, claims=None):
    claims = claims or {}
    return {
        "actor_type": str(claims.get("role") or claims.get("user_type") or "anonymous"),
        "actor_id": claims.get("user_id"),
        "request_id": getattr(getattr(request, "state", None), "request_id", None),
        "ip_address": getattr(getattr(request, "client", None), "host", None),
        "user_agent": request.headers.get("user-agent") if request is not None else None,
    }
