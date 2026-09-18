from backend.phase3b_investor_reporting import report
def test_report(): assert report(outstanding=1000,overdue=100)['overdue_rate_pct']==10