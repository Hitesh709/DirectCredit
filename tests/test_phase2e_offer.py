from datetime import datetime, timezone, timedelta

from backend.phase2e_offer_engine import build_offer, calculate_emi, offer_is_active


def test_emi_is_deterministic():
    assert calculate_emi(100000, 18, 12) == 9168.75


def test_100_percent_offer():
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    offer = build_offer(customer_id=1, loan_id=2, requested_amount=150000,
                        eligible_amount=150000, approval_percent=100,
                        decision="APPROVE", score=108, policy_version="MBL-POLICY-2D-v1", now=now)
    assert offer["approved_amount"] == 150000
    assert offer["annual_interest_rate"] == 18.0
    assert offer["tenure_months"] == 12
    assert offer["offer_status"] == "ACTIVE"
    assert offer_is_active(offer, now=now)
    assert not offer_is_active(offer, now=now + timedelta(hours=24, seconds=1))


def test_80_percent_band():
    offer = build_offer(customer_id=1, loan_id=2, requested_amount=150000,
                        eligible_amount=120000, approval_percent=80,
                        decision="APPROVE", score=96, policy_version="MBL-POLICY-2D-v1")
    assert offer["approved_amount"] == 120000
    assert offer["annual_interest_rate"] == 24.0


def test_non_approval_cannot_create_offer():
    try:
        build_offer(customer_id=1, loan_id=2, requested_amount=100000,
                    eligible_amount=0, approval_percent=0, decision="MANUAL_REVIEW",
                    score=70, policy_version="MBL-POLICY-2D-v1")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "offer_requires_approved_policy_decision"
