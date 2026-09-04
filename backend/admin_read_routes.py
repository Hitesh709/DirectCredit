from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin-data", tags=["admin-data"])

@router.get("/customers")
def customers(q: str | None = Query(default=None), db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    rows = db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()
    if q:
        n=q.strip().lower(); rows=[r for r in rows if n in (r.name or '').lower() or n in (r.mobile or '').lower() or n in (r.customer_code or '').lower()]
    return [{"id":r.id,"customer_id":r.customer_code,"name":r.name,"mobile":r.mobile,"email":r.email,"customer_type":r.customer_type} for r in rows]

@router.get("/customers/{customer_id}")
def customer(customer_id:int, db:Session=Depends(get_db), _admin: dict = Depends(get_current_admin)):
    r=db.get(CustomerRecord,customer_id)
    if not r: raise HTTPException(404,"customer_not_found")
    return {"id":r.id,"customer_id":r.customer_code,"name":r.name,"mobile":r.mobile,"email":r.email,"customer_type":r.customer_type,"occupation":r.occupation,"business_name":r.business_name,"business_type":r.business_type,"city":r.current_city,"address":r.address,"permanent_address":r.permanent_address,"residence_ownership":r.residence_ownership}

@router.get("/customers/{customer_id}/documents")
def documents(customer_id:int, db:Session=Depends(get_db), _admin: dict = Depends(get_current_admin)):
    return [{"id":d.id,"customer_id":d.customer_id,"loan_id":d.loan_id,"document_type":d.document_type,"document_role":d.document_role,"verification_status":d.verification_status,"required":d.required} for d in db.query(DocumentRecord).filter(DocumentRecord.customer_id==customer_id).all()]

@router.get("/customers/{customer_id}/loans")
def loans(customer_id:int, db:Session=Depends(get_db), _admin: dict = Depends(get_current_admin)):
    return [{"id":l.id,"customer_id":l.customer_id,"amount":l.requested_amount,"eligible_amount":l.eligible_amount,"status":l.status,"stage":l.current_stage} for l in db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).all()]
