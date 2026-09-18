"""Phase 3A - Funding capacity."""
PHASE3A_VERSION="MBL-FUNDING-3A-v1"
def funding_capacity(cash=0,committed_funding=0,undrawn_funding=0,reserved=0):
 total=float(cash or 0)+float(committed_funding or 0)+float(undrawn_funding or 0)
 return {"version":PHASE3A_VERSION,"funding_capacity":round(total,2),"available_capacity":round(max(0,total-float(reserved or 0)),2)}
def contract(): return {"version":PHASE3A_VERSION,"purpose":"Funding facilities and capacity","rules":["Funding availability must be evidenced","No automatic borrowing or drawdown"]}