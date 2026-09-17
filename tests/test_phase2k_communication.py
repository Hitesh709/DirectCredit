from backend.phase2k_communication import PHASE2K_VERSION, communication_plan, communication_contract

def test_contract_version():
    assert communication_contract()["version"] == PHASE2K_VERSION

def test_due_today_plan():
    p=communication_plan("DUE_TODAY",0,{"sms":True,"whatsapp":False,"email":True})
    assert p.template == "emi_due_today"
    assert p.channels == ("sms","email")

def test_failed_debit_plan():
    p=communication_plan("DEBIT_FAILED",7,{"sms":True,"whatsapp":True,"email":False})
    assert p.template == "auto_debit_failed"

def test_dpd_90_escalation():
    p=communication_plan("DPD",95,{"sms":True,"whatsapp":True,"email":True})
    assert p.template == "dpd_90"
    assert p.reason == "dpd_90_plus_escalation"

def test_ptp_overrides_dpd_template():
    p=communication_plan("DPD",15,{"sms":True},ptp_active=True)
    assert p.template == "dpd_ptp_follow_up"
