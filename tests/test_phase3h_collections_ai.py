from backend.phase3h_collections_ai import recommend
def test_recommend(): assert recommend(dpd=95)['recommended_actions']==['MANUAL_ESCALATION']