from backend.phase2p_reconciliation import reconcile_loan, reconciliation_contract

def test_contract_version():
    assert reconciliation_contract()["version"] == "MBL-RECONCILIATION-2P-v1"

def test_clean_reconciliation():
    r = reconcile_loan(loan_id=1, expected_amount=10000, observed_amount=10000, repayment_references=["PAY-1"])
    assert r.status == "RECONCILED"
    assert r.variance == 0
    assert r.exceptions == ()

def test_duplicate_and_unallocated_payment_are_exceptions():
    r = reconcile_loan(loan_id=2, expected_amount=10000, observed_amount=11000, repayment_references=["PAY-1", "PAY-1"], duplicate_references=1, unallocated_amount=1000)
    assert r.status == "EXCEPTION"
    assert "DUPLICATE_PAYMENT_REFERENCE" in r.exceptions
    assert "UNALLOCATED_PAYMENT" in r.exceptions
    assert "PAYMENT_AMOUNT_MISMATCH" in r.exceptions

def test_missing_reference_only_when_money_observed():
    r = reconcile_loan(loan_id=3, expected_amount=0, observed_amount=500, repayment_references=[])
    assert "PAYMENT_REFERENCE_MISSING" in r.exceptions

def test_tolerance_is_respected():
    r = reconcile_loan(loan_id=4, expected_amount=10000, observed_amount=10000.50, repayment_references=["PAY-4"], tolerance=1)
    assert r.status == "RECONCILED"
