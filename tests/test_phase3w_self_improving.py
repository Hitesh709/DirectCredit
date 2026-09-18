from backend.phase3w_self_improving import improvement_cycle
def test_blocked(): assert improvement_cycle(observation="x",proposal="y")["deployment"]=="BLOCKED"
def test_eligible(): assert improvement_cycle(observation="x",proposal="y",test_result="PASS",approval="APPROVED")["deployment"]=="ELIGIBLE_FOR_DEPLOYMENT"
