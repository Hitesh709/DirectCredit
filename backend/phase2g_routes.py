"""Phase 2G customer-scoped disbursement APIs."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .auth import get_current_customer
from .database import get_db
from .db_models import AuditEventRecord, CustomerBankAccountRecord, CustomerEventRecord, LoanRecord, RepaymentRecord
from .loan_lifecycle import can_transition
from .phase2e_offer_engine import offer_is_active, parse_offer
from .phase2g_disbursement import (PHASE2G_VERSION, build_disbursement_request,
                                   disbursement_contract, disbursement_payload,
                                   repayment_schedule, verify_callback)

router = APIRouter(prefix="/api/v1/disbursement", tags=["loan-disbursement"])


def _owner(customer_id, claims):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")


def _loan(db, customer_id, loan_id):
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "loan_not_found")
    if int(loan.customer_id) != int(customer_id):
        raise HTTPException(403, "loan_access_forbidden")
    return loan


def _audit(db, customer_id, loan_id, action, outcome, reason, details):
    db.add(AuditEventRecord(
        event_id=str(uuid.uuid4()), actor_type="customer", actor_id=str(customer_id),
        action=action, entity_type="loan_disbursement", entity_id=str(loan_id),
        customer_id=customer_id, loan_id=loan_id, source="phase2g", outcome=outcome,
        reason_code=reason, details=json.dumps(details, ensure_ascii=False),
    ))


@router.get("/contract")
def contract():
    return disbursement_contract()


@router.get("/{customer_id}/{loan_id}/status")
def status(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    loan = _loan(db, customer_id, loan_id)
    p = disbursement_payload(loan.disbursement_details)
    return {
        "phase": PHASE2G_VERSION,
        "loan_status": loan.status,
        "stage": loan.current_stage,
        "disbursement": p.get("disbursement", {"status": "NOT_STARTED"}),
        "schedule_count": db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).count(),
        "disbursed_amount": loan.disbursed_amount,
        "outstanding_amount": loan.outstanding_amount,
    }


@router.post("/{customer_id}/{loan_id}/start")
def start(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    loan = _loan(db, customer_id, loan_id)
    offer = parse_offer(loan)
    p = disbursement_payload(loan.disbursement_details)
    existing = p.get("disbursement")
    if existing and existing.get("status") in ("PENDING", "SUCCESS"):
        return {"status": "existing_request", "disbursement": existing}
    if not offer or offer.get("offer_status") != "ACCEPTED":
        raise HTTPException(409, "accepted_offer_required")
    if loan.status != "disbursement_pending":
        raise HTTPException(409, "loan_not_ready_for_disbursement")
    if not can_transition(loan.status, "disbursed"):
        raise HTTPException(409, "invalid_disbursement_transition")
    if not offer_is_active(offer, allow_accepted=True):
        raise HTTPException(409, "accepted_offer_invalid_or_expired")

    mandate = p.get("mandate", {})
    esign = p.get("esign", {})
    if esign.get("status") != "SIGNED":
        raise HTTPException(409, "completed_esign_required")
    if mandate.get("status") != "ACTIVE":
        raise HTTPException(409, "active_mandate_required")

    bank = db.query(CustomerBankAccountRecord).filter(
        CustomerBankAccountRecord.customer_id == customer_id,
        CustomerBankAccountRecord.is_primary == True,
        CustomerBankAccountRecord.verification_status.in_(["verified", "success", "active"]),
    ).first()
    if not bank:
        raise HTTPException(409, "verified_primary_bank_account_required")

    amount = round(float(loan.sanctioned_amount or loan.eligible_amount or loan.requested_amount or 0), 2)
    if amount <= 0 or amount > float(loan.requested_amount or amount):
        raise HTTPException(409, "invalid_disbursement_amount")
    beneficiary = {"bank_name": bank.bank_name, "account_number_masked": bank.account_number_masked, "ifsc": bank.ifsc}
    req = build_disbursement_request(customer_id=customer_id, loan_id=loan_id, amount=amount, beneficiary=beneficiary)
    p["disbursement"] = req
    loan.disbursement_details = json.dumps(p, ensure_ascii=False)
    if req["status"] == "PENDING":
        loan.status = "disbursement_pending"
        loan.current_stage = "DISBURSEMENT"
    db.add(CustomerEventRecord(customer_id=customer_id, event_type="DISBURSEMENT_REQUESTED", event_status="completed", source="phase2g", actor_type="customer", actor_id=str(customer_id), details=json.dumps(req)))
    _audit(db, customer_id, loan_id, "disbursement_requested", "success", req.get("reason", "request_created"), req)
    db.commit()
    return {"status": "created", "disbursement": req}


@router.post("/{customer_id}/{loan_id}/callback")
def callback(customer_id: int, loan_id: int, status_value: str, request_id: str | None = None, provider_reference: str | None = None, signature: str | None = Header(default=None), db: Session = Depends(get_db)):
    loan = _loan(db, customer_id, loan_id)
    secret = __import__('os').getenv("DC_DISBURSEMENT_CALLBACK_SECRET", "")
    body = json.dumps({"customer_id": customer_id, "loan_id": loan_id, "status": status_value, "request_id": request_id, "provider_reference": provider_reference}, sort_keys=True)
    if not verify_callback(body, signature or "", secret):
        raise HTTPException(401, "invalid_callback_signature")
    state = status_value.upper()
    if state not in ("SUCCESS", "FAILED", "REVERSED"):
        raise HTTPException(422, "unsupported_disbursement_status")
    p = disbursement_payload(loan.disbursement_details)
    req = p.get("disbursement", {})
    if request_id and req.get("request_id") and request_id != req["request_id"]:
        raise HTTPException(409, "request_id_mismatch")
    req.update({"status": state, "provider_reference": provider_reference, "completed_at": datetime.now(timezone.utc).isoformat()})
    p["disbursement"] = req
    if state == "SUCCESS":
        amount = round(float(req.get("amount") or 0), 2)
        loan.disbursed_amount = amount
        loan.outstanding_amount = amount
        loan.status = "active"
        loan.current_stage = "REPAYMENT"
        if db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).count() == 0:
            schedule = repayment_schedule(loan_id=loan_id, principal=amount, annual_rate=float(loan.interest_rate or 0), tenure_months=int(loan.tenure_months or 1))
            for row in schedule:
                db.add(RepaymentRecord(**row))
            p["repayment_schedule"] = {"version": PHASE2G_VERSION, "created_at": datetime.now(timezone.utc).isoformat(), "count": len(schedule)}
    elif state == "REVERSED":
        loan.disbursed_amount = 0
        loan.outstanding_amount = 0
        loan.status = "disbursement_pending"
        loan.current_stage = "DISBURSEMENT"
    else:
        loan.status = "disbursement_pending"
        loan.current_stage = "DISBURSEMENT"
    loan.disbursement_details = json.dumps(p, ensure_ascii=False)
    _audit(db, customer_id, loan_id, "disbursement_callback", "success", "provider_callback", req)
    db.add(CustomerEventRecord(customer_id=customer_id, event_type="DISBURSEMENT_" + state, event_status="completed", source="phase2g", actor_type="provider", actor_id=provider_reference, details=json.dumps(req)))
    db.commit()
    return {"status": "processed", "disbursement": req, "loan_status": loan.status, "disbursed_amount": loan.disbursed_amount, "schedule_count": db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).count()}
