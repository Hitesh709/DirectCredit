from backend.phase2o_resolution import assess_resolution, resolution_contract


def test_contract_version():
    assert resolution_contract()["version"] == "MBL-RESOLUTION-2O-v1"


def test_zero_balance_is_ready_for_closure():
    r = assess_resolution(loan_id=1, outstanding_amount=0, loan_status="active")
    assert r.state == "READY_FOR_CLOSURE"
    assert r.closure_ready is True
    assert r.resolution_action == "CLOSE_AND_ISSUE_NOC"


def test_outstanding_balance_blocks_noc():
    r = assess_resolution(loan_id=2, outstanding_amount=1000, loan_status="active")
    assert r.closure_ready is False
    assert "OUTSTANDING_BALANCE" in r.blockers


def test_pending_settlement_blocks_closure():
    r = assess_resolution(loan_id=3, outstanding_amount=1000, settlement_status="quoted")
    assert r.state == "SETTLEMENT_PENDING"
    assert "PENDING_SETTLEMENT" in r.blockers


def test_approved_settlement_requires_payment():
    r = assess_resolution(loan_id=4, outstanding_amount=0, settlement_status="approved", settlement_approved_amount=500, settlement_paid_amount=0)
    assert r.state == "SETTLEMENT_APPROVED"
    assert r.closure_ready is False
    assert "APPROVED_SETTLEMENT_UNPAID" in r.blockers


def test_closed_loan_without_blockers_is_closed():
    r = assess_resolution(loan_id=5, outstanding_amount=0, loan_status="closed")
    assert r.state == "CLOSED"
    assert r.closure_ready is True
