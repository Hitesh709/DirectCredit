from collections import Counter, defaultdict
from datetime import date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd

router=APIRouter(prefix="/api/admin/analytics",tags=["admin-analytics"])

def snapshot(db):
    customers=db.query(CustomerRecord).all(); loans=db.query(LoanRecord).all(); repayments=db.query(RepaymentRecord).all()
    return customers,loans,repayments

@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    c,l,r=snapshot(db); dis=sum(float(x.disbursed_amount or 0) for x in l); out=sum(float(x.outstanding_amount or 0) for x in l); paid=sum(float(x.paid_amount or 0) for x in r); overdue=sum(max(0,float(x.due_amount or 0)-float(x.paid_amount or 0)) for x in r if calculate_dpd(x.due_date,x.paid_amount,x.due_amount)>0)
    return {"generated_at":datetime.utcnow().isoformat()+"Z","customers":len(c),"applications":len(l),"disbursed_amount":round(dis,2),"outstanding_amount":round(out,2),"paid_amount":round(paid,2),"overdue_amount":round(overdue,2),"active_loans":sum(x.status=="active" for x in l),"overdue_loans":sum(x.status=="overdue" for x in l),"repaid_loans":sum(x.status=="repaid" for x in l),"pending_applications":sum(x.status in {"draft","assessment"} for x in l)}

@router.get("/applications")
def applications(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,loans,_=snapshot(db); counts=Counter(x.status for x in loans); return {"total":len(loans),"by_status":dict(counts),"recent":[{"loan_id":x.id,"customer_id":x.customer_id,"amount":x.requested_amount,"status":x.status,"stage":x.current_stage} for x in sorted(loans,key=lambda z:z.id,reverse=True)[:100]]}

@router.get("/customers")
def customer_analytics(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    customers,loans,_=snapshot(db); by=Counter(x.customer_id for x in loans); return {"total":len(customers),"kyc_verified":sum(x.kyc_status=="verified" for x in customers),"business_customers":sum(bool(x.business_name) for x in customers),"with_loans":sum(v>0 for v in by.values()),"repeat_borrowers":sum(v>1 for v in by.values())}

@router.get("/pipeline")
def pipeline(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,loans,_=snapshot(db); stages=Counter(x.current_stage for x in loans); return {"stages":[{"stage":k,"count":v} for k,v in sorted(stages.items())],"statuses":[{"status":k,"count":v} for k,v in sorted(Counter(x.status for x in loans).items())]}

@router.get("/disbursements")
def disbursement_matrix(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,loans,_=snapshot(db); buckets=defaultdict(lambda:{"count":0,"amount":0.0})
    for x in loans:
        if float(x.disbursed_amount or 0)>0: b=str(int(x.disbursed_amount)); buckets[b]["count"]+=1; buckets[b]["amount"]+=x.disbursed_amount or 0
    return [{"slab":k,"count":v["count"],"amount":round(v["amount"],2)} for k,v in sorted(buckets.items(),key=lambda z:float(z[0]))]

@router.get("/loan-slabs")
def loan_slabs(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,loans,_=snapshot(db); slabs=[5000,7500,10000,12500,15000]; out=[]
    for s in slabs:
        rows=[x for x in loans if round(float(x.sanctioned_amount or x.requested_amount or 0))==s]; out.append({"amount":s,"applications":len(rows),"sanctioned":sum(1 for x in rows if x.sanctioned_amount),"disbursed":sum(1 for x in rows if x.disbursed_amount),"outstanding":round(sum(x.outstanding_amount or 0 for x in rows),2)})
    return out

@router.get("/repayments")
def repayment_matrix(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,_,rows=snapshot(db); counts=Counter(); amounts=defaultdict(float)
    for r in rows:
        d=calculate_dpd(r.due_date,r.paid_amount,r.due_amount); bucket="paid" if d==0 and r.paid_amount>=r.due_amount else ("overdue" if d>0 else "upcoming"); counts[bucket]+=1; amounts[bucket]+=max(0,float(r.due_amount or 0)-float(r.paid_amount or 0))
    return {"buckets":[{"status":k,"count":counts[k],"unpaid_amount":round(amounts[k],2)} for k in sorted(counts)]}

@router.get("/due-calendar")
def due_calendar(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,_,rows=snapshot(db); out=defaultdict(lambda:{"count":0,"due":0.0,"paid":0.0})
    for r in rows: x=out[str(r.due_date)[:10]]; x["count"]+=1; x["due"]+=r.due_amount or 0; x["paid"]+=r.paid_amount or 0
    return [{"date":k,"count":v["count"],"due":round(v["due"],2),"paid":round(v["paid"],2),"unpaid":round(v["due"]-v["paid"],2)} for k,v in sorted(out.items())]

@router.get("/trends")
def trends(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    _,loans,_=snapshot(db); out=defaultdict(lambda:{"applications":0,"disbursed":0.0})
    for x in loans:
        key=str(x.created_at)[:7] if x.created_at else "unknown"; out[key]["applications"]+=1; out[key]["disbursed"]+=x.disbursed_amount or 0
    return [{"month":k,"applications":v["applications"],"disbursed":round(v["disbursed"],2)} for k,v in sorted(out.items())]

@router.get("/risk")
def risk_analytics(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    customers,loans,_=snapshot(db); scores=[x.cibil_score for x in customers if x.cibil_score and x.cibil_score>0]; return {"customers_with_bureau_score":len(scores),"average_cibil":round(sum(scores)/len(scores),2) if scores else None,"loan_status_counts":dict(Counter(x.status for x in loans)),"scorecard_status":"official_125_point_scorecard_required"}
