"""Authenticated customer profile and employment/business update APIs."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord
from .auth import get_current_customer
from .schemas import PersonalProfileUpdate, EmploymentBusinessUpdate
from .audit_service import record_event, audit_request_context

router = APIRouter(prefix="/customer-profile", tags=["customer-profile"])


def _customer(c: CustomerRecord) -> dict:
    return {
        "id": c.id, "customer_code": c.customer_code or f"CUST{c.id:08d}",
        "name": c.name, "mobile": c.mobile, "email": c.email,
        "gender": c.gender, "date_of_birth": c.date_of_birth, "marital_status": c.marital_status,
        "address": c.address, "permanent_address": c.permanent_address, "current_city": c.current_city,
        "residence_ownership": c.residence_ownership, "residence_since": c.residence_since,
        "customer_type": c.customer_type, "occupation": c.occupation,
        "business_name": c.business_name, "business_type": c.business_type,
        "monthly_income": c.monthly_income, "work_experience_years": c.work_experience_years,
        "years_in_business": c.years_in_business, "average_bank_balance": c.average_bank_balance,
        "primary_bank": c.primary_bank, "existing_emi": c.existing_emi, "dependents": c.dependents,
        "kyc_status": c.kyc_status,
    }


def _get(customer_id: int, claims: dict, db: Session) -> CustomerRecord:
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "Customer not found")
    return c


def _audit(request: Request, db: Session, claims: dict, c: CustomerRecord, action: str, details: dict):
    ctx = audit_request_context(request, claims)
    record_event(db, action=action, entity_type="customer", entity_id=c.id, customer_id=c.id, details=details, **ctx)
    db.commit()


@router.get("/{customer_id}/personal")
def get_personal(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    return {"customer_id": c.id, "section": "personal", "profile": _customer(c)}


@router.patch("/{customer_id}/personal")
def update_personal(customer_id: int, payload: PersonalProfileUpdate, request: Request, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and not str(changes["name"] or "").strip():
        raise HTTPException(422, "Name cannot be empty")
    for key, value in changes.items():
        setattr(c, key, value.strip() if isinstance(value, str) else value)
    db.commit(); db.refresh(c)
    _audit(request, db, claims, c, "CUSTOMER_PERSONAL_PROFILE_UPDATED", {"fields": sorted(changes.keys())})
    return {"updated": True, "customer_id": c.id, "section": "personal", "profile": _customer(c)}


@router.get("/{customer_id}/employment-business")
def get_employment_business(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    return {"customer_id": c.id, "section": "employment_business", "profile": _customer(c)}


@router.patch("/{customer_id}/employment-business")
def update_employment_business(customer_id: int, payload: EmploymentBusinessUpdate, request: Request, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if isinstance(value, str): value = value.strip()
        setattr(c, key, value)
    db.commit(); db.refresh(c)
    _audit(request, db, claims, c, "CUSTOMER_EMPLOYMENT_BUSINESS_UPDATED", {"fields": sorted(changes.keys())})
    return {"updated": True, "customer_id": c.id, "section": "employment_business", "profile": _customer(c)}
