"""Phase 3O - Repeat borrower intelligence."""
PHASE3O_VERSION="MBL-REPEAT-BORROWER-3O-v1"
def profile(*,closed_loans=0,on_time_rate=0,max_dpd=0): return {"version":PHASE3O_VERSION,"closed_loans":int(closed_loans),"on_time_rate":float(on_time_rate),"max_dpd":int(max_dpd),"performance_evidence":bool(closed_loans and on_time_rate>=0)}
def contract(): return {"version":PHASE3O_VERSION,"purpose":"Repeat-borrower performance profile","rules":["Historical performance is evidence, not automatic approval","Current eligibility must be reassessed"]}