from backend.phase3i_operations_ai import prioritize
def test_prioritize(): assert prioritize(items=[{'priority_score':1},{'priority_score':9}])['queue'][0]['priority_score']==9