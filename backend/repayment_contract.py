"""Canonical repayment and collection contract for DirectCredit."""
from datetime import date
from typing import Optional

REPAYMENT_STATUSES = (
    "upcoming",
    "due",
    "paid",
    "partially_paid",
    "overdue",
    "bounced",
    "waived",
    "cancelled",
)

PAYMENT_METHODS = (
    "upi",
    "bank_transfer",
    "nach",
    "cash",
    "card",
    "other",
)


def normalize_repayment_status(status: Optional[str]) -> str:
    value = str(status or "upcoming").strip().lower().replace("-", "_")
    aliases = {"pending": "upcoming", "partial": "partially_paid", "part_paid": "partially_paid"}
    value = aliases.get(value, value)
    if value not in REPAYMENT_STATUSES:
        raise ValueError(f"Unsupported repayment status: {status}")
    return value


def calculate_dpd(due_date: str, paid_amount: float, due_amount: float, as_of: Optional[date] = None) -> int:
    if float(paid_amount or 0) >= float(due_amount or 0):
        return 0
    try:
        due = date.fromisoformat(str(due_date)[:10])
    except ValueError:
        return 0
    today = as_of or date.today()
    return max(0, (today - due).days)


def derive_status(due_date: str, due_amount: float, paid_amount: float, as_of: Optional[date] = None) -> str:
    due = float(due_amount or 0)
    paid = max(0.0, float(paid_amount or 0))
    if due <= 0:
        raise ValueError("Due amount must be greater than zero")
    if paid >= due:
        return "paid"
    try:
        due_day = date.fromisoformat(str(due_date)[:10])
        today = as_of or date.today()
        if paid > 0:
            return "partially_paid" if today <= due_day else "overdue"
        return "due" if today >= due_day else "upcoming"
    except ValueError:
        return "upcoming"


def repayment_payload(record, as_of: Optional[date] = None) -> dict:
    status = normalize_repayment_status(record.status)
    dpd = calculate_dpd(record.due_date, record.paid_amount, record.due_amount, as_of)
    return {
        "id": record.id,
        "loan_id": record.loan_id,
        "installment": record.installment,
        "due_date": record.due_date,
        "due_amount": float(record.due_amount or 0),
        "paid_amount": float(record.paid_amount or 0),
        "unpaid_amount": max(0.0, float(record.due_amount or 0) - float(record.paid_amount or 0)),
        "status": status,
        "dpd": dpd,
        "payment_reference": record.payment_reference,
        "payment_method": record.payment_method,
        "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        "bounce_reason": record.bounce_reason,
    }
