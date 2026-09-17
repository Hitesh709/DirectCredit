"""Phase 2H loan servicing: EMI status, DPD, overdue and payoff contracts."""
from __future__ import annotations
from datetime import date

PHASE2H_VERSION = "MBL-SERVICING-2H-v1"

SERVICING_STATES = ("ACTIVE", "OVERDUE", "REPAID", "CLOSED")


def servicing_contract() -> dict:
    return {
        "version": PHASE2H_VERSION,
        "states": list(SERVICING_STATES),
        "rules": {
            "dpd": "days from due date while installment remains unpaid",
            "overdue": "unpaid installments with DPD > 0",
            "payment_allocation": "oldest outstanding installment first",
            "payoff": "remaining principal/interest is provider-policy dependent; never invent a quote",
            "source_of_truth": "repayment ledger",
        },
        "principles": [
            "servicing is ledger-driven",
            "payments are idempotent by provider/reference where available",
            "no payment is considered successful without a recorded receipt",
            "customer and loan scope is enforced at API boundary",
        ],
    }


def installment_metrics(row, as_of: date | None = None) -> dict:
    due = float(row.due_amount or 0)
    paid = float(row.paid_amount or 0)
    unpaid = max(0.0, due - paid)
    try:
        due_day = date.fromisoformat(str(row.due_date)[:10])
        today = as_of or date.today()
        dpd = 0 if unpaid <= 0 else max(0, (today - due_day).days)
    except ValueError:
        dpd = 0
    if unpaid <= 0:
        state = "PAID"
    elif dpd > 0:
        state = "OVERDUE"
    else:
        state = "DUE"
    return {"repayment_id": row.id, "installment": row.installment, "due_date": row.due_date,
            "due_amount": due, "paid_amount": paid, "unpaid_amount": unpaid, "dpd": dpd, "state": state}
