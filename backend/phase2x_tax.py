"""Phase 2X - GST / Tax Intelligence."""
PHASE2X_VERSION="MBL-TAX-2X-v1"
def reconcile_tax(*,gst_monthly_turnover:float=0, itr_income:float=0, bank_monthly_credits:float=0, gst_filing_status:str="unknown", months:int=0)->dict:
 g=float(gst_monthly_turnover or 0); b=float(bank_monthly_credits or 0)
 gap=round(b-g,2); ratio=round(b/g,3) if g else None
 return {"version":PHASE2X_VERSION,"gst_monthly_turnover":g,"itr_income":float(itr_income or 0),"bank_monthly_credits":b,"bank_vs_gst_gap":gap,"bank_to_gst_ratio":ratio,"gst_filing_status":gst_filing_status,"months":int(months or 0),"review_required": (g>0 and abs(gap)>max(10000,g*.30))}
def contract(): return {"version":PHASE2X_VERSION,"purpose":"GST, tax and declared-vs-observed financial reconciliation","rules":["Tax reconciliation is evidence analytics, not a tax/legal conclusion","Material variance requires review","Source provenance must be retained"]}