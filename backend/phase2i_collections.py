"""Phase 2I collections and auto-debit orchestration contracts.

This module is provider-neutral: it creates auditable debit requests but never
moves money itself. A licensed payment/mandate provider must confirm success
before a receipt is posted to the repayment ledger.
"""
from dataclasses import dataclass
from datetime import date, datetime
import os

PHASE2I_VERSION = "MBL-COLLECTIONS-2I-v1"
MAX_AUTO_DEBIT_RETRIES = int(os.getenv("DC_MAX_AUTO_DEBIT_RETRIES", "3"))
RETRY_DELAY_HOURS = int(os.getenv("DC_AUTO_DEBIT_RETRY_DELAY_HOURS", "24"))

BUCKETS = (
    "CURRENT",
    "DPD_1_7",
    "DPD_8_30",
    "DPD_31_60",
    "DPD_61_90",
    "DPD_90_PLUS",
)

@dataclass(frozen=True)
class CollectionDecision:
    bucket: str
    overdue_amount: float
    auto_debit_eligible: bool
    retry_allowed: bool
    retry_number: int
    reason: str


def _due_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def dpd(due_date, paid_amount, due_amount, as_of=None):
    if float(paid_amount or 0) >= float(due_amount or 0):
        return 0
    today = as_of or date.today()
    return max(0, (today - _due_date(due_date)).days)


def collection_bucket(dpd_value):
    d = int(dpd_value or 0)
    if d <= 0: return "CURRENT"
    if d <= 7: return "DPD_1_7"
    if d <= 30: return "DPD_8_30"
    if d <= 60: return "DPD_31_60"
    if d <= 90: return "DPD_61_90"
    return "DPD_90_PLUS"


def overdue_amount(rows, as_of=None):
    total = 0.0
    max_dpd = 0
    for row in rows:
        d = dpd(row.due_date, row.paid_amount, row.due_amount, as_of)
        if d > 0:
            total += max(0.0, float(row.due_amount or 0) - float(row.paid_amount or 0))
            max_dpd = max(max_dpd, d)
    return round(total, 2), max_dpd


def count_debit_attempts(actions):
    """Count all persisted auto-debit request action spellings."""
    debit_types = {"debit_request", "auto_debit_request"}
    return sum(1 for x in actions if str(getattr(x, "action_type", "")) in debit_types)


def decide_collection(rows, actions, mandate_active=True, as_of=None):
    amount, max_dpd = overdue_amount(rows, as_of)
    attempts = count_debit_attempts(actions)
    bucket = collection_bucket(max_dpd)
    eligible = amount > 0 and mandate_active and bucket != "DPD_90_PLUS"
    retry_allowed = eligible and attempts < MAX_AUTO_DEBIT_RETRIES
    if amount <= 0:
        reason = "no_overdue_amount"
    elif not mandate_active:
        reason = "active_mandate_required"
    elif bucket == "DPD_90_PLUS":
        reason = "manual_collection_bucket"
    elif not retry_allowed:
        reason = "maximum_auto_debit_attempts_reached"
    else:
        reason = "auto_debit_eligible"
    return CollectionDecision(bucket, amount, eligible, retry_allowed, attempts + 1, reason)


def collections_contract():
    return {
        "version": PHASE2I_VERSION,
        "buckets": list(BUCKETS),
        "rules": {
            "allocation": "oldest outstanding installment first",
            "auto_debit": "provider request only; provider confirmation required before receipt",
            "idempotency": "one provider/reference cannot be posted twice",
            "max_auto_debit_retries": MAX_AUTO_DEBIT_RETRIES,
            "retry_delay_hours": RETRY_DELAY_HOURS,
            "dpd_90_plus": "manual collection workflow; no automatic debit retry by default",
            "promise_to_pay": "auditable collection action; never marks a repayment paid",
        },
        "actions": ["auto_debit_request", "auto_debit_callback", "promise_to_pay", "reminder", "contact", "field_visit"],
    }
