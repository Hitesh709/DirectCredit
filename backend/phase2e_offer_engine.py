"""Phase 2E: loan offer generation, acceptance and audit-ready offer contract.

Phase 2E converts a clean Phase 2D APPROVE decision into a customer-facing
loan offer. Offer state is stored in LoanRecord.disbursement_details so this
phase does not require a destructive database migration.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

OFFER_POLICY_VERSION = "MBL-OFFER-2E-v1"
OFFER_VALIDITY_HOURS = 24
# Product pricing is configuration, not a credit decision. These are initial
# MBL defaults and should be moved to the policy/config service before launch.
RATE_BY_APPROVAL = {100: 18.0, 90: 21.0, 80: 24.0}
TENURE_OPTIONS = (6, 9, 12, 18, 24)
DEFAULT_TENURE_MONTHS = 12


def _money(value: float) -> float:
    return round(float(value or 0), 2)


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    principal = float(principal or 0)
    n = int(tenure_months)
    if principal <= 0 or n <= 0:
        return 0.0
    monthly_rate = float(annual_rate) / 12 / 100
    if monthly_rate == 0:
        return _money(principal / n)
    emi = principal * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)
    return _money(emi)


def build_offer(*, customer_id: int, loan_id: int, requested_amount: float,
                eligible_amount: float, approval_percent: int, decision: str,
                score: float, policy_version: str, tenure_months: int = DEFAULT_TENURE_MONTHS,
                now: datetime | None = None) -> dict[str, Any]:
    if str(decision).upper() != "APPROVE":
        raise ValueError("offer_requires_approved_policy_decision")
    approval = int(approval_percent or 0)
    rate = RATE_BY_APPROVAL.get(approval)
    if rate is None:
        raise ValueError("unsupported_approval_pricing_band")
    tenure = int(tenure_months)
    if tenure not in TENURE_OPTIONS:
        raise ValueError("unsupported_tenure")
    amount = math.floor(min(float(eligible_amount or 0), float(requested_amount or 0)))
    if amount <= 0:
        raise ValueError("offer_amount_must_be_positive")
    issued = now or datetime.now(timezone.utc)
    expires = issued + timedelta(hours=OFFER_VALIDITY_HOURS)
    emi = calculate_emi(amount, rate, tenure)
    total_payable = _money(emi * tenure)
    return {
        "offer_id": str(uuid.uuid4()),
        "offer_status": "ACTIVE",
        "offer_policy_version": OFFER_POLICY_VERSION,
        "policy_version": policy_version,
        "customer_id": int(customer_id),
        "loan_id": int(loan_id),
        "approved_amount": amount,
        "requested_amount": _money(requested_amount),
        "approval_percent": approval,
        "annual_interest_rate": rate,
        "interest_rate_type": "reducing_balance",
        "tenure_months": tenure,
        "emi": emi,
        "total_payable": total_payable,
        "total_interest": _money(max(0, total_payable - amount)),
        "currency": "INR",
        "issued_at": issued.isoformat(),
        "expires_at": expires.isoformat(),
        "conditions": [
            "KYC and required document verification must remain valid",
            "customer acceptance is required before e-sign and mandate",
            "final disbursement remains subject to mandate activation and operational checks",
        ],
        "decision_score": float(score),
    }


def parse_offer(loan) -> dict[str, Any] | None:
    try:
        payload = json.loads(loan.disbursement_details or "{}")
    except (TypeError, ValueError):
        return None
    offer = payload.get("offer") if isinstance(payload, dict) else None
    return offer if isinstance(offer, dict) else None


def save_offer(loan, offer: dict[str, Any]) -> None:
    try:
        payload = json.loads(loan.disbursement_details or "{}")
    except (TypeError, ValueError):
        payload = {}
    payload["offer"] = offer
    loan.disbursement_details = json.dumps(payload, ensure_ascii=False)
    loan.eligible_amount = offer["approved_amount"]
    loan.sanctioned_amount = offer["approved_amount"]
    loan.interest_rate = offer["annual_interest_rate"]
    loan.tenure_months = offer["tenure_months"]
    loan.monthly_emi = offer["emi"]


def offer_is_active(offer: dict[str, Any], now: datetime | None = None) -> bool:
    if str(offer.get("offer_status", "")).upper() != "ACTIVE":
        return False
    try:
        expires = datetime.fromisoformat(str(offer["expires_at"]))
    except (KeyError, ValueError, TypeError):
        return False
    current = now or datetime.now(timezone.utc)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return current < expires
