"""Phase 1 Customer 360 service helpers."""
from __future__ import annotations
import hashlib
import json
from typing import Any
from sqlalchemy.orm import Session
from .db_models import CustomerRecord, CustomerBusinessRecord, CustomerContactRecord, CustomerAddressRecord, CustomerKYCRecord, CustomerBankAccountRecord, CustomerConsentRecord, CustomerPreferenceRecord, CustomerRiskProfileRecord, CustomerEventRecord

def fingerprint(value: str | None) -> str | None:
    if not value: return None
    return hashlib.sha256("".join(str(value).split()).lower().encode()).hexdigest()

def potential_duplicates(db: Session, *, pan=None, mobile=None, email=None, gstin=None):
    matches: set[int] = set()
    if pan: matches.update(x.id for x in db.query(CustomerRecord).filter(CustomerRecord.pan == pan).all())
    if mobile: matches.update(x.id for x in db.query(CustomerRecord).filter(CustomerRecord.mobile == mobile).all())
    if email: matches.update(x.id for x in db.query(CustomerRecord).filter(CustomerRecord.email == email).all())
    if gstin: matches.update(x.customer_id for x in db.query(CustomerBusinessRecord).filter(CustomerBusinessRecord.gstin == gstin).all())
    return sorted(matches)

def record_customer_event(db: Session, customer_id: int, event_type: str, *, details: dict[str, Any] | None = None, source="api", actor_type="system", actor_id=None):
    event = CustomerEventRecord(customer_id=customer_id, event_type=event_type, source=source, actor_type=actor_type, actor_id=str(actor_id) if actor_id is not None else None, details=json.dumps(details or {}, default=str))
    db.add(event)
    return event

def customer_360(db: Session, customer_id: int) -> dict[str, Any] | None:
    customer = db.get(CustomerRecord, customer_id)
    if not customer: return None
    def rows(model): return db.query(model).filter(model.customer_id == customer_id).all()
    def one(model): return db.query(model).filter(model.customer_id == customer_id).first()
    def dump(obj): return None if obj is None else {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    events = db.query(CustomerEventRecord).filter(CustomerEventRecord.customer_id == customer_id).order_by(CustomerEventRecord.id.desc()).limit(100).all()
    return {"customer": dump(customer), "businesses": [dump(x) for x in rows(CustomerBusinessRecord)], "contacts": [dump(x) for x in rows(CustomerContactRecord)], "addresses": [dump(x) for x in rows(CustomerAddressRecord)], "kyc": dump(one(CustomerKYCRecord)), "bank_accounts": [dump(x) for x in rows(CustomerBankAccountRecord)], "consents": [dump(x) for x in rows(CustomerConsentRecord)], "preferences": dump(one(CustomerPreferenceRecord)), "risk_profile": dump(one(CustomerRiskProfileRecord)), "events": [dump(x) for x in events]}
