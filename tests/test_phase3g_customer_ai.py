from backend.phase3g_customer_ai import response
def test_ai(): assert 'credit_decision' in response('status')['requires_human_for']