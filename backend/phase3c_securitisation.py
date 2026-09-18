"""Phase 3C - Pool analytics."""
PHASE3C_VERSION="MBL-SECURITISATION-3C-v1"
def pool(loans):
 eligible=[x for x in loans or [] if str(x.get("status","")).lower() in {"active","disbursed"} and float(x.get("outstanding_amount") or 0)>0]
 return {"version":PHASE3C_VERSION,"loan_count":len(loans or []),"eligible_count":len(eligible),"eligible_outstanding":round(sum(float(x.get("outstanding_amount") or 0) for x in eligible),2)}
def contract(): return {"version":PHASE3C_VERSION,"purpose":"Securitisation/co-lending pool readiness","rules":["Eligibility is policy-driven","No ownership transfer or funding action"]}