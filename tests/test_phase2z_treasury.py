from backend.phase2z_treasury import liquidity
def test_liquidity(): assert liquidity(cash=100,expected_disbursements=150,expected_collections=20)['liquidity_gap']==30