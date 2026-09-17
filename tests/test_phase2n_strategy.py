from backend.phase2n_strategy import allocation_score, build_allocation, strategy_contract

def test_contract_version():
    assert strategy_contract()["version"] == "MBL-COLLECTIONS-2N-v1"

def test_high_dpd_manual_escalation():
    d=build_allocation(loan_id=1,bucket="DPD_90_PLUS",overdue_amount=60000,max_dpd=95,agents=[],active_ptp=False,mandate_active=True,failed_debit=False)
    assert d.strategy == "MANUAL_ESCALATION"
    assert d.sla_hours == 4

def test_ptp_strategy_precedes_auto_debit():
    d=build_allocation(loan_id=2,bucket="DPD_8_30",overdue_amount=12000,max_dpd=10,agents=[],active_ptp=True,mandate_active=True,failed_debit=False)
    assert d.strategy == "PTP_FOLLOW_UP"

def test_capacity_balancing_is_deterministic():
    agents=[{"agent_id":"A","capacity":0.9},{"agent_id":"B","capacity":0.2}]
    d=build_allocation(loan_id=3,bucket="DPD_31_60",overdue_amount=30000,max_dpd=40,agents=agents)
    assert d.agent_id == "B"

def test_score_is_bounded():
    assert 0 <= allocation_score(bucket="DPD_90_PLUS",overdue_amount=999999,max_dpd=999,skill_match=99,geography_match=99) <= 100
