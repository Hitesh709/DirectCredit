"""Phase 3H - Collections AI assistive strategy."""
PHASE3H_VERSION="MBL-COLLECTIONS-AI-3H-v1"
def recommend(*,dpd=0,overdue_amount=0,ptp_active=False,failed_debit=False):
 actions=[]; d=int(dpd or 0)
 if d>=90: actions.append("MANUAL_ESCALATION")
 elif failed_debit: actions.append("AUTO_DEBIT_REVIEW")
 elif ptp_active: actions.append("PTP_FOLLOW_UP")
 elif d>0: actions.append("CUSTOMER_CONTACT")
 else: actions.append("DUE_REMINDER")
 return {"version":PHASE3H_VERSION,"dpd":d,"overdue_amount":float(overdue_amount or 0),"recommended_actions":actions,"human_review_required":d>=90,"mode":"ASSISTIVE"}
def contract(): return {"version":PHASE3H_VERSION,"purpose":"Explainable collections strategy assistance","rules":["AI recommends actions; authorized collections policy remains authoritative","No harassment or uncontrolled contact","AI does not post payments or approve waivers"]}