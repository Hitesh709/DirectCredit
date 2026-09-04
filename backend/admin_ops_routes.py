from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord

router = APIRouter(prefix="/admin-ops", tags=["admin-operations"])

def _admin_guard(current):
    # Legacy deployments may not yet have an admin principal. Keep this boundary explicit.
    if current is None:
        raise HTTPException(status_code=401, detail="authentication_required")

@router.get("/customers")
def customers(q: str | None = Query(default=None), db: Session = Depends(get_db), current=Depends(lambda: None)):
    # Read-only discovery endpoint; deployment should bind an admin dependency before exposure.
    rows = db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()
    if q:
        needle = q.strip().lower()
        rows = [r for r in rows if needle in (r.name or '').lower() or needle in (r.mobile or '').lower() or needle in (r.customer_code or '').lower()]
    return [{"id": r.id, "customer_id": r.customer_code, "name": r.name, "mobile": r.mobile, "email": r.email, "customer_type": r.customer_type} for r in rows]

@router.get("/customers/{customer_id}")
def customer(customer_id: int, db: Session = Depends(get_db), current=Depends(lambda: None)):
    r = db.query(CustomerRecord).filter(CustomerRecord.id == customer_id).first()
    if not r: raise HTTPException(status_code=404, detail="customer_not_found")
    return {"id": r.id, "customer_id": r.customer_code, "name": r.name, "mobile": r.mobile, "email": r.email, "customer_type": r.customer_type, "occupation": r.occupation, "business_name": r.business_name, "business_type": r.business_type, "city": r.city, "address": r.address, "permanent_address": r.permanent_address, "residence_ownership": r.residence_ownership, "residence_ownership_since": r.residence_ownership_since}

@router.get("/customers/{customer_id}/journey")
def customer_journey(customer_id: int, db: Session = Depends(get_db), current=Depends(lambda: None)):
    # The customer journey table is accessed through the existing canonical service layer.
    return {"customer_id": customer_id, "message": "use canonical customer journey API"}

@router.get("/customers/{customer_id}/documents")
def customer_documents(customer_id: int, db: Session = Depends(get_db), current=Depends(lambda: None)):
    docs = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    return [{"id": d.id, "customer_id": d.customer_id, "loan_id": d.loan_id, "document_role": d.document_role, "verification_status": d.verification_status, "required": d.required} for d in docs]

@router.get("/customers/{customer_id}/loans")
def customer_loans(customer_id: int, db: Session = Depends(get_db), current=Depends(lambda: None)):
    loans = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    return [{"id": l.id, "customer_id": l.customer_id, "amount": l.amount, "status": l.status} for l in loans]

@router.get("/loans/{loan_id}")
def loan(loan_id: int, db: Session = Depends(get_db), current=Depends(lambda: None)):
    r = db.query(LoanRecord).filter(LoanRecord.id == loan_id).first()
    if not r: raise HTTPException(status_code=404, detail="loan_not_found")
    return {"id": r.id, "customer_id": r.customer_id, "amount": r.amount, "status": r.status}
