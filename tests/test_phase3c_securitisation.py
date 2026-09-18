from backend.phase3c_securitisation import pool
def test_pool(): assert pool([{'status':'active','outstanding_amount':100}])['eligible_count']==1