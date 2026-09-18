from backend.phase3r_observability import health
def test_health(): assert health(error_rate=6)["status"]=="ALERT"
