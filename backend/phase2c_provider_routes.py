"""Phase 2C external-provider APIs with customer scoping and audit events."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .auth import get_current_customer
from .database import get_db
from .db_models import CustomerRecord, CustomerEventRecord
from .phase1_customer import record_customer_event
from .phase2c_provider_gateway import PROVIDER_KINDS, consent_contract, provider_status, request_provider

router = APIRouter(prefix="/api/v1/providers", tags=["external-providers"])

class ProviderRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = None

class ConsentRequest(BaseModel):
    purpose: str = Field(min_length=3, max_length=500)
    provider: str = "account_aggregator"
    accepted: bool = False
    consent_version: str = "2C-1.0"


def _owner(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")

@router.get("/status")
def status():
    return {"providers": provider_status(), "supported": list(PROVIDER_KINDS)}

@router.get("/{customer_id}/consent-contract")
def get_consent_contract(customer_id: int, purpose: str = "credit_assessment", db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id): raise HTTPException(404, "customer_not_found")
    return consent_contract(customer_id, purpose)

@router.post("/{customer_id}/consent")
def record_consent(customer_id: int, body: ConsentRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id): raise HTTPException(404, "customer_not_found")
    if body.provider not in PROVIDER_KINDS: raise HTTPException(422, "unsupported_provider")
    event = record_customer_event(db, customer_id, "EXTERNAL_DATA_CONSENT", details={
        "provider": body.provider, "purpose": body.purpose, "accepted": body.accepted,
        "consent_version": body.consent_version,
    })
    db.commit()
    return {"status": "ACCEPTED" if body.accepted else "DECLINED", "event_id": event.id if event else None,
            "provider": body.provider, "purpose": body.purpose, "consent_version": body.consent_version}

@router.post("/{customer_id}/{provider}/request")
def request_external_data(customer_id: int, provider: str, body: ProviderRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    if provider not in PROVIDER_KINDS: raise HTTPException(404, "unsupported_provider")
    if not db.get(CustomerRecord, customer_id): raise HTTPException(404, "customer_not_found")
    if provider == "account_aggregator":
        accepted = db.query(CustomerEventRecord).filter(
            CustomerEventRecord.customer_id == customer_id,
            CustomerEventRecord.event_type == "EXTERNAL_DATA_CONSENT",
        ).order_by(CustomerEventRecord.id.desc()).first()
        if not accepted or '"accepted": true' not in str(accepted.details or "").lower():
            raise HTTPException(409, "account_aggregator_consent_required")
    result = request_provider(provider, {"customer_id": customer_id, **body.payload}, body.idempotency_key)
    record_customer_event(db, customer_id, "EXTERNAL_DATA_PROVIDER_RESPONSE", details={
        "provider": provider, "status": result.get("status"), "request_id": result.get("request_id"),
        "provenance": result.get("provenance"), "error": result.get("error"),
        "data_keys": sorted((result.get("data") or {}).keys()),
    })
    db.commit()
    return result
