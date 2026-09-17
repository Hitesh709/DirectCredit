"""Phase 2D policy contract and customer-scoped decision preview."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .auth import get_current_customer
from .database import get_db
from .db_models import CustomerRecord, LoanRecord
from .phase2b_data_adapters import build_phase2b_inputs
from .phase2_credit_engine import fraud_screen
from .mbl_scorecard import calculate
from .phase2d_policy_engine import evaluate_policy, policy_contract

router = APIRouter(prefix="/api/v1/policy", tags=["policy-engine"])


def _owner(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")


@router.get("/contract")
def contract():
    return policy_contract()


@router.get("/{customer_id}/preview")
def preview(customer_id: int, loan_id: int | None = None, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    loan = db.get(LoanRecord, loan_id) if loan_id else db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan or loan.customer_id != customer_id:
        raise HTTPException(404, "loan_not_found")
    payload = build_phase2b_inputs(db, customer_id)
    inputs = payload["inputs"]
    quality = payload["data_quality"]
    fraud = fraud_screen(inputs)
    score = calculate(inputs)
    decision = evaluate_policy(
        score=score.score,
        score_decision=score.decision,
        score_approval_percent=score.approval_percent,
        requested_amount=float(loan.requested_amount or 0),
        unavailable_fields=quality.get("unavailable_fields", []),
        fraud_status=fraud["status"],
        fraud_flags=fraud["flags"],
        hard_rejects=score.hard_rejects,
        inputs=inputs,
    )
    return {
        "customer_id": customer_id,
        "loan_id": loan.id,
        "credit": score.payload(),
        "policy": decision.payload(),
        "fraud": fraud,
        "data_quality": quality,
    }
