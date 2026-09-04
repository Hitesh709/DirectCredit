from collections import Counter, defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd
router=APIRouter(prefix="/analytics",tags=["admin-analytics"])
def snapshot(db): return db.query(CustomerRecord).all(),db.query(LoanRecord).all(),db.query(RepaymentRecord).all()
@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 c,l,r=snapshot(db); dis=sum(float(x.disbursed_amount or 0) for x in l); out=sum(float(x.outstanding_amount or 0) for x in l); paid=sum(float(x.paid_amount or 0) for x in r); od=sum(max(0,float(x.due_amount or 0)-float(x.paid_amount or 0)) for x in r if calculate_dpd(x.due_date,x.paid_amount,x.due_amount)>0)
 return {"generated_at":datetime.utcnow().isoformat()+"Z","customers":len(c),"applications":len(l),"disbursed_amount":round(dis,2),"outstanding_amount":round(out,2),"paid_amount":round(paid,2),"overdue_amount":round(od,2),"active_loans":sum(x.status=="active" for x in l),"overdue_loans":sum(x.status=="overdue" for x in l),"repaid_loans":sum(x.status=="repaid" for x in l),"pending_applications":sum(x.status in {"draft","assessment"} for x in l)}
@router.get("/applications")
def applications(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=snapshot(db); c=Counter(x.status for x in l); return {"total":len(l),"by_status":dict(c),"recent":[{"loan_id":x.id,"customer_id":x.customer_id,"amount":x.requested_amount,"status":x.status,"stage":x.current_stage} for x in sorted(l,key=lambda z:z.id,reverse=True)[:100]]}
@router.get("/customers")
def customers(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 c,l,_=snapshot(db); by=Counter(x.customer_id for x in l); return {"total":len(c),"kyc_verified":sum(x.kyc_status=="verified" for x in c),"business_customers":sum(bool(x.business_name) for x in c),"with_loans":len(by),"repeat_borrowers":sum(v>1 for v in by.values())}
@router.get("/pipeline")
def pipeline(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=snapshot(db); return {"stages":[{"stage":k,"count":v} for k,v in sorted(Counter(x.current_stage for x in l).items())],"statuses":[{"status":k,"count":v} for k,v in sorted(Counter(x.status for x in l).items())]}
@router.get("/disbursements")
def disbursements(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=snapshot(db); return [{"loan_id":x.id,"customer_id":x.customer_id,"amount":x.disbursed_amount,"status":x.status} for x in l if x.disbursed_amount]
@router.get("/loan-slabs")
def loan_slabs(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=snapshot(db); return [{"amount":s,"applications":sum(round(float(x.sanctioned_amount or x.requested_amount or 0))==s for x in l),"disbursed":sum(round(float(x.sanctioned_amount or x.requested_amount or 0))==s and bool(x.disbursed_amount) for x in l)} for s in (5000,7500,10000,12500,15000)]
@router.get("/repayments")
def repayments(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,_,r=snapshot(db); buckets=Counter(); amounts=defaultdict(float)
 for x in r:
  d=calculate_dpd(x.due_date,x.paid_amount,x.due_amount); b="paid" if x.paid_amount>=x.due_amount else ("overdue" if d else "upcoming"); buckets[b]+=1; amounts[b]+=max(0,(x.due_amount or 0)-(x.paid_amount or 0))
 return [{"status":k,"count":buckets[k],"unpaid_amount":round(amounts[k],2)} for k in sorted(buckets)]
@router.get("/due-calendar")
def due_calendar(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,_,r=snapshot(db); out=defaultdict(lambda:{"count":0,"due":0.0,"paid":0.0})
 for x in r: a=out[str(x.due_date)[:10]]; a["count"]+=1; a["due"]+=x.due_amount or 0; a["paid"]+=x.paid_amount or 0
 return [{"date":k,**v,"unpaid":round(v["due"]-v["paid"],2)} for k,v in sorted(out.items())]
@router.get("/trends")
def trends(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=snapshot(db); out=defaultdict(lambda:{"applications":0,"disbursed":0.0})
 for x in l: k=str(x.created_at)[:7] if x.created_at else "unknown"; out[k]["applications"]+=1; out[k]["disbursed"]+=x.disbursed_amount or 0
 return [{"month":k,**v} for k,v in sorted(out.items())]
@router.get("/risk")
def risk(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 c,l,_=snapshot(db); s=[x.cibil_score for x in c if x.cibil_score and x.cibil_score>0]; return {"customers_with_bureau_score":len(s),"average_cibil":round(sum(s)/len(s),2) if s else None,"loan_status_counts":dict(Counter(x.status for x in l)),"scorecard_status":"official_125_point_scorecard_required"}
