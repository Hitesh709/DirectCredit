from backend.phase3v_autonomous_operations import plan
def test_plan(): assert "fund_transfer" in plan([])["approval_required_for"]
