from backend.phase2t_risk import calculate_risk, risk_contract

def test_contract_version():
    assert risk_contract()["version"] == "MBL-CREDIT-RISK-2T-v1"

def test_high_score_is_low_risk_grade():
    r = calculate_risk(scorecard_score=110, scorecard_max=125, cibil_score=750, business_vintage_years=5)
    assert r["risk_grade"] == "A"
    assert r["model_status"] == "CALIBRATION_REQUIRED"

def test_stress_signals_reduce_grade():
    r = calculate_risk(scorecard_score=100, cibil_score=620, foir=.70, bank_bounces_3m=2, active_dpd=True, fraud_score=65)
    assert r["risk_grade"] in {"D", "E"}
    assert "active_dpd" in r["reasons"]

def test_expected_loss_formula():
    r = calculate_risk(scorecard_score=100, pd_override=.10, lgd_override=.50, ead_override=100000)
    assert r["expected_loss"] == 5000.0
    assert r["model_status"] == "PARAMETERS_SUPPLIED"
