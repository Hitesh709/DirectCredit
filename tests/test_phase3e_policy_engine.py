from backend.phase3e_policy_engine import evaluate_rules
def test_policy(): assert evaluate_rules({'x':5},[{'rule_id':'r1','field':'x','operator':'gte','value':5,'action':'REVIEW'}])['matched_rules']