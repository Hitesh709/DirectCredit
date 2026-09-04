from backend.mbl_scorecard import calculate, MAX_POINTS, VERSION

def complete_inputs():
    return {
        "ownership_proof":"applicant","business_owned":True,"residence_owned":True,
        "business_geography":"tier1","age":35,"cibil_unsecured_enquiries_30d":1,
        "cibil_repayment":"none","unsecured_loans_50k_plus":3,
        "avg_monthly_bank_credits":500000,"bank_bounces_3m":0,"aqb":15000,"ecs_returns_12m":0,
        "business_type":"trader","business_vintage_years":4,"business_stock":500000,
        "monthly_emi_obligation":20000,"foir":0.30,"trade_validations":6,"gst_years":4,
        "gstr3b_avg_monthly_turnover":500000,"itr_income":500000,"mobile_stability_years":6,
    }

def test_official_scorecard_maximum_is_125():
    result=calculate(complete_inputs())
    assert result.score == MAX_POINTS == 125
    assert result.version == VERSION
    assert result.decision == "APPROVE"
    assert result.approval_percent == 100

def test_approval_matrix():
    data=complete_inputs()
    data["age"]=21
    data["avg_monthly_bank_credits"]=100000
    data["aqb"]=5000
    data["unsecured_loans_50k_plus"]=0
    result=calculate(data)
    assert result.score < 105
    assert result.decision in {"APPROVE","MANUAL_REVIEW","REJECT"}

def test_hard_reject_overrides_score():
    data=complete_inputs(); data["bank_bounces_3m"]=2
    result=calculate(data)
    assert result.decision == "REJECT"
    assert "bank_bounces_2_plus" in result.hard_rejects
