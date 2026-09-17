"""Phase 2H authenticated loan-servicing APIs."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .auth import get_current_customer
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .phase2h_servicing import PHASE2H_VERSION, installment_metrics, servicing_contract

router = APIRouter(prefix="/api/v1/servicing", tags=["loan-servicing"])

class PaymentRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_reference: str = Field(min_length=3, max_length=160)
    payment_method: str = Field(min_length=2, max_length=40)


def _owner(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")

def _loan(customer_id: int, loan_id: int, db: Session):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "loan_not_found")
    if int(loan.customer_id) != int(customer_id): raise HTTPException(403, "loan_access_forbidden")
    return loan

@router.get("/contract")
def contract():
    return servicing_contract()

@router.get("/{customer_id}/{loan_id}/summary")
def summary(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims); loan = _loan(customer_id, loan_id, db)
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    metrics = [installment_metrics(r) for r in rows]
    overdue = round(sum(x["unpaid_amount"] for x in metrics if x["dpd"] > 0), 2)
    next_due = next((x for x in metrics if x["unpaid_amount"] > 0), None)
    max_dpd = max((x["dpd"] for x in metrics), default=0)
    return {"phase": PHASE2H_VERSION, "loan_id": loan_id, "loan_status": loan.status,
            "outstanding_amount": float(loan.outstanding_amount or 0), "overdue_amount": overdue,
            "max_dpd": max_dpd, "next_due": next_due, "installments": metrics}

@router.get("/{customer_id}/{loan_id}/schedule")
def schedule(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims); _loan(customer_id, loan_id, db)
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    return [installment_metrics(r) for r in rows]

@router.post("/{customer_id}/{loan_id}/payment")
def payment(customer_id: int, loan_id: int, body: PaymentRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims); loan = _loan(customer_id, loan_id, db)
    duplicate = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id, RepaymentRecord.payment_reference == body.payment_reference).first()
    if duplicate: raise HTTPException(409, "payment_reference_already_processed")
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    if not rows: raise HTTPException(409, "no_repayment_schedule")
    remaining = float(body.amount); allocations = []
    for row in rows:
        balance = max(0.0, float(row.due_amount or 0) - float(row.paid_amount or 0))
        if balance <= 0: continue
        take = min(balance, remaining)
        row.paid_amount = round(float(row.paid_amount or 0) + take, 2)
        row.payment_reference = body.payment_reference
        row.payment_method = body.payment_method.strip().lower()
        row.status = "paid" if row.paid_amount >= row.due_amount else "partially_paid"
        allocations.append({"repayment_id": row.id, "allocated": take})
        remaining = round(remaining - take, 2)
        if remaining <= 0: break
    if not allocations: raise HTTPException(409, "no_outstanding_balance")
    outstanding = round(sum(max(0.0, float(r.due_amount or 0) - float(r.paid_amount or 0)) for r in rows), 2)
    loan.outstanding_amount = outstanding
    loan.status = "repaid" if outstanding <= 0 else "overdue" if any(installment_metrics(r)["dpd"] > 0 and r.paid_amount < r.due_amount for r in rows) else "active"
    db.commit()
    return {"phase": PHASE2H_VERSION, "loan_id": loan_id, "received": body.amount, "allocated": round(body.amount - remaining, 2), "unallocated": remaining, "outstanding_amount": outstanding, "loan_status": loan.status, "allocations": allocations}
