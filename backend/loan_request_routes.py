from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord
from .auth import get_current_customer

router = APIRouter(prefix="/loan-request", tags=["loan-request"])
MIN_AMOUNT, MAX_AMOUNT = 5000.0, 15000.0
ALLOWED_TENURES = {3, 6, 9, 12}

class LoanRequest(BaseModel):
    product: str = Field(default="Micro Business Loan", min_length=1, max_length=120)
    requested_amount: float = Field(ge=MIN_AMOUNT, le=MAX_AMOUNT)
    tenure_months: int = Field(default=6, ge=1, le=60)

@router.post("/{customer_id}")
def create_request(customer_id: int, payload: LoanRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    if payload.tenure_months not in ALLOWED_TENURES:
        raise HTTPException(422, "Supported tenure is 3, 6, 9 or 12 months")
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "Customer not found")
    loan = LoanRecord(customer_id=customer_id, requested_amount=payload.requested_amount,
                      tenure_months=payload.tenure_months, product=payload.product,
                      status="draft", current_stage="PAN")
    db.add(loan); db.commit(); db.refresh(loan)
    return {"loan_id": loan.id, "customer_id": customer_id, "product": loan.product,
            "requested_amount": loan.requested_amount, "tenure_months": loan.tenure_months,
            "status": loan.status, "current_stage": loan.current_stage}

@router.get("/{customer_id}")
def list_requests(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id: raise HTTPException(403, "Customer session does not match this customer")
    rows = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    return [{"loan_id": r.id, "product": r.product, "requested_amount": r.requested_amount,
             "eligible_amount": r.eligible_amount, "tenure_months": r.tenure_months,
             "status": r.status, "current_stage": r.current_stage} for r in rows]
