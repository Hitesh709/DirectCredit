from backend.phase3o_repeat_borrower import profile
def test_profile(): assert profile(closed_loans=2,on_time_rate=1,max_dpd=0)["performance_evidence"] is True
