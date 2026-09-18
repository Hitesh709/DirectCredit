from backend.phase2y_portfolio_risk import aggregate
def test_portfolio(): assert aggregate([{'outstanding_amount':1000,'overdue_amount':100,'max_dpd':95}])['dpd90_plus_count']==1