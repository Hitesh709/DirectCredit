from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_customer
from .db_models import CustomerRecord, LoanRecord
from .eligibility_engine import assess, MIN_LOAN, MAX_LOAN

router = APIRouter(prefix="/eligibility", tags=["eligibility"])

class LoanRequest(BaseModel):
    amount: int = Field(ge=MIN_LOAN, le=MAX_LOAN)
    tenure_months: int = Field(ge=1, le=36)
    product: str = "MBL"

class AssessmentInput(BaseModel):
    monthly_income: float | None = None
    existing_emi: float | None = None
    bureau_score: float | None = None
    banking_score: float | None = None
    official_score: int | None = Field(default=None, ge=0, le=125)
    score_source: str = "scorecard_not_configured"

@router.post("/{customer_id}/request")
def create_or_update_request(customer_id: int, body: LoanRequest, db: Session = Depends(get_db), current=Depends(get_current_customer)):
    if current.id != customer_id:
        raise HTTPException(status_code=403, detail="customer_scope_forbidden")
    customer = db.query(CustomerRecord).filter(CustomerRecord.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="customer_not_found")
    loan = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan:
        loan = LoanRecord(customer_id=customer_id, amount=body.amount, status="draft")
        db.add(loan)
    else:
        loan.amount = body.amount
    db.commit(); db.refresh(loan)
    return {"loan_id": loan.id, "customer_id": customer_id, "requested_amount": body.amount, "tenure_months": body.tenure_months, "product": body.product, "status": loan.status}

@router.post("/{customer_id}/assess")
def assess_customer(customer_id: int, body: AssessmentInput, db: Session = Depends(get_db), current=Depends(get_current_customer)):
    if current.id != customer_id:
        raise HTTPException(status_code=403, detail="customer_scope_forbidden")
    loan = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan:
        raise HTTPException(status_code=404, detail="loan_request_not_found")
    result = assess(requested_amount=int(loan.amount or 0), tenure_months=12, monthly_income=body.monthly_income, existing_emi=body.existing_emi, bureau_score=body.bureau_score, banking_score=body.banking_score, score=body.official_score, score_source=body.score_source)
    return result.payload()

@router.get("/{customer_id}")
def get_eligibility(customer_id: int, db: Session = Depends(get_db), current=Depends(get_current_customer)):
    if current.id != customer_id:
        raise HTTPException(status_code=403, detail="customer_scope_forbidden")
    loan = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan:
        return {"loan": None, "decision": "NOT_ASSESSED", "score_source": "scorecard_not_configured"}
    return {"loan_id": loan.id, "customer_id": customer_id, "requested_amount": loan.amount, "status": loan.status, "decision": "NOT_ASSESSED", "score_source": "scorecard_not_configured"}
