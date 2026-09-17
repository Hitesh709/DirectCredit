"""Phase 1 Customer 360 API."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_customer
from .db_models import CustomerRecord, CustomerBusinessRecord, CustomerContactRecord, CustomerAddressRecord, CustomerKYCRecord, CustomerBankAccountRecord, CustomerConsentRecord, CustomerPreferenceRecord, CustomerRiskProfileRecord, CustomerEventRecord
from .phase1_customer import customer_360, potential_duplicates, fingerprint, record_customer_event

router = APIRouter(prefix="/api/v1/customers", tags=["customer-360"])

def owner(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match customer")

def require_customer(db: Session, customer_id: int):
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "Customer not found")
    return c

class BusinessIn(BaseModel):
    legal_name: str = Field(min_length=1, max_length=200)
    trade_name: Optional[str] = None
    business_type: Optional[str] = None
    constitution: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    business_vintage_years: Optional[float] = Field(default=None, ge=0)
    annual_turnover: Optional[float] = Field(default=None, ge=0)
    monthly_turnover: Optional[float] = Field(default=None, ge=0)
    employee_count: Optional[int] = Field(default=None, ge=0)
    ownership_type: Optional[str] = None

class ContactIn(BaseModel):
    contact_type: str = Field(min_length=1, max_length=40)
    contact_value: str = Field(min_length=1, max_length=255)
    is_primary: bool = False

class AddressIn(BaseModel):
    address_type: str = Field(min_length=1, max_length=40)
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BankIn(BaseModel):
    bank_name: str = Field(min_length=1, max_length=160)
    account_holder_name: Optional[str] = None
    account_number_masked: str = Field(min_length=4, max_length=40)
    account_number: Optional[str] = Field(default=None, min_length=4, max_length=40)
    ifsc: Optional[str] = None
    account_type: Optional[str] = None
    is_primary: bool = False

class ConsentIn(BaseModel):
    consent_type: str = Field(min_length=1, max_length=80)
    purpose: Optional[str] = None
    version: str = Field(min_length=1, max_length=40)
    accepted: bool
    channel: Optional[str] = None

class PreferencesIn(BaseModel):
    sms: bool = True
    email: bool = True
    whatsapp: bool = True
    phone: bool = True
    push: bool = True
    transactional_only: bool = True

class KYCIn(BaseModel):
    status: Optional[str] = None
    pan_status: Optional[str] = None
    identity_status: Optional[str] = None
    address_status: Optional[str] = None
    business_status: Optional[str] = None
    aadhaar_reference: Optional[str] = Field(default=None, max_length=120)
    verification_source: Optional[str] = Field(default=None, max_length=80)
    verification_reference: Optional[str] = Field(default=None, max_length=160)
    review_reason: Optional[str] = None

@router.get("/{customer_id}/360")
def get_customer_360(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    data = customer_360(db, customer_id)
    if not data: raise HTTPException(404, "Customer not found")
    return data

@router.get("/{customer_id}/duplicates")
def find_duplicates(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); c = require_customer(db, customer_id)
    return {"customer_id": customer_id, "potential_duplicate_customer_ids": [x for x in potential_duplicates(db, pan=c.pan, mobile=c.mobile, email=c.email) if x != customer_id]}

@router.post("/{customer_id}/business")
def add_business(customer_id: int, payload: BusinessIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = CustomerBusinessRecord(customer_id=customer_id, **payload.model_dump()); db.add(row)
    record_customer_event(db, customer_id, "BUSINESS_ADDED", details={"business_type": payload.business_type})
    db.commit(); db.refresh(row); return {"id": row.id, "customer_id": customer_id, "status": "created"}

@router.get("/{customer_id}/businesses")
def list_businesses(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerBusinessRecord).filter(CustomerBusinessRecord.customer_id == customer_id).all()

@router.post("/{customer_id}/contacts")
def add_contact(customer_id: int, payload: ContactIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    if payload.is_primary:
        db.query(CustomerContactRecord).filter(CustomerContactRecord.customer_id == customer_id, CustomerContactRecord.contact_type == payload.contact_type).update({"is_primary": False})
    row = CustomerContactRecord(customer_id=customer_id, **payload.model_dump()); db.add(row)
    record_customer_event(db, customer_id, "CONTACT_ADDED", details={"contact_type": payload.contact_type})
    db.commit(); db.refresh(row); return {"id": row.id, "status": "created"}

@router.get("/{customer_id}/contacts")
def list_contacts(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerContactRecord).filter(CustomerContactRecord.customer_id == customer_id).all()

@router.post("/{customer_id}/addresses")
def add_address(customer_id: int, payload: AddressIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = CustomerAddressRecord(customer_id=customer_id, **payload.model_dump()); db.add(row)
    record_customer_event(db, customer_id, "ADDRESS_ADDED", details={"address_type": payload.address_type})
    db.commit(); db.refresh(row); return {"id": row.id, "status": "created"}

@router.get("/{customer_id}/addresses")
def list_addresses(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerAddressRecord).filter(CustomerAddressRecord.customer_id == customer_id).all()

@router.get("/{customer_id}/kyc")
def get_kyc(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    return row or {"customer_id": customer_id, "status": "not_started"}

@router.put("/{customer_id}/kyc")
def upsert_kyc(customer_id: int, payload: KYCIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    if not row: row = CustomerKYCRecord(customer_id=customer_id); db.add(row)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    record_customer_event(db, customer_id, "KYC_PROFILE_UPDATED", details={"fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    db.commit(); db.refresh(row); return row

@router.post("/{customer_id}/bank-accounts")
def add_bank_account(customer_id: int, payload: BankIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    fp = fingerprint(payload.account_number) if payload.account_number else None
    if fp:
        duplicate = db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.account_number_fingerprint == fp).first()
        if duplicate and duplicate.customer_id != customer_id: raise HTTPException(409, "Bank account is already associated with another customer")
    data = payload.model_dump(exclude={"account_number"}); data["account_number_fingerprint"] = fp
    if payload.is_primary: db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer_id).update({"is_primary": False})
    row = CustomerBankAccountRecord(customer_id=customer_id, **data); db.add(row)
    record_customer_event(db, customer_id, "BANK_ACCOUNT_ADDED", details={"bank_name": payload.bank_name})
    db.commit(); db.refresh(row); return {"id": row.id, "status": "created", "verification_status": row.verification_status}

@router.get("/{customer_id}/bank-accounts")
def list_bank_accounts(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer_id).all()

@router.post("/{customer_id}/consents")
def add_consent(customer_id: int, payload: ConsentIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = CustomerConsentRecord(customer_id=customer_id, **payload.model_dump()); db.add(row)
    record_customer_event(db, customer_id, "CONSENT_RECORDED", details={"consent_type": payload.consent_type, "accepted": payload.accepted})
    db.commit(); db.refresh(row); return {"id": row.id, "status": "recorded"}

@router.get("/{customer_id}/consents")
def list_consents(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerConsentRecord).filter(CustomerConsentRecord.customer_id == customer_id).order_by(CustomerConsentRecord.id.desc()).all()

@router.put("/{customer_id}/preferences")
def set_preferences(customer_id: int, payload: PreferencesIn, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = db.query(CustomerPreferenceRecord).filter(CustomerPreferenceRecord.customer_id == customer_id).first()
    if not row: row = CustomerPreferenceRecord(customer_id=customer_id); db.add(row)
    for k, v in payload.model_dump().items(): setattr(row, k, v)
    record_customer_event(db, customer_id, "PREFERENCES_UPDATED"); db.commit(); db.refresh(row); return row

@router.get("/{customer_id}/preferences")
def get_preferences(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = db.query(CustomerPreferenceRecord).filter(CustomerPreferenceRecord.customer_id == customer_id).first()
    return row or {"customer_id": customer_id, "transactional_only": True}

@router.get("/{customer_id}/risk-profile")
def risk_profile(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    row = db.query(CustomerRiskProfileRecord).filter(CustomerRiskProfileRecord.customer_id == customer_id).first()
    return row or {"customer_id": customer_id, "risk_status": "not_assessed", "fraud_status": "not_assessed", "credit_status": "not_assessed"}

@router.get("/{customer_id}/events")
def list_events(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims); require_customer(db, customer_id)
    return db.query(CustomerEventRecord).filter(CustomerEventRecord.customer_id == customer_id).order_by(CustomerEventRecord.id.desc()).limit(100).all()
