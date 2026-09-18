"""Phase 3E - Dynamic policy engine."""
PHASE3E_VERSION="MBL-DYNAMIC-POLICY-3E-v1"
def evaluate_rules(facts,rules):
 matched=[]
 for r in rules or []:
  actual=facts.get(r.get("field")); value=r.get("value"); op=r.get("operator","equals")
  try:
   ok=actual==value if op=="equals" else float(actual)>=float(value) if op=="gte" and actual is not None else float(actual)>float(value) if op=="gt" and actual is not None else actual in value if op=="in" and isinstance(value,list) else False
  except (TypeError,ValueError): ok=False
  if ok: matched.append({"rule_id":r.get("rule_id"),"action":r.get("action")})
 return {"version":PHASE3E_VERSION,"matched_rules":matched,"rule_count":len(rules or [])}
def contract(): return {"version":PHASE3E_VERSION,"purpose":"Versioned configurable policy evaluation","rules":["Rules are explicit and auditable","Unknown facts are not positive evidence","Policy changes require authorization"]}