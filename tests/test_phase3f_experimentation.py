from backend.phase3f_experimentation import assign
def test_assignment(): assert assign('x',1,['A','B'])['status']=='ASSIGNED'