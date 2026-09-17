from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import LoanRecord, RepaymentRecord, SettlementRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .phase2o_resolution import PHASE2O_VERSION, assess_resolution, resolution_contract

router = APIRouter(prefix="/api/v1/resolution", tags=["phase-2o-resolution"])


def _assessment(loan_id: int, db: Session):
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "loan_not_found")
    repayments = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).all()
    # Unallocated means money recorded against a repayment reference but still
    # exceeding the installment due amount. This is a control signal, not a
    # payment mutation.
    unallocated = sum(max(0.0, float(r.paid_amount or 0) - float(r.due_amount or 0)) for r in repayments)
    settlement = db.query(SettlementRecord).filter(SettlementRecord.loan_id == loan_id).order_by(SettlementRecord.id.desc()).first()
    actions = db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id == loan_id).all()
    pending = sum(1 for a in actions if str(a.status or "").lower() in {"pending", "open", "assigned"})
    result = assess_resolution(
        loan_id=loan.id,
        outstanding_amount=float(loan.outstanding_amount or 0),
        repayment_unallocated=unallocated,
        settlement_status=settlement.status if settlement else None,
        settlement_approved_amount=float(settlement.approved_amount or 0) if settlement else 0,
        settlement_paid_amount=float(settlement.approved_amount or 0) if settlement and settlement.status == "completed" else 0,
        pending_operations=pending,
        loan_status=loan.status or "",
    )
    return loan, result


@router.get("/contract")
def contract():
    return resolution_contract()


@router.get("/loan/{loan_id}")
def loan_resolution(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, result = _assessment(loan_id, db)
    return {
        "loan_id": loan.id,
        "customer_id": loan.customer_id,
        "assessment": result.__dict__,
        "engine_version": PHASE2O_VERSION,
    }


@router.get("/queue")
def resolution_queue(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    out = []
    for loan in db.query(LoanRecord).all():
        _, result = _assessment(loan.id, db)
        if result.state != "CLOSED":
            out.append({"loan_id": loan.id, "customer_id": loan.customer_id, **result.__dict__})
    order = {"SETTLEMENT_APPROVED": 0, "SETTLEMENT_PENDING": 1, "OPEN": 2, "READY_FOR_CLOSURE": 3}
    return sorted(out, key=lambda x: (order.get(x["state"], 9), -x["outstanding_amount"], x["loan_id"]))


@router.get("/loan/{loan_id}/noc-readiness")
def noc_readiness(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, result = _assessment(loan_id, db)
    return {
        "loan_id": loan.id,
        "customer_id": loan.customer_id,
        "ready": result.closure_ready,
        "state": result.state,
        "blockers": list(result.blockers),
        "noc_action": "ISSUE_NOC" if result.closure_ready else "DO_NOT_ISSUE",
        "engine_version": PHASE2O_VERSION,
    }
