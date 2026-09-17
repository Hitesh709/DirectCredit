"""Phase 2G controlled disbursement orchestration and repayment schedule generation."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from datetime import date, timedelta
from dataclasses import dataclass

PHASE2G_VERSION = "MBL-DISBURSEMENT-2G-v1"
DISBURSEMENT_PROVIDER_URL = "DC_DISBURSEMENT_URL"
DISBURSEMENT_PROVIDER_TOKEN = "DC_DISBURSEMENT_TOKEN"
DISBURSEMENT_CALLBACK_SECRET = "DC_DISBURSEMENT_CALLBACK_SECRET"

DISBURSEMENT_STATES = ("NOT_STARTED", "PENDING", "SUCCESS", "FAILED", "REVERSED")


@dataclass(frozen=True)
class DisbursementResult:
    status: str
    request_id: str | None
    amount: float
    reason: str | None = None


def disbursement_contract() -> dict:
    return {
        "version": PHASE2G_VERSION,
        "states": list(DISBURSEMENT_STATES),
        "required_preconditions": [
            "CUSTOMER_APPROVED",
            "ESIGN_SIGNED",
            "MANDATE_ACTIVE",
            "DISBURSEMENT_PENDING",
            "VALID_BENEFICIARY_BANK_ACCOUNT",
        ],
        "success_transition": "DISBURSED -> ACTIVE",
        "principles": [
            "provider-confirmed success only",
            "idempotent request creation",
            "no disbursement before all preconditions pass",
            "loan amount is never increased by the disbursement service",
            "provider callbacks are authenticated and auditable",
            "repayment schedule is created exactly once",
        ],
    }


def callback_signature(body: str, secret: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def verify_callback(body: str, signature: str, secret: str) -> bool:
    if not secret or not signature:
        return False
    return hmac.compare_digest(callback_signature(body, secret), signature)


def provider_configured() -> bool:
    return bool(os.getenv(DISBURSEMENT_PROVIDER_URL) and os.getenv(DISBURSEMENT_PROVIDER_TOKEN))


def build_disbursement_request(*, customer_id: int, loan_id: int, amount: float, beneficiary: dict) -> dict:
    amount = round(float(amount), 2)
    if amount <= 0:
        raise ValueError("disbursement_amount_must_be_positive")
    request_id = str(uuid.uuid4())
    if not provider_configured():
        return {
            "status": "NOT_STARTED",
            "request_id": None,
            "amount": amount,
            "reason": "provider_not_configured",
        }
    return {
        "status": "PENDING",
        "request_id": request_id,
        "amount": amount,
        "customer_id": customer_id,
        "loan_id": loan_id,
        "beneficiary": beneficiary,
        "provider": "configured",
    }


def repayment_schedule(*, loan_id: int, principal: float, annual_rate: float, tenure_months: int, first_due_date: date | None = None) -> list[dict]:
    principal = round(float(principal), 2)
    annual_rate = float(annual_rate or 0)
    tenure_months = int(tenure_months)
    if principal <= 0 or tenure_months <= 0:
        raise ValueError("invalid_repayment_parameters")
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        emi = principal / tenure_months
    else:
        emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
    emi = round(emi, 2)
    first_due_date = first_due_date or (date.today() + timedelta(days=30))
    balance = principal
    rows = []
    for installment in range(1, tenure_months + 1):
        interest = round(balance * monthly_rate, 2)
        principal_component = round(emi - interest, 2)
        if installment == tenure_months:
            principal_component = round(balance, 2)
            installment_amount = round(principal_component + interest, 2)
        else:
            installment_amount = emi
        balance = round(max(0, balance - principal_component), 2)
        due = first_due_date + timedelta(days=30 * (installment - 1))
        rows.append({
            "loan_id": loan_id,
            "installment": installment,
            "due_date": due.isoformat(),
            "due_amount": installment_amount,
            "principal_component": principal_component,
            "interest_component": interest,
            "status": "upcoming",
        })
    return rows


def disbursement_payload(existing: str | None) -> dict:
    try:
        value = json.loads(existing or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}
