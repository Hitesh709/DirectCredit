from datetime import date
from types import SimpleNamespace
from backend.phase2h_servicing import PHASE2H_VERSION, installment_metrics, servicing_contract


def row(**kwargs):
    base = dict(id=1, installment=1, due_date="2026-09-01", due_amount=1000, paid_amount=0)
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_contract_versioned():
    contract = servicing_contract()
    assert contract["version"] == PHASE2H_VERSION
    assert contract["rules"]["payment_allocation"] == "oldest outstanding installment first"


def test_paid_installment_has_zero_dpd():
    result = installment_metrics(row(paid_amount=1000), as_of=date(2026, 9, 17))
    assert result["state"] == "PAID"
    assert result["dpd"] == 0


def test_overdue_installment_calculates_dpd():
    result = installment_metrics(row(), as_of=date(2026, 9, 17))
    assert result["state"] == "OVERDUE"
    assert result["dpd"] == 16
    assert result["unpaid_amount"] == 1000
