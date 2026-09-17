import hashlib
import hmac
import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .phase2i_collections import PHASE2I_VERSION, collections_contract, decide_collection
from .repayment_contract import calculate_dpd, derive_status

router = APIRouter(prefix="/api/v1/collections", tags=["phase-2i-collections"])

class AutoDebitRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=80)
    reference: str = Field(min_length=3, max_length=160)
    amount: float = Field(gt=0)
    mandate_reference: str | None = Field(default=None, max_length=160)

class Callback(BaseModel):
    reference: str = Field(min_length=3, max_length=160)
    status: str = Field(min_length=3, max_length=30)
    provider_reference: str | None = Field(default=None, max_length=160)
    amount: float | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, max_length=500)
    signature: str | None = None

class PTPRequest(BaseModel):
    promised_amount: float = Field(gt=0)
    promised_date: str = Field(min_length=10, max_length=20)
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
        details = json.loads(loan.disbursement_details or "{}")
        return str(details.get("mandate", {}).get("status", "")).upper() == "ACTIVE"
    except Exception:
        return False


def _callback_valid(body, secret):
    if not secret: return False
    payload = body.model_dump(exclude={"signature"})
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return bool(body.signature) and hmac.compare_digest(body.signature, expected)


@router.get("/contract")
def contract():
    return collections_contract()

@router.get("/loan/{loan_id}/queue")
def queue(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    rows = _rows(loan_id, db)
    decision = decide_collection(rows, _actions(loan_id, db), _mandate_active(loan))
    return {"loan_id": loan_id, "customer_id": customer.id, "bucket": decision.bucket, "overdue_amount": decision.overdue_amount, "auto_debit_eligible": decision.auto_debit_eligible, "retry_allowed": decision.retry_allowed, "next_retry_number": decision.retry_number, "reason": decision.reason}

@router.get("/queue")
def collection_queue(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    out = []
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active", "overdue"])).order_by(LoanRecord.id).all():
        rows = _rows(loan.id, db)
        decision = decide_collection(rows, _actions(loan.id, db), _mandate_active(loan))
        if decision.overdue_amount > 0:
            out.append({"loan_id": loan.id, "customer_id": loan.customer_id, "bucket": decision.bucket, "overdue_amount": decision.overdue_amount, "auto_debit_eligible": decision.auto_debit_eligible, "retry_allowed": decision.retry_allowed, "next_retry_number": decision.retry_number, "reason": decision.reason})
    return sorted(out, key=lambda x: (x["bucket"], -x["overdue_amount"], x["loan_id"]))

@router.post("/loan/{loan_id}/auto-debit")
def auto_debit(loan_id: int, body: AutoDebitRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    if db.query(CollectionActionRecord).filter(CollectionActionRecord.reference == body.reference).first():
        raise HTTPException(409, "collection_reference_already_processed")
    decision = decide_collection(_rows(loan_id, db), _actions(loan_id, db), _mandate_active(loan))
    if not decision.auto_debit_eligible: raise HTTPException(409, decision.reason)
    if not decision.retry_allowed: raise HTTPException(409, "maximum_auto_debit_attempts_reached")
    amount = min(float(body.amount), decision.overdue_amount)
    row = CollectionActionRecord(loan_id=loan_id, customer_id=customer.id, action_type="auto_debit_request", amount=amount, reference=body.reference, status="pending_provider", notes=json.dumps({"provider": body.provider, "mandate_reference": body.mandate_reference, "attempt": decision.retry_number}))
    db.add(row); db.commit(); db.refresh(row)
    return {"action_id": row.id, "loan_id": loan_id, "amount": amount, "bucket": decision.bucket, "attempt": decision.retry_number, "status": "pending_provider", "provider": body.provider}

@router.post("/loan/{loan_id}/auto-debit/callback")
def auto_debit_callback(loan_id: int, body: Callback, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    if not _callback_valid(body, os.getenv("DC_COLLECTION_CALLBACK_SECRET", "")):
        raise HTTPException(401, "invalid_callback_signature")
    action = db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id == loan_id, CollectionActionRecord.reference == body.reference, CollectionActionRecord.action_type == "auto_debit_request").first()
    if not action: raise HTTPException(404, "debit_request_not_found")
    if action.status == "posted": return {"status": "already_processed", "action_id": action.id}
    status = body.status.strip().upper()
    if status in {"SUCCESS", "PAID", "CAPTURED"}:
        amount = min(float(body.amount or action.amount or 0), float(action.amount or 0))
        if amount <= 0: raise HTTPException(422, "invalid_callback_amount")
        rows = _rows(loan_id, db); remaining = amount; allocated = 0.0
        for row in rows:
            balance = max(0.0, float(row.due_amount or 0) - float(row.paid_amount or 0))
            take = min(balance, remaining)
            if take <= 0: continue
            row.paid_amount = round(float(row.paid_amount or 0) + take, 2); row.payment_reference = body.provider_reference or body.reference; row.payment_method = "auto_debit"; row.paid_at = datetime.utcnow(); row.status = derive_status(row.due_date, row.due_amount, row.paid_amount)
            allocated += take; remaining = round(remaining - take, 2)
            if remaining <= 0: break
        if allocated <= 0: raise HTTPException(409, "no_outstanding_repayment_balance")
        action.status = "posted"; action.amount = allocated; action.notes = (action.notes or "") + " | provider_success"
        loan.outstanding_amount = round(sum(max(0, float(r.due_amount or 0) - float(r.paid_amount or 0)) for r in rows), 2)
        loan.status = "repaid" if loan.outstanding_amount <= 0 else ("overdue" if any(calculate_dpd(r.due_date, r.paid_amount, r.due_amount) > 0 for r in rows if r.paid_amount < r.due_amount) else "active")
        db.commit()
        return {"status": "posted", "action_id": action.id, "received": allocated, "unallocated": remaining, "outstanding_amount": loan.outstanding_amount}
    if status in {"FAILED", "BOUNCED", "DECLINED", "CANCELLED"}:
        action.status = "failed"; action.notes = (action.notes or "") + " | " + (body.reason or status); db.commit()
        return {"status": "failed", "action_id": action.id, "retry_policy": "eligible_for_next_attempt_subject_to_max_retries"}
    raise HTTPException(422, "unsupported_provider_status")

@router.post("/loan/{loan_id}/promise-to-pay")
def promise_to_pay(loan_id: int, body: PTPRequest, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db)
    if db.query(CollectionActionRecord).filter(CollectionActionRecord.reference == body.reference).first(): raise HTTPException(409, "collection_reference_already_processed")
    decision = decide_collection(_rows(loan_id, db), _actions(loan_id, db), _mandate_active(loan))
    if decision.overdue_amount <= 0: raise HTTPException(409, "no_overdue_amount")
    if body.promised_amount > decision.overdue_amount: raise HTTPException(422, "promise_exceeds_overdue_amount")
    row = CollectionActionRecord(loan_id=loan_id, customer_id=customer.id, action_type="promise_to_pay", amount=body.promised_amount, reference=body.reference, status="recorded", notes=json.dumps({"promised_date": body.promised_date, "notes": body.notes}, ensure_ascii=False))
    db.add(row); db.commit(); db.refresh(row)
    return {"action_id": row.id, "loan_id": loan_id, "bucket": decision.bucket, "promised_amount": body.promised_amount, "promised_date": body.promised_date, "status": "recorded"}
