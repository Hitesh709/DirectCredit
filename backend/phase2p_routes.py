from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import LoanRecord, RepaymentRecord, CollectionActionRecord, SettlementRecord
from .admin_auth import get_current_admin
from .phase2p_reconciliation import PHASE2P_VERSION, reconcile_loan, reconciliation_contract

router = APIRouter(prefix="/api/v1/reconciliation", tags=["phase-2p-reconciliation"])

class ReconcileRequest(BaseModel):
    expected_amount: float = Field(ge=0)
    observed_amount: float = Field(ge=0)
    tolerance: float = Field(default=1.0, ge=0)

@router.get("/contract")
def contract():
    return reconciliation_contract()

def _loan(loan_id, db):
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "loan_not_found")
    return loan

def _build(loan_id, db, expected, observed, tolerance):
    _loan(loan_id, db)
    repayments = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).all()
    refs = [r.payment_reference for r in repayments if r.payment_reference]
    counts = {}
    for ref in refs: counts[str(ref)] = counts.get(str(ref), 0) + 1
    duplicates = sum(1 for n in counts.values() if n > 1)
    unallocated = sum(max(0.0, float(r.paid_amount or 0) - float(r.due_amount or 0)) for r in repayments)
    actions = db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id == loan_id).all()
    collection_refs = {str(a.reference) for a in actions if a.reference}
    payment_refs = {str(r.payment_reference) for r in repayments if r.payment_reference}
    mismatch = bool(collection_refs and payment_refs and not collection_refs.intersection(payment_refs))
    settlement = db.query(SettlementRecord).filter(SettlementRecord.loan_id == loan_id).order_by(SettlementRecord.id.desc()).first()
    settlement_missing = bool(settlement and settlement.status == "completed" and not settlement.reference)
    return reconcile_loan(loan_id=loan_id, expected_amount=expected, observed_amount=observed,
                          repayment_references=refs, duplicate_references=duplicates,
                          unallocated_amount=unallocated, collection_reference_mismatch=mismatch,
                          settlement_evidence_missing=settlement_missing,
                          ledger_balance=float(loan.outstanding_amount or 0), loan_balance=float(loan.outstanding_amount or 0),
                          tolerance=tolerance)

@router.post("/loan/{loan_id}/check")
def check(loan_id: int, body: ReconcileRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    result = _build(loan_id, db, body.expected_amount, body.observed_amount, body.tolerance)
    return {"loan_id": loan_id, "assessment": result.__dict__, "engine_version": PHASE2P_VERSION}

@router.get("/loan/{loan_id}")
def loan_reconciliation(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan = _loan(loan_id, db)
    expected = sum(float(r.due_amount or 0) for r in db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).all())
    observed = sum(float(r.paid_amount or 0) for r in db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).all())
    result = _build(loan_id, db, expected, observed, 1.0)
    return {"loan_id": loan.id, "customer_id": loan.customer_id, "assessment": result.__dict__, "engine_version": PHASE2P_VERSION}

@router.get("/queue")
def queue(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    out = []
    for loan in db.query(LoanRecord).all():
        expected = sum(float(r.due_amount or 0) for r in db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan.id).all())
        observed = sum(float(r.paid_amount or 0) for r in db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan.id).all())
        result = _build(loan.id, db, expected, observed, 1.0)
        if result.status == "EXCEPTION":
            out.append({"loan_id": loan.id, "customer_id": loan.customer_id, **result.__dict__})
    return sorted(out, key=lambda x: (-len(x["exceptions"]), -abs(x["variance"]), x["loan_id"]))
