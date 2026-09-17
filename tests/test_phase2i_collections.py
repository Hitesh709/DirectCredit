from datetime import date
from types import SimpleNamespace
from backend.phase2i_collections import PHASE2I_VERSION, collection_bucket, decide_collection, collections_contract

def row(**kwargs):
    base = dict(id=1, installment=1, due_date="2026-09-01", due_amount=1000, paid_amount=0)
    base.update(kwargs)
    return SimpleNamespace(**base)

def action(**kwargs):
    base = dict(action_type="auto_debit_request")
    base.update(kwargs)
    return SimpleNamespace(**base)

def test_contract_versioned():
    assert collections_contract()["version"] == PHASE2I_VERSION

def test_buckets():
    assert collection_bucket(0) == "CURRENT"
    assert collection_bucket(7) == "DPD_1_7"
    assert collection_bucket(30) == "DPD_8_30"
    assert collection_bucket(60) == "DPD_31_60"
    assert collection_bucket(90) == "DPD_61_90"
    assert collection_bucket(91) == "DPD_90_PLUS"

def test_overdue_is_auto_debit_eligible_with_active_mandate():
    result = decide_collection([row()], [], True, date(2026, 9, 17))
    assert result.overdue_amount == 1000
    assert result.bucket == "DPD_8_30"
    assert result.auto_debit_eligible is True
    assert result.retry_allowed is True

def test_no_mandate_blocks_debit():
    result = decide_collection([row()], [], False, date(2026, 9, 17))
    assert result.auto_debit_eligible is False
    assert result.reason == "active_mandate_required"

def test_90_plus_moves_to_manual_collection():
    result = decide_collection([row(due_date="2026-06-01")], [], True, date(2026, 9, 17))
    assert result.bucket == "DPD_90_PLUS"
    assert result.auto_debit_eligible is False

def test_retry_limit():
    actions = [action(), action(), action()]
    result = decide_collection([row()], actions, True, date(2026, 9, 17))
    assert result.retry_allowed is False
    assert result.reason == "maximum_auto_debit_attempts_reached"
