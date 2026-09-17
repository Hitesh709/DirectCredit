from backend.phase2s_fraud import evaluate_fraud, fraud_contract

def test_contract_version():
    assert fraud_contract()["version"] == "MBL-FRAUD-2S-v1"

def test_clean_case():
    r = evaluate_fraud()
    assert r["status"] == "CLEAR"
    assert r["fraud_score"] == 0

def test_velocity_creates_review():
    r = evaluate_fraud(application_count_24h=3)
    assert r["status"] == "REVIEW"
    assert "APPLICATION_VELOCITY_24H" in r["high_severity_signals"] or r["fraud_score"] == 12

def test_identity_mismatch_high_risk():
    r = evaluate_fraud(identity_match="mismatch")
    assert r["status"] == "HIGH_RISK"
    assert "IDENTITY_MISMATCH" in r["high_severity_signals"]

def test_external_signal_is_capped():
    r = evaluate_fraud(external_signals=[{"code":"TEST","severity":"HIGH","points":100}])
    assert r["fraud_score"] == 40
