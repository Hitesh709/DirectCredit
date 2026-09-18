from backend.phase3a_funding import funding_capacity
def test_capacity(): assert funding_capacity(cash=100,committed_funding=200,reserved=50)['available_capacity']==250