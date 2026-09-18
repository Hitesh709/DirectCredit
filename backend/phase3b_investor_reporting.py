"""Phase 3B - Investor reporting."""
PHASE3B_VERSION="MBL-INVESTOR-REPORTING-3B-v1"
def report(loan_count=0,outstanding=0,overdue=0,collections=0,expected_loss=0):
 e=float(outstanding or 0); o=float(overdue or 0)
 return {"version":PHASE3B_VERSION,"loan_count":int(loan_count or 0),"outstanding":e,"overdue":o,"collections":float(collections or 0),"expected_loss":float(expected_loss or 0),"overdue_rate_pct":round(o/e*100,2) if e else 0}
def contract(): return {"version":PHASE3B_VERSION,"purpose":"Traceable investor/lender portfolio reporting","rules":["No fabricated performance","Source metrics must be traceable"]}