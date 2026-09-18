from backend.phase2u_underwriting import underwriting_summary,contract
def test_contract(): assert contract()['version']=='MBL-AI-UNDERWRITING-2U-v1'
def test_flags(): assert underwriting_summary(customer={},loan={},risk={'risk_grade':'D'})['human_review_required']