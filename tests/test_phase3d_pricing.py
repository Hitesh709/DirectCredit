from backend.phase3d_pricing import profitability
def test_profit(): assert profitability(principal=1000,annual_rate=20,expected_loss=50,funding_cost=50,operating_cost=50)['contribution']==50