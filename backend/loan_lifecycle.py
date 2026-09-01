"""Canonical loan lifecycle contract used by Customer Portal, Admin and APIs."""

from typing import Optional

# One canonical vocabulary for the loan's business lifecycle.
LOAN_STATUSES = (
    "draft",
    "assessment",
    "sanctioned",
    "customer_approved",
    "esign_pending",
    "esigned",
    "mandate_pending",
    "mandate_active",
    "disbursement_pending",
    "disbursed",
    "active",
    "overdue",
    "repaid",
    "closed",
    "rejected",
    "cancelled",
)

# The application journey remains separately addressable from the financial status.
LOAN_STAGES = (
    "PAN",
    "AADHAAR",
    "SELFIE",
    "BUREAU",
    "PROFILE",
    "BANK_ANALYSIS",
    "DOCUMENTS",
    "ASSESSMENT",
    "SANCTION",
    "CUSTOMER_APPROVAL",
    "E_SIGN",
    "E_MANDATE",
    "DISBURSEMENT",
    "REPAYMENT",
    "CLOSED",
)

STATUS_TO_STAGE = {
    "draft": "PAN",
    "assessment": "ASSESSMENT",
    "sanctioned": "SANCTION",
    "customer_approved": "CUSTOMER_APPROVAL",
    "esign_pending": "E_SIGN",
    "esigned": "E_SIGN",
    "mandate_pending": "E_MANDATE",
    "mandate_active": "E_MANDATE",
    "disbursement_pending": "DISBURSEMENT",
    "disbursed": "DISBURSEMENT",
    "active": "REPAYMENT",
    "overdue": "REPAYMENT",
    "repaid": "REPAYMENT",
    "closed": "CLOSED",
    "rejected": "ASSESSMENT",
    "cancelled": "ASSESSMENT",
}

# Allowed forward/operational transitions. Terminal statuses may only be re-opened
# through an explicit admin operation in a future task, not a generic status patch.
TRANSITIONS = {
    "draft": {"assessment", "rejected", "cancelled"},
    "assessment": {"sanctioned", "rejected", "cancelled"},
    "sanctioned": {"customer_approved", "rejected", "cancelled"},
    "customer_approved": {"esign_pending", "cancelled"},
    "esign_pending": {"esigned", "cancelled"},
    "esigned": {"mandate_pending", "cancelled"},
    "mandate_pending": {"mandate_active", "cancelled"},
    "mandate_active": {"disbursement_pending", "cancelled"},
    "disbursement_pending": {"disbursed", "cancelled"},
    "disbursed": {"active", "overdue", "repaid", "closed"},
    "active": {"overdue", "repaid", "closed"},
    "overdue": {"active", "repaid", "closed"},
    "repaid": {"closed"},
    "closed": set(),
    "rejected": set(),
    "cancelled": set(),
}

# Legacy values already present in older demo records are normalized here.
STATUS_ALIASES = {
    "pending": "assessment",
    "approved": "sanctioned",
    "sanction": "sanctioned",
    "disbursement": "disbursement_pending",
    "repayment": "active",
}
STAGE_ALIASES = {
    "BANK STATEMENT": "BANK_ANALYSIS",
    "BANK_STATEMENT": "BANK_ANALYSIS",
    "BANK ANALYSIS": "BANK_ANALYSIS",
    "CUSTOMER APPROVAL": "CUSTOMER_APPROVAL",
    "E-SIGN": "E_SIGN",
    "E-MANDATE": "E_MANDATE",
}


def normalize_status(status: Optional[str]) -> str:
    value = str(status or "draft").strip().lower()
    value = STATUS_ALIASES.get(value, value)
    if value not in LOAN_STATUSES:
        raise ValueError(f"Unsupported loan status: {status}")
    return value


def normalize_stage(stage: Optional[str], status: Optional[str] = None) -> str:
    value = str(stage or "").strip().upper().replace("-", "_")
    value = STAGE_ALIASES.get(value, value)
    if not value and status:
        value = STATUS_TO_STAGE[normalize_status(status)]
    if value not in LOAN_STAGES:
        raise ValueError(f"Unsupported loan stage: {stage}")
    return value


def can_transition(current: str, target: str) -> bool:
    current = normalize_status(current)
    target = normalize_status(target)
    return current == target or target in TRANSITIONS.get(current, set())


def transition_error(current: str, target: str) -> Optional[str]:
    current = normalize_status(current)
    target = normalize_status(target)
    if current == target:
        return None
    if target not in TRANSITIONS.get(current, set()):
        return f"Invalid loan transition: {current} -> {target}"
    return None


def lifecycle_payload(loan) -> dict:
    status = normalize_status(loan.status)
    stage = normalize_stage(loan.current_stage, status)
    return {
        "loan_id": loan.id,
        "customer_id": loan.customer_id,
        "status": status,
        "stage": stage,
        "stage_from_status": STATUS_TO_STAGE[status],
        "allowed_next_statuses": sorted(TRANSITIONS.get(status, set())),
        "requested_amount": loan.requested_amount,
        "eligible_amount": loan.eligible_amount,
        "sanctioned_amount": loan.sanctioned_amount,
        "disbursed_amount": loan.disbursed_amount,
        "outstanding_amount": loan.outstanding_amount,
        "tenure_months": loan.tenure_months,
        "product": loan.product,
    }
