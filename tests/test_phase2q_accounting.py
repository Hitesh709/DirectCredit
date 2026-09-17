from backend.phase2q_accounting import validate_journal, ledger_summary, accounting_contract

def test_contract_version():
    assert accounting_contract()["version"] == "MBL-ACCOUNTING-2Q-v1"

def test_balanced_journal():
    r = validate_journal(debit=1000, credit=1000)
    assert r.status == "VALID"
    assert r.reason == "BALANCED"

def test_unbalanced_journal_rejected():
    r = validate_journal(debit=1000, credit=900)
    assert r.status == "REJECTED"
    assert r.reason == "UNBALANCED_JOURNAL"

def test_empty_journal_rejected():
    assert validate_journal(debit=0, credit=0).reason == "EMPTY_JOURNAL"

def test_ledger_summary():
    s = ledger_summary([{"debit": 1000, "credit": 0}, {"debit": 0, "credit": 1000}])
    assert s["status"] == "BALANCED"
    assert s["balance"] == 0
