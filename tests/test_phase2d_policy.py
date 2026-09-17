from backend.phase2d_policy_engine import POLICY_VERSION, evaluate_policy, policy_contract


def test_unknown_evidence_routes_to_manual_review():
    result = evaluate_policy(
        score=110,
        score_decision="APPROVE",
        score_approval_percent=100,
        requested_amount=10000,
        unavailable_fields=["cibil_adverse_last_3y"],
    )
    assert result.decision == "MANUAL_REVIEW"
    assert result.approval_percent == 0


def test_confirmed_hard_stop_rejects():
    result = evaluate_policy(
        score=110,
        score_decision="APPROVE",
        score_approval_percent=100,
        requested_amount=10000,
        inputs={"writeoff_last_3y": True},
    )
    assert result.decision == "REJECT"
    assert "writeoff_last_3y" in result.hard_rejects


def test_clean_known_case_preserves_scorecard_band():
    result = evaluate_policy(
        score=106,
        score_decision="APPROVE",
        score_approval_percent=100,
        requested_amount=10000,
    )
    assert result.decision == "APPROVE"
    assert result.eligible_amount == 10000
    assert result.policy_version == POLICY_VERSION


def test_policy_contract_is_versioned():
    contract = policy_contract()
    assert contract["policy_version"] == POLICY_VERSION
    assert set(contract["decision_states"]) == {"APPROVE", "MANUAL_REVIEW", "REJECT"}
