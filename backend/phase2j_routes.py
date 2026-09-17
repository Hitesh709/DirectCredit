import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .phase2i_collections import dpd, collection_bucket, overdue_amount
from .phase2j_collections_intelligence import PHASE2J_VERSION, build_priority, latest_ptp, has_failed_debit, recovery_action, intelligence_contract

router = APIRouter(prefix="/api/v1/collections/intelligence", tags=["phase-2j-collections-intelligence"])

class RecoveryTask(BaseModel):
    action: str = Field(min_length=3, max_length=60)
    scheduled_for: str | None = Field(default=None, max_length=30)
    reference: str = Field(min_length=3, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)

def _loan(loan_id, db):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "loan_not_found")
    customer = db.get(CustomerRecord, loan.customer_id)
    if not customer: raise HTTPException(404, "customer_not_found")
    return loan, customer

def _rows(loan_id, db):
    return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()

def _actions(loan_id, db):
    return db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id == loan_id).order_by(CollectionActionRecord.id).all()

def _mandate_active(loan):
    try:
        return str(json.loads(loan.disbursement_details or "{}").get("mandate", {}).get("status", "")).upper() == "ACTIVE"
    except Exception:
        return False

def _profile(loan, db):
    rows = _rows(loan.id, db); actions = _actions(loan.id, db)
    overdue, max_dpd = overdue_amount(rows)
    bucket = collection_bucket(max_dpd)
    ptp = latest_ptp(actions)
    p = build_priority(bucket, overdue, max_dpd, bool(ptp), has_failed_debit(actions))
    return rows, actions, overdue, max_dpd, bucket, ptp, p

@router.get("/contract")
def contract(): return intelligence_contract()

@router.get("/queue")
def queue(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    out=[]
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active", "overdue"])).all():
        _, actions, overdue, max_dpd, bucket, ptp, p = _profile(loan, db)
        if overdue <= 0: continue
        out.append({"loan_id": loan.id, "customer_id": loan.customer_id, "bucket": bucket, "dpd": max_dpd, "overdue_amount": overdue, "priority_score": p.score, "urgency": p.urgency, "reason_codes": list(p.reason_codes), "recommended_action": recovery_action(p, _mandate_active(loan)), "ptp_active": bool(ptp), "mandate_active": _mandate_active(loan)})
    return sorted(out, key=lambda x: (-x["priority_score"], -x["overdue_amount"], x["loan_id"]))

@router.get("/loan/{loan_id}")
def loan_intelligence(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    _, actions, overdue, max_dpd, bucket, ptp, p = _profile(loan, db)
    return {"loan_id": loan.id, "customer_id": customer.id, "bucket": bucket, "dpd": max_dpd, "overdue_amount": overdue, "priority_score": p.score, "urgency": p.urgency, "reason_codes": list(p.reason_codes), "recommended_action": recovery_action(p, _mandate_active(loan)), "ptp": ({"reference": ptp.reference, "amount": ptp.amount, "details": ptp.notes} if ptp else None), "mandate_active": _mandate_active(loan), "debit_failures": sum(x.action_type == "auto_debit_request" and x.status == "failed" for x in actions), "engine_version": PHASE2J_VERSION}

@router.post("/loan/{loan_id}/task")
def create_task(loan_id: int, body: RecoveryTask, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    _, _, overdue, _, _, _, p = _profile(loan, db)
    if overdue <= 0: raise HTTPException(409, "no_overdue_amount")
    if db.query(CollectionActionRecord).filter(CollectionActionRecord.reference == body.reference).first(): raise HTTPException(409, "collection_reference_already_processed")
    allowed={"CUSTOMER_CONTACT","PTP_FOLLOW_UP","AUTO_DEBIT_REVIEW","MANUAL_ESCALATION","REMINDER","FIELD_VISIT"}
    action=body.action.strip().upper()
    if action not in allowed: raise HTTPException(422,"unsupported_recovery_action")
    scheduled = body.scheduled_for or datetime.utcnow().isoformat()
    notes={"scheduled_for": scheduled, "priority_score": p.score, "urgency": p.urgency, "reason_codes": list(p.reason_codes), "notes": body.notes}
    row=CollectionActionRecord(loan_id=loan.id, customer_id=customer.id, action_type=action.lower(), amount=0, reference=body.reference, status="scheduled", notes=json.dumps(notes, ensure_ascii=False))
    db.add(row); db.commit(); db.refresh(row)
    return {"task_id":row.id,"loan_id":loan.id,"action":action,"status":"scheduled","scheduled_for":scheduled,"priority_score":p.score}

@router.get("/loan/{loan_id}/timeline")
def timeline(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, _ = _loan(loan_id, db)
    rows=[]
    for x in _actions(loan.id, db):
        rows.append({"id":x.id,"action":x.action_type,"amount":x.amount or 0,"reference":x.reference,"status":x.status,"created_at":str(x.created_at) if x.created_at else None,"notes":x.notes})
    return rows
