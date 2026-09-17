from backend.phase2j_collections_intelligence import build_priority, collection_bucket, priority_score, urgency


def test_bucket_boundaries():
    assert collection_bucket(0) == "CURRENT"
    assert collection_bucket(7) == "DPD_1_7"
    assert collection_bucket(30) == "DPD_8_30"
    assert collection_bucket(60) == "DPD_31_60"
    assert collection_bucket(90) == "DPD_61_90"
    assert collection_bucket(91) == "DPD_90_PLUS"


def test_priority_is_explainable_and_bounded():
    p = build_priority("DPD_31_60", 30000, 45, ptp_active=True, failed_debit=True)
    assert 0 <= p.score <= 100
    assert p.urgency in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert "AGING_31_PLUS_DPD" in p.reason_codes
    assert "MATERIAL_OVERDUE" in p.reason_codes
    assert "PTP_ACTIVE" in p.reason_codes
    assert "DEBIT_FAILED" in p.reason_codes


def test_90_plus_routes_to_manual_escalation():
    p = build_priority("DPD_90_PLUS", 10000, 120)
    assert p.urgency == "CRITICAL"


def test_score_increases_with_risk_signals():
    base = priority_score("DPD_8_30", 5000, 10)
    enriched = priority_score("DPD_8_30", 50000, 45, ptp_active=True, failed_debit=True)
    assert enriched > base
