"""Phase 2Y - Portfolio Risk Intelligence."""
PHASE2Y_VERSION="MBL-PORTFOLIO-RISK-2Y-v1"
def aggregate(loans:list[dict])->dict:
 n=len(loans or []); exposure=sum(float(x.get("outstanding_amount") or 0) for x in loans or [])
 overdue=sum(float(x.get("overdue_amount") or 0) for x in loans or [])
 dpd90=sum(1 for x in loans or [] if float(x.get("max_dpd") or 0)>=90)
 return {"version":PHASE2Y_VERSION,"loan_count":n,"outstanding_exposure":round(exposure,2),"overdue_amount":round(overdue,2),"overdue_rate_pct":round(overdue/exposure*100,2) if exposure else 0,"dpd90_plus_count":dpd90,"dpd90_plus_rate_pct":round(dpd90/n*100,2) if n else 0}
def contract(): return {"version":PHASE2Y_VERSION,"purpose":"Descriptive portfolio risk aggregation","outputs":["exposure","overdue","overdue rate","90+ DPD count/rate"],"rules":["Descriptive MIS only","No loan-level decision from aggregate metrics"]}