from collections import defaultdict, Counter
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord, CollectionAgentRecord, CollectionActionRecord
from .analytics_routes import router as analytics_router
from .report_routes import router as report_router
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd

router = APIRouter(prefix="/api/admin", tags=["reporting"])
router.include_router(analytics_router)
router.include_router(report_router)

def loan_state(loan, repayment_rows):
    if any(r.status == "overdue" and (r.paid_amount or 0) < (r.due_amount or 0) for r in repayment_rows): return "overdue"
    if (loan.outstanding_amount or 0) <= 0 and (loan.disbursed_amount or 0) > 0: return "repaid"
    if (loan.disbursed_amount or 0) > 0 or loan.status in {"disbursed", "repayment", "active"}: return "active"
    if loan.status in {"rejected", "dropped", "cancelled"}: return "rejected"
    return "pending"

def money(v): return round(float(v or 0), 2)

def _report_data(db):
    customers = db.query(CustomerRecord).all()
    loans = db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()
    repayments = db.query(RepaymentRecord).all()
    documents = db.query(DocumentRecord).all()
    by = defaultdict(list)
    for r in repayments: by[r.loan_id].append(r)
    states = {l.id: loan_state(l, by[l.id]) for l in loans}
    return customers, loans, repayments, documents, by, states

def _collection_rows(customers, loans, by, states):
    names={c.id:c.name for c in customers}; banks={c.id:c.primary_bank for c in customers}
    rows=[]
    for loan in loans:
        rs=by[loan.id]
        overdue=money(sum(max(0,(r.due_amount or 0)-(r.paid_amount or 0)) for r in rs if calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0))
        outstanding=money(loan.outstanding_amount or sum(max(0,(r.due_amount or 0)-(r.paid_amount or 0)) for r in rs))
        if outstanding<=0 and overdue<=0 and not loan.disbursed_amount: continue
        rows.append({"loan_id":loan.id,"customer_id":loan.customer_id,"name":names.get(loan.customer_id,"Customer"),"loan_amount":money(loan.sanctioned_amount or loan.requested_amount),"outstanding":outstanding,"overdue":overdue,"status":states[loan.id],"mandate":"Active" if loan.status=="mandate_active" else "Not connected","bank":banks.get(loan.customer_id)})
    return rows

@router.get("/reporting")
def reporting(db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    customers, loans, repayments, documents, by, states = _report_data(db)
    monthly=defaultdict(lambda:{"applications":0,"disbursed_count":0,"disbursed_amount":0.0})
    for l in loans:
        key=str(l.created_at)[:7] if l.created_at else "unknown"
        monthly[key]["applications"]+=1
        if l.disbursed_amount:
            monthly[key]["disbursed_count"]+=1; monthly[key]["disbursed_amount"]+=float(l.disbursed_amount or 0)
    monthly_rows=[{"month":k,**{n:money(v) if n=="disbursed_amount" else v for n,v in val.items()}} for k,val in sorted(monthly.items())]
    slabs=[]
    for slab in (5000,7500,10000,12500,15000):
        selected=[l for l in loans if round(float(l.sanctioned_amount or l.requested_amount or 0))==slab]
        slabs.append({"amount":slab,"total_count":len(selected),"active_count":sum(states[l.id]=="active" for l in selected),"overdue_count":sum(states[l.id]=="overdue" for l in selected),"repaid_count":sum(states[l.id]=="repaid" for l in selected),"active_amount":money(sum(l.outstanding_amount or 0 for l in selected if states[l.id]=="active")),"overdue_amount":money(sum(l.outstanding_amount or 0 for l in selected if states[l.id]=="overdue"))})
    repayment_status=defaultdict(lambda:{"count":0,"due":0.0,"paid":0.0,"unpaid":0.0})
    for r in repayments:
        dpd=calculate_dpd(r.due_date,r.paid_amount,r.due_amount); paid=money(r.paid_amount); due=money(r.due_amount); unpaid=money(max(0,due-paid))
        key="On-Time / Paid" if paid>=due else "Overdue DPD 1–30" if dpd<=30 and dpd>0 else "Overdue DPD 31–60" if dpd<=60 else "Overdue DPD 61–90" if dpd<=90 else "NPA DPD 90+" if dpd>90 else "Upcoming"
        x=repayment_status[key];x["count"]+=1;x["due"]+=due;x["paid"]+=paid;x["unpaid"]+=unpaid
    repayment_status={k:{**v,"due":money(v["due"]),"paid":money(v["paid"]),"unpaid":money(v["unpaid"])} for k,v in repayment_status.items()}
    due=defaultdict(lambda:{"count":0,"due":0.0,"paid":0.0})
    for r in repayments:
        x=due[str(r.due_date)[:10]];x["count"]+=1;x["due"]+=r.due_amount or 0;x["paid"]+=r.paid_amount or 0
    due_calendar=[{"date":k,"count":v["count"],"due":money(v["due"]),"paid":money(v["paid"])} for k,v in sorted(due.items())]
    states_count=Counter(states.values()); collection=_collection_rows(customers,loans,by,states)
    agents=db.query(CollectionAgentRecord).all(); actions=db.query(CollectionActionRecord).all()
    agent_perf=[]
    for a in agents:
        aa=[x for x in actions if x.agent_id==a.id]; rr=[x for x in aa if x.action_type=="receipt" and x.status=="posted"]
        agent_perf.append({"agent_id":a.id,"agent_code":a.agent_code,"name":a.name,"actions":len(aa),"receipts":len(rr),"collected_amount":money(sum(x.amount or 0 for x in rr))})
    agent_perf.sort(key=lambda x:(-x["collected_amount"],x["agent_id"]))
    return {
        "generated_at": datetime.utcnow().isoformat()+"Z", "customers": {"total":len(customers),"active":sum(c.kyc_status!="closed" for c in customers),"incomplete":sum(c.kyc_status!="verified" for c in customers),"kyc_verified":sum(c.kyc_status=="verified" for c in customers)},
        "applications":len(loans), "unique_users":len({l.customer_id for l in loans}), "repeat_users":sum(v>1 for v in Counter(l.customer_id for l in loans).values()),
        "pending":states_count["pending"], "rejected":states_count["rejected"], "disbursed_count":sum(bool(l.disbursed_amount) for l in loans),"active_loans":states_count["active"],"overdue_loans":states_count["overdue"],"repaid_loans":states_count["repaid"],
        "amounts":{"disbursed":money(sum(l.disbursed_amount or 0 for l in loans)),"outstanding":money(sum(l.outstanding_amount or 0 for l in loans if states[l.id] in {"active","overdue"})),"overdue":money(sum(max((r.due_amount or 0)-(r.paid_amount or 0),0) for r in repayments if calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0)),"due":money(sum(r.due_amount or 0 for r in repayments)),"paid":money(sum(r.paid_amount or 0 for r in repayments)),"unpaid":money(sum(max((r.due_amount or 0)-(r.paid_amount or 0),0) for r in repayments))},
        "documents":len(documents),"repayments":len(repayments),"recent_loans":[{"id":l.id,"customer_id":l.customer_id,"amount":money(l.sanctioned_amount or l.requested_amount),"status":states[l.id],"created_at":str(l.created_at) if l.created_at else None} for l in loans[:20]],
        "monthly":monthly_rows,"slabs":slabs,"repayment_status":repayment_status,"due_calendar":due_calendar,"collection":collection,"collection_agent_performance":agent_perf
    }
