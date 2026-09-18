from backend.phase3t_internal_audit import finding
def test_finding(): assert finding("KYC","FAIL")["remediation_required"] is True
