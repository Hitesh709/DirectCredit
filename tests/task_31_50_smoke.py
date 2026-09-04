"""Contract smoke tests for Tasks 31-50.

These tests intentionally verify data boundaries rather than external-provider
success. Provider integrations remain explicit adapters and must not fabricate
results.
"""
from backend.eligibility_engine import assess, MIN_LOAN, MAX_LOAN


def test_task_31_40_eligibility_boundaries():
    r = assess(requested_amount=10_000, tenure_months=12)
    assert r.decision == "REFER"
    assert r.score is None
    assert r.score_source == "scorecard_not_configured"
    assert "required_assessment_inputs_unavailable" in r.reasons


def test_task_33_amount_boundaries():
    assert assess(requested_amount=MIN_LOAN, tenure_months=12).requested_amount == 5_000
    assert assess(requested_amount=MAX_LOAN, tenure_months=12).requested_amount == 15_000
    assert "requested_amount_outside_mbl_range" in assess(requested_amount=4_999, tenure_months=12).reasons


def test_task_36_foir():
    r = assess(requested_amount=10_000, tenure_months=12, monthly_income=20_000, existing_emi=12_000, bureau_score=750, banking_score=80)
    assert r.foir == 0.6
    assert "foir_above_policy_limit" in r.reasons


def test_task_40_decision_requires_official_scorecard():
    r = assess(requested_amount=10_000, tenure_months=12, monthly_income=50_000, existing_emi=5_000, bureau_score=750, banking_score=90)
    assert r.decision == "REFER"
    assert "official_scorecard_not_configured" in r.reasons


def test_task_41_50_contract_modules_exist():
    # Tasks 41-50 consume canonical customer/loan/document records. This test
    # deliberately avoids asserting fake admin data.
    from backend import admin_ops_routes  # noqa: F401
    assert hasattr(admin_ops_routes, "router")
