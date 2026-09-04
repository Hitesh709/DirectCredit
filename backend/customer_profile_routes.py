"""Authenticated customer profile APIs for canonical profile data."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, DocumentRecord
from .auth import get_current_customer
from .schemas import PersonalProfileUpdate, EmploymentBusinessUpdate, AddressResidenceUpdate, ResidenceProofCreate
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
        "kyc_status": c.kyc_status, "ownership_proof_name": c.ownership_proof_name,
        "ownership_proof_status": c.ownership_proof_status,
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
    if "name" in changes and not str(changes["name"] or "").strip(): raise HTTPException(422, "Name cannot be empty")
    for key, value in changes.items(): setattr(c, key, value.strip() if isinstance(value, str) else value)
    db.commit(); db.refresh(c); _audit(request, db, claims, c, "CUSTOMER_PERSONAL_PROFILE_UPDATED", {"fields": sorted(changes.keys())})
    return {"updated": True, "customer_id": c.id, "section": "personal", "profile": _customer(c)}

@router.get("/{customer_id}/employment-business")
def get_employment_business(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    return {"customer_id": c.id, "section": "employment_business", "profile": _customer(c)}

@router.patch("/{customer_id}/employment-business")
def update_employment_business(customer_id: int, payload: EmploymentBusinessUpdate, request: Request, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items(): setattr(c, key, value.strip() if isinstance(value, str) else value)
    db.commit(); db.refresh(c); _audit(request, db, claims, c, "CUSTOMER_EMPLOYMENT_BUSINESS_UPDATED", {"fields": sorted(changes.keys())})
    return {"updated": True, "customer_id": c.id, "section": "employment_business", "profile": _customer(c)}

@router.get("/{customer_id}/address-residence")
def get_address_residence(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    return {"customer_id": c.id, "section": "address_residence", "profile": _customer(c)}

@router.patch("/{customer_id}/address-residence")
def update_address_residence(customer_id: int, payload: AddressResidenceUpdate, request: Request, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    changes = payload.model_dump(exclude_unset=True)
    if not changes: raise HTTPException(422, "At least one address or residence field is required")
    for key, value in changes.items(): setattr(c, key, value.strip() if isinstance(value, str) else value)
    if c.residence_ownership and c.residence_ownership.strip().lower() not in {"owned", "rented", "leased", "family", "company", "other"}:
        raise HTTPException(422, "Unsupported residence ownership value")
    db.commit(); db.refresh(c); _audit(request, db, claims, c, "CUSTOMER_ADDRESS_RESIDENCE_UPDATED", {"fields": sorted(changes.keys())})
    return {"updated": True, "customer_id": c.id, "section": "address_residence", "profile": _customer(c)}

@router.post("/{customer_id}/residence-proof")
def upload_residence_proof(customer_id: int, payload: ResidenceProofCreate, request: Request, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    if not c.residence_ownership or not c.address or not c.current_city:
        raise HTTPException(422, "Complete address and residence ownership before uploading proof")
    existing = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id, DocumentRecord.document_type == payload.document_type, DocumentRecord.verification_status.in_(["pending", "verified"])).first()
    if existing: raise HTTPException(409, "Residence proof already submitted")
    d = DocumentRecord(customer_id=customer_id, document_type=payload.document_type, document_role="residence_proof", file_name=payload.file_name, mime_type=payload.mime_type, file_size=payload.file_size, checksum=payload.checksum, source="customer_portal", required=True, verification_status="pending", storage_provider=payload.storage_provider, storage_key=payload.storage_key)
    db.add(d); c.ownership_proof_name = payload.file_name; c.ownership_proof_status = "pending"; db.commit(); db.refresh(d); db.refresh(c)
    _audit(request, db, claims, c, "CUSTOMER_RESIDENCE_PROOF_SUBMITTED", {"document_id": d.id, "document_type": d.document_type})
    return {"submitted": True, "customer_id": c.id, "document_id": d.id, "verification_status": d.verification_status, "ownership_proof_status": c.ownership_proof_status}

@router.get("/{customer_id}/profile-completion")
def profile_completion(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    checks = {
        "personal_identity": bool(c.name and c.mobile and c.date_of_birth and c.gender and c.marital_status),
        "current_address": bool(c.address and c.current_city),
        "permanent_address": bool(c.permanent_address),
        "residence_ownership": bool(c.residence_ownership and c.residence_since),
        "employment_business": bool(c.occupation and c.customer_type and (c.business_name or c.occupation != "Business") and c.monthly_income is not None),
        "bank_profile": bool(c.primary_bank and c.average_bank_balance is not None),
        "residence_proof": bool(c.ownership_proof_name and c.ownership_proof_status in {"pending", "verified"}),
    }
    total = len(checks); completed = sum(checks.values()); percentage = round(completed / total * 100, 2)
    return {"customer_id": c.id, "completion_percentage": percentage, "completed_sections": completed, "total_sections": total, "complete": completed == total, "sections": checks}

@router.get("/{customer_id}/admin-sync")
def admin_sync_view(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    c = _get(customer_id, claims, db)
    completion = profile_completion(customer_id, db, claims)
    documents = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    return {"customer_id": c.id, "source_of_truth": "customers_and_documents", "profile": _customer(c), "profile_completion": completion, "documents": [{"id": d.id, "document_type": d.document_type, "file_name": d.file_name, "verification_status": d.verification_status, "created_at": d.created_at} for d in documents]}
