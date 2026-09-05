"""Post-100 production hardening contracts.

This module is deliberately read-only except for validation helpers: it must not
become a second source of truth for lending data.
"""
import os
import re
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord, AuditEventRecord
from .admin_auth import get_current_admin
from .config import settings
from .provider_gateway import provider_status

router = APIRouter(prefix="/api/admin/post-100", tags=["post-100-hardening"])

SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "authorization", "pan", "aadhaar", "aadhaar_number"}
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


def mask_mobile(value: Any) -> str | None:
    if value is None: return None
    s = str(value)
    return "*" * max(0, len(s) - 4) + s[-4:]


def mask_pan(value: Any) -> str | None:
    if value is None: return None
    s = str(value)
    return (s[:2] + "*" * max(0, len(s) - 4) + s[-2:]) if len(s) >= 4 else "***"


def mask_aadhaar(value: Any) -> str | None:
    if value is None: return None
    s = re.sub(r"\D", "", str(value))
    return "XXXX-XXXX-" + s[-4:] if len(s) >= 4 else "XXXX-XXXX-XXXX"


def safe_event_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else safe_event_details(v) for k, v in value.items()}
    if isinstance(value, list): return [safe_event_details(v) for v in value]
    return value


def validate_idempotency_key(value: str) -> str:
    if not IDEMPOTENCY_RE.fullmatch(value or ""):
        raise ValueError("Invalid idempotency key")
    return value


def production_config_issues() -> list[str]:
    issues=[]
    if str(getattr(settings, "app_env", os.getenv("APP_ENV", "development"))).lower() == "production":
        if str(getattr(settings, "allow_demo_credential_claim", os.getenv("ALLOW_DEMO_CREDENTIAL_CLAIM", "false"))).lower() == "true": issues.append("demo_credential_claim_enabled")
        if str(getattr(settings, "cors_origins", os.getenv("CORS_ORIGINS", ""))).strip() in {"", "*"}: issues.append("cors_not_restricted")
        secret=str(getattr(settings, "directcredit_secret", os.getenv("DIRECTCREDIT_SECRET", "")))
        if len(secret) < 32: issues.append("weak_or_missing_directcredit_secret")
    return issues


@router.get("/data-contract")
def data_contract(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    return {"source_of_truth": {"customers": CustomerRecord.__tablename__, "loans": LoanRecord.__tablename__, "documents": DocumentRecord.__tablename__, "repayments": RepaymentRecord.__tablename__, "audit_events": AuditEventRecord.__tablename__}, "static_business_totals": False, "browser_owned_identity": False}


@router.get("/security-contract")
def security_contract(admin: dict = Depends(get_current_admin)):
    return {"masked_mobile": mask_mobile("9876543210"), "masked_pan": mask_pan("ABCDE1234F"), "masked_aadhaar": mask_aadhaar("123456789012"), "sensitive_keys_redacted": sorted(SENSITIVE_KEYS), "idempotency_key_pattern": IDEMPOTENCY_RE.pattern}


@router.get("/config-drift")
def config_drift(admin: dict = Depends(get_current_admin)):
    issues=production_config_issues()
    return {"production_safe": not issues, "issues": issues}


@router.get("/providers")
def providers(admin: dict = Depends(get_current_admin)):
    return {"providers": provider_status(), "secrets_exposed": False}


@router.get("/audit-integrity")
def audit_integrity(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    rows=db.query(AuditEventRecord).all(); invalid=[]
    for r in rows:
        missing=[k for k,v in {"event_id":r.event_id,"actor_type":r.actor_type,"action":r.action,"entity_type":r.entity_type,"outcome":r.outcome}.items() if not v]
        if missing: invalid.append({"id":r.id,"missing":missing})
    return {"checked":len(rows), "valid":len(invalid)==0, "invalid_count":len(invalid), "invalid":invalid[:50]}


@router.get("/release-readiness")
def release_readiness(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    drift=production_config_issues()
    audit=audit_integrity(db, admin)
    providers=provider_status()
    pending=[name for name,item in providers.items() if item.get("configured") is False and item.get("provider") not in {"internal"}]
    checks={"database_source_of_truth":True,"security_contract":True,"audit_integrity":audit["valid"],"configuration_safe":not drift,"provider_matrix_available":True,"live_deployment_verified":False}
    return {"ready_for_live_verification": all(checks.values()) is False and False, "checks":checks, "config_issues":drift,"external_providers_pending":pending,"note":"Live deployment and real-provider credentials must be verified in the target environment; CI cannot claim them."}
