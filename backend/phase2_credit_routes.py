"""Phase 2 Credit Decision + Fraud + Phase 2B data intelligence APIs."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_customer
from .db_models import CustomerRecord, LoanRecord, BankTransactionRecord
from .phase2_credit_engine import assess, fraud_screen, build_assessment_input
from .phase2b_data_adapters import build_phase2b_inputs, bank_statement_intelligence

router = APIRouter(prefix="/api/v1/credit", tags=["credit-decision"])


def owner(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")


class AssessRequest(BaseModel):
    loan_id: int | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.post("/{customer_id}/assess")
def run_assessment(customer_id: int, body: AssessRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    try:
        return assess(db, customer_id, body.loan_id, body.overrides)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/{customer_id}/assessment-inputs")
def get_assessment_inputs(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    return build_assessment_input(db, customer_id)


@router.get("/{customer_id}/data-readiness")
def get_data_readiness(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    payload = build_phase2b_inputs(db, customer_id)
    return {"customer_id": customer_id, "data_quality": payload["data_quality"], "geo": payload["geo"]}


@router.get("/{customer_id}/bank-intelligence")
def get_bank_intelligence(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    transactions = db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id == customer_id).order_by(BankTransactionRecord.id.asc()).all()
    return {"customer_id": customer_id, "bank_statement": bank_statement_intelligence(transactions)}


@router.post("/{customer_id}/fraud-screen")
def run_fraud_screen(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    inputs = build_assessment_input(db, customer_id)
    return {"customer_id": customer_id, "fraud": fraud_screen(inputs), "inputs": inputs}


@router.get("/{customer_id}/decision")
def get_decision(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    owner(customer_id, claims)
    loan = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan:
        return {"customer_id": customer_id, "decision": "NOT_ASSESSED"}
    import json
    return {
        "customer_id": customer_id,
        "loan_id": loan.id,
        "decision": loan.scorecard_decision or "NOT_ASSESSED",
        "score": loan.scorecard_score,
        "max_score": loan.scorecard_max,
        "approval_percent": loan.scorecard_approval_percent,
        "eligible_amount": loan.eligible_amount,
        "reasons": json.loads(loan.scorecard_reasons or "[]"),
        "hard_rejects": json.loads(loan.scorecard_hard_rejects or "[]"),
        "factor_scores": json.loads(loan.scorecard_factor_scores or "{}"),
        "scorecard_version": loan.scorecard_version,
    }
