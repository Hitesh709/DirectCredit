"""Phase 2E customer-facing loan offer APIs."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import get_current_customer
from .database import get_db
from .db_models import AuditEventRecord, CustomerEventRecord, CustomerRecord, LoanRecord
from .phase2d_routes import preview as policy_preview
from .phase2e_offer_engine import (
    DEFAULT_TENURE_MONTHS, OFFER_POLICY_VERSION, TENURE_OPTIONS,
    build_offer, offer_is_active, parse_offer, save_offer,
)

router = APIRouter(prefix="/api/v1/offers", tags=["loan-offers"])


def _owner(customer_id: int, claims: dict) -> None:
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(403, "customer_scope_forbidden")


def _audit(db: Session, *, customer_id: int, loan_id: int, action: str, outcome: str,
           reason_code: str, details: dict) -> None:
    db.add(AuditEventRecord(
        event_id=str(uuid.uuid4()), actor_type="customer", actor_id=str(customer_id),
        action=action, entity_type="loan_offer", entity_id=str(loan_id),
        customer_id=customer_id, loan_id=loan_id, source="phase2e", outcome=outcome,
        reason_code=reason_code, details=json.dumps(details, ensure_ascii=False),
    ))


def _loan_for_customer(db: Session, customer_id: int, loan_id: int) -> LoanRecord:
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "loan_not_found")
    if int(loan.customer_id) != int(customer_id):
        raise HTTPException(403, "loan_access_forbidden")
    return loan


@router.get("/contract")
def offer_contract():
    return {
        "offer_policy_version": OFFER_POLICY_VERSION,
        "validity_hours": 24,
        "tenure_options_months": list(TENURE_OPTIONS),
        "default_tenure_months": DEFAULT_TENURE_MONTHS,
        "pricing_basis": "approval_percent_band",
        "states": ["ACTIVE", "ACCEPTED", "EXPIRED", "DECLINED"],
    }


@router.post("/{customer_id}/{loan_id}/generate")
def generate_offer(customer_id: int, loan_id: int, tenure_months: int = DEFAULT_TENURE_MONTHS,
                   db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "customer_not_found")
    loan = _loan_for_customer(db, customer_id, loan_id)
    existing = parse_offer(loan)
    if existing and offer_is_active(existing):
        return {"status": "existing_offer", "offer": existing}

    preview = policy_preview(customer_id, loan_id=loan_id, db=db, claims=claims)
    policy = preview["policy"]
    if policy["decision"] != "APPROVE":
        raise HTTPException(409, {"code": "offer_not_available", "decision": policy["decision"],
                                   "reasons": policy.get("reasons", []),
                                   "review_reasons": policy.get("review_reasons", [])})
    try:
        offer = build_offer(
            customer_id=customer_id, loan_id=loan_id,
            requested_amount=float(loan.requested_amount or 0),
            eligible_amount=float(policy["eligible_amount"] or 0),
            approval_percent=int(policy["approval_percent"] or 0),
            decision=policy["decision"], score=float(preview["credit"]["score"]),
            policy_version=policy["policy_version"], tenure_months=tenure_months,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    save_offer(loan, offer)
    loan.status = "sanctioned"
    loan.current_stage = "SANCTION"
    db.add(CustomerEventRecord(customer_id=customer_id, event_type="LOAN_OFFER_GENERATED",
                               event_status="completed", source="phase2e", actor_type="customer",
                               actor_id=str(customer_id), details=json.dumps({"loan_id": loan_id, "offer_id": offer["offer_id"]})))
    _audit(db, customer_id=customer_id, loan_id=loan_id, action="offer_generated", outcome="success",
           reason_code="offer_created", details=offer)
    db.commit()
    return {"status": "created", "offer": offer}


@router.get("/{customer_id}/{loan_id}")
def get_offer(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    loan = _loan_for_customer(db, customer_id, loan_id)
    offer = parse_offer(loan)
    if not offer:
        raise HTTPException(404, "offer_not_found")
    if offer_is_active(offer):
        return {"offer": offer}
    if offer.get("offer_status") == "ACTIVE":
        offer["offer_status"] = "EXPIRED"
        save_offer(loan, offer)
        db.commit()
    return {"offer": offer}


@router.post("/{customer_id}/{loan_id}/accept")
def accept_offer(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    loan = _loan_for_customer(db, customer_id, loan_id)
    offer = parse_offer(loan)
    if not offer:
        raise HTTPException(404, "offer_not_found")
    if not offer_is_active(offer):
        raise HTTPException(409, "offer_expired_or_inactive")
    offer["offer_status"] = "ACCEPTED"
    offer["accepted_at"] = datetime.now(timezone.utc).isoformat()
    save_offer(loan, offer)
    loan.status = "customer_approved"
    loan.current_stage = "CUSTOMER_APPROVAL"
    db.add(CustomerEventRecord(customer_id=customer_id, event_type="LOAN_OFFER_ACCEPTED",
                               event_status="completed", source="phase2e", actor_type="customer",
                               actor_id=str(customer_id), details=json.dumps({"loan_id": loan_id, "offer_id": offer["offer_id"]})))
    _audit(db, customer_id=customer_id, loan_id=loan_id, action="offer_accepted", outcome="success",
           reason_code="customer_accepted_offer", details={"offer_id": offer["offer_id"]})
    db.commit()
    return {"status": "accepted", "loan_status": loan.status, "next_stage": loan.current_stage, "offer": offer}


@router.post("/{customer_id}/{loan_id}/decline")
def decline_offer(customer_id: int, loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    _owner(customer_id, claims)
    loan = _loan_for_customer(db, customer_id, loan_id)
    offer = parse_offer(loan)
    if not offer or not offer_is_active(offer):
        raise HTTPException(409, "offer_expired_or_inactive")
    offer["offer_status"] = "DECLINED"
    offer["declined_at"] = datetime.now(timezone.utc).isoformat()
    save_offer(loan, offer)
    loan.status = "cancelled"
    loan.current_stage = "ASSESSMENT"
    _audit(db, customer_id=customer_id, loan_id=loan_id, action="offer_declined", outcome="success",
           reason_code="customer_declined_offer", details={"offer_id": offer["offer_id"]})
    db.commit()
    return {"status": "declined", "loan_status": loan.status, "offer": offer}
