"""Smoke coverage for Tasks 31-50: eligibility plus admin operations contracts."""
from backend.eligibility_engine import evaluate


def test_tasks_31_40_no_unconfigured_score():
    result = evaluate(
        {"monthly_income": 30000, "existing_emi": 5000},
        {"requested_amount": 10000, "tenure_months": 6},
        None,
    )
    assert result.score is None
    assert result.scorecard_source == "scorecard_not_configured"
    assert result.decision == "Not assessed"


def test_tasks_31_40_configured_scorecard():
    result = evaluate(
        {"monthly_income": 30000, "existing_emi": 3000},
        {"requested_amount": 10000, "tenure_months": 6},
        {"configured": True, "score": 110, "auto_approval_threshold": 100},
    )
    assert result.scorecard_source == "configured_125_point_scorecard"
    assert result.decision == "Approve"
    assert result.eligible_amount is not None


def test_tasks_31_40_amount_and_tenure_validation():
    result = evaluate(
        {"monthly_income": 30000, "existing_emi": 0},
        {"requested_amount": 20000, "tenure_months": 5},
        {"configured": True, "score": 120, "auto_approval_threshold": 100},
    )
    assert "requested_amount_outside_mbl_range" in result.reasons
    assert "unsupported_tenure" in result.reasons
