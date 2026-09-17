"""Phase 2M collections control-tower metrics.

Deterministic operational MIS derived from existing collection actions and
repayment records. Metrics are descriptive; this module does not make credit
decisions or post payments.
"""
from datetime import date, datetime

PHASE2M_VERSION = "MBL-CONTROL-TOWER-2M-v1"


def _as_date(value):
    if isinstance(value, datetime): return value.date()
    if isinstance(value, date): return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _action_type(row): return str(getattr(row, "action_type", "") or "").lower()


def _status(row): return str(getattr(row, "status", "") or "").lower()


def _ratio(numerator, denominator):
    return round((float(numerator) / float(denominator)) * 100, 2) if denominator else 0.0


def loan_metrics(rows, actions, as_of=None):
    today = as_of or date.today()
    due = sum(float(getattr(r, "due_amount", 0) or 0) for r in rows)
    paid = sum(float(getattr(r, "paid_amount", 0) or 0) for r in rows)
    overdue_rows = []
    for r in rows:
        paid_amount = float(getattr(r, "paid_amount", 0) or 0)
        due_amount = float(getattr(r, "due_amount", 0) or 0)
        if paid_amount < due_amount and _as_date(getattr(r, "due_date")) < today:
            overdue_rows.append(r)
    overdue = sum(max(0.0, float(getattr(r, "due_amount", 0) or 0) - float(getattr(r, "paid_amount", 0) or 0)) for r in overdue_rows)
    debits = [a for a in actions if "debit" in _action_type(a)]
    debit_success = sum(_status(a) in ("success", "succeeded", "successful") for a in debits)
    debit_failed = sum(_status(a) == "failed" for a in debits)
    ptps = [a for a in actions if _action_type(a) == "promise_to_pay"]
    calls = [a for a in actions if _action_type(a) == "collection_call"]
    visits = [a for a in actions if _action_type(a) == "field_visit"]
    return {
        "due_amount": round(due, 2), "paid_amount": round(paid, 2),
        "overdue_amount": round(overdue, 2), "overdue_installments": len(overdue_rows),
        "collection_rate_pct": _ratio(paid, due),
        "debit_attempts": len(debits), "debit_successes": debit_success, "debit_failures": debit_failed,
        "debit_success_rate_pct": _ratio(debit_success, len(debits)),
        "ptp_count": len(ptps), "call_count": len(calls), "field_visit_count": len(visits),
    }


def aggregate(metrics):
    total_loans=len(metrics)
    total_due=sum(x["due_amount"] for x in metrics)
    total_paid=sum(x["paid_amount"] for x in metrics)
    total_overdue=sum(x["overdue_amount"] for x in metrics)
    total_debits=sum(x["debit_attempts"] for x in metrics)
    total_debit_success=sum(x["debit_successes"] for x in metrics)
    return {
        "loan_count": total_loans,
        "due_amount": round(total_due,2), "paid_amount": round(total_paid,2), "overdue_amount": round(total_overdue,2),
        "collection_rate_pct": _ratio(total_paid,total_due),
        "debit_attempts": total_debits, "debit_successes": total_debit_success,
        "debit_success_rate_pct": _ratio(total_debit_success,total_debits),
        "ptp_count": sum(x["ptp_count"] for x in metrics),
        "call_count": sum(x["call_count"] for x in metrics),
        "field_visit_count": sum(x["field_visit_count"] for x in metrics),
    }


def control_tower_contract():
    return {
        "version": PHASE2M_VERSION,
        "metrics": ["due_amount","paid_amount","overdue_amount","collection_rate_pct","debit_success_rate_pct","ptp_count","call_count","field_visit_count"],
        "principles": ["descriptive operational MIS", "derived from ledger and audited actions", "no credit decision", "no payment posting", "division-by-zero safe"],
    }
