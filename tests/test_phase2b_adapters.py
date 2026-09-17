from backend.db_models import BankTransactionRecord
from backend.phase2b_data_adapters import bank_statement_intelligence
from backend.phase2_credit_engine import _unknown_hard_rejects


def tx(date, amount, direction, description="", balance=None, category=""):
    return BankTransactionRecord(
        customer_id=1,
        transaction_date=date,
        amount=amount,
        direction=direction,
        description=description,
        balance=balance,
        category=category,
    )


def test_bank_statement_metrics_use_month_coverage_not_transaction_count():
    rows = [
        tx("2026-01-10", 100000, "credit", balance=10000),
        tx("2026-01-20", 50000, "debit", balance=60000),
        tx("2026-02-10", 120000, "credit", balance=80000),
        tx("2026-03-10", 80000, "credit", balance=90000),
        tx("2026-03-15", 10000, "debit", "NACH ECS returned", balance=80000),
    ]
    result = bank_statement_intelligence(rows)
    assert result["available"] is True
    assert result["coverage_months"] == 3
    assert result["avg_monthly_credits"] == 100000
    assert result["aqb"] == 66000
    assert result["ecs_returns_12m"] == 1


def test_unknown_evidence_does_not_become_a_hard_reject():
    hard = [
        "cibil_enquiries_above_5",
        "no_positive_trade_validation",
        "business_vintage_below_6_months",
        "active_dpd_or_overdue",
    ]
    unavailable = {
        "cibil_unsecured_enquiries_30d",
        "trade_validations",
        "business_vintage_years",
        "active_dpd_overdue",
    }
    assert _unknown_hard_rejects(hard, unavailable) == []


def test_confirmed_policy_event_remains_hard_reject():
    hard = ["gaming_transactions_present", "writeoff_last_3y"]
    assert _unknown_hard_rejects(hard, {"itr_income"}) == hard
