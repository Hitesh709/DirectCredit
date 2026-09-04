"""Authenticated repayment ledger endpoints using the canonical contract."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .auth import get_current_customer
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .repayment_contract import PAYMENT_METHODS, calculate_dpd, derive_status, repayment_payload

router = APIRouter(prefix="/api/services/repayments", tags=["repayments"])

class RepaymentPost(BaseModel):
    amount: float = Field(gt=0)
    payment_reference: str = Field(min_length=3, max_length=160)
    payment_method: str


def _loan_for_customer(loan_id: int, claims: dict, db: Session):
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    if int(loan.customer_id) != int(claims.get("user_id", -1)):
        raise HTTPException(403, "Customer session does not match this loan")
    return loan


@router.get("/customer/{customer_id}")
def customer_repayments(customer_id: int, claims: dict = Depends(get_current_customer), db: Session = Depends(get_db)):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "Customer session does not match this customer")
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "Customer not found")
    rows = db.query(RepaymentRecord).join(LoanRecord, LoanRecord.id == RepaymentRecord.loan_id).filter(LoanRecord.customer_id == customer_id).order_by(RepaymentRecord.due_date, RepaymentRecord.installment).all()
    return [repayment_payload(x) for x in rows]


@router.get("loan/{loan_id}")
def loan_repayments(loan_id: int, claims: dict = Depends(get_current_customer), db: Session = Depends(get_db)):
    _loan_for_customer(loan_id, claims, db)
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    return [repayment_payload(x) for x in rows]


@router.post("loan/{loan_id}/payments")
def post_repayment(loan_id: int, payload: RepaymentPost, claims: dict = Depends(get_current_customer), db: Session = Depends(get_db)):
    loan = _loan_for_customer(loan_id, claims, db)
    method = payload.payment_method.strip().lower()
    if method not in PAYMENT_METHODS:
        raise HTTPException(422, f"Unsupported payment method: {payload.payment_method}")
    remaining = float(payload.amount)
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    if not rows:
        raise HTTPException(409, "No repayment schedule exists for this loan")
    applied = []
    for row in rows:
        balance = max(0.0, float(row.due_amount or 0) - float(row.paid_amount or 0))
        if balance <= 0 or remaining <= 0:
            continue
        allocation = min(balance, remaining)
        row.paid_amount = round(float(row.paid_amount or 0) + allocation, 2)
        row.payment_reference = payload.payment_reference
        row.payment_method = method
        row.paid_at = datetime.utcnow()
        row.status = derive_status(row.due_date, row.due_amount, row.paid_amount)
        applied.append({"repayment_id": row.id, "allocated": allocation})
        remaining = round(remaining - allocation, 2)
    if not applied:
        raise HTTPException(409, "Payment amount cannot be allocated to outstanding installments")
    db.commit()
    db.refresh(loan)
    outstanding = sum(max(0.0, float(x.due_amount or 0) - float(x.paid_amount or 0)) for x in rows)
    loan.outstanding_amount = round(outstanding, 2)
    if outstanding <= 0:
        loan.status = "repaid"
    elif any(calculate_dpd(x.due_date, x.paid_amount, x.due_amount) > 0 for x in rows if float(x.paid_amount or 0) < float(x.due_amount or 0)):
        loan.status = "overdue"
    else:
        loan.status = "active"
    db.commit()
    return {"loan_id": loan_id, "payment_reference": payload.payment_reference, "amount_received": payload.amount, "amount_unallocated": max(0.0, remaining), "allocations": applied, "outstanding_amount": loan.outstanding_amount, "loan_status": loan.status}
