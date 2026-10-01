from collections import defaultdict, Counter
from datetime import datetime
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session, load_only
from sqlalchemy import func
import os
import time
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord, CollectionAgentRecord, CollectionActionRecord, BankTransactionRecord, CustomerJourneyRecord
from .analytics_routes import router as analytics_router
from .report_routes import router as report_router
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd
import json
import threading

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
    customers = db.query(CustomerRecord).options(load_only(
        CustomerRecord.id, CustomerRecord.customer_code, CustomerRecord.name,
        CustomerRecord.mobile, CustomerRecord.email, CustomerRecord.business_name,
        CustomerRecord.kyc_status, CustomerRecord.current_city, CustomerRecord.primary_bank
    )).all()
    loans = db.query(LoanRecord).options(load_only(
        LoanRecord.id, LoanRecord.customer_id, LoanRecord.requested_amount,
        LoanRecord.eligible_amount, LoanRecord.monthly_emi, LoanRecord.sanctioned_amount,
        LoanRecord.disbursed_amount, LoanRecord.outstanding_amount, LoanRecord.interest_rate,
        LoanRecord.tenure_months, LoanRecord.status, LoanRecord.current_stage,
        LoanRecord.product, LoanRecord.scorecard_score, LoanRecord.scorecard_decision,
        LoanRecord.scorecard_approval_percent, LoanRecord.scorecard_hard_rejects,
        LoanRecord.created_at
    )).order_by(LoanRecord.id.desc()).all()
    repayments = db.query(RepaymentRecord).options(load_only(
        RepaymentRecord.id, RepaymentRecord.loan_id, RepaymentRecord.installment,
        RepaymentRecord.due_date, RepaymentRecord.due_amount, RepaymentRecord.paid_amount,
        RepaymentRecord.status
    )).all()
    documents_count = db.query(func.count(DocumentRecord.id)).scalar() or 0
    transactions = db.query(BankTransactionRecord).options(load_only(
        BankTransactionRecord.transaction_date, BankTransactionRecord.amount,
        BankTransactionRecord.direction, BankTransactionRecord.category,
        BankTransactionRecord.balance
    )).all()
    by = defaultdict(list)
    for r in repayments: by[r.loan_id].append(r)
    states = {l.id: loan_state(l, by[l.id]) for l in loans}
    return customers, loans, repayments, documents_count, transactions, by, states

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

def _bank_matrix(transactions):
    monthly=defaultdict(lambda:{"credits":0.0,"debits":0.0,"transactions":0,"average_balance":None,"closing_balance":None})
    balances=defaultdict(list); categories=Counter()
    for t in transactions:
        month=str(t.transaction_date or "")[:7] or "unknown"
        row=monthly[month]; row["transactions"]+=1
        amount=money(t.amount)
        if str(t.direction).lower()=="credit": row["credits"]+=amount
        elif str(t.direction).lower()=="debit": row["debits"]+=amount
        if t.balance is not None:
            row["closing_balance"]=money(t.balance); balances[month].append(float(t.balance))
        if t.category: categories[t.category]+=1
    for month,row in monthly.items():
        vals=balances.get(month,[]); row["average_balance"]=money(sum(vals)/len(vals)) if vals else None
        row["credits"]=money(row["credits"]); row["debits"]=money(row["debits"])
    return monthly, categories

_REPORT_CACHE = {"at": 0.0, "data": None}
_REPORT_CACHE_TTL = max(0.0, float(os.getenv("ADMIN_REPORT_CACHE_TTL_SECONDS", "60")))
_REPORT_CACHE_LOCK = threading.Lock()

@router.get("/reporting")
def reporting(response: Response, db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    now = time.monotonic()
    cached = _REPORT_CACHE["data"]
    if cached is not None and now - _REPORT_CACHE["at"] < _REPORT_CACHE_TTL:
        response.headers["Cache-Control"] = "private, max-age=30, stale-while-revalidate=30"
        response.headers["X-Reporting-Cache"] = "HIT"
        return cached

    # Single-flight cache refresh: concurrent admin tabs must not all execute
    # the same expensive reporting queries when the cache expires.
    with _REPORT_CACHE_LOCK:
        now = time.monotonic()
        cached = _REPORT_CACHE["data"]
        if cached is not None and now - _REPORT_CACHE["at"] < _REPORT_CACHE_TTL:
            response.headers["Cache-Control"] = "private, max-age=30, stale-while-revalidate=30"
            response.headers["X-Reporting-Cache"] = "HIT-AFTER-WAIT"
            return cached
        customers, loans, repayments, documents, transactions, by, states = _report_data(db)
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
    due_calendar=[{"date":k,"count":v["count"],"due":money(v["due"]),"paid":money(v["paid"]),"unpaid":money(v["due"]-v["paid"])} for k,v in sorted(due.items())]
    states_count=Counter(states.values())
    today=datetime.utcnow().date()
    upcoming_lms=sum(1 for r in repayments if r.due_date and str(r.due_date)[:10] > today.isoformat() and money(r.due_amount)>money(r.paid_amount))
    due_today_lms=sum(1 for r in repayments if r.due_date and str(r.due_date)[:10] == today.isoformat() and money(r.due_amount)>money(r.paid_amount))

    # Journey-based funnel stages are optional: older/live databases may not have
    # journey records for every application. When present, expose the real stage
    # counts; the UI falls back to portfolio metrics when a stage is unavailable.
    # Only fetch journey rows that can contribute to the four funnel stages.
    # This avoids materializing unrelated journey events on every cache refresh.
    journey_keys=sorted({
        "approval","approval_stage","approvalstage","credit_approval",
        "esign","e_sign","e-sign","esignature","e_signature",
        "emandate","e_mandate","e-mandate","mandate","e_mandate_setup",
        "disbursement","disbursal","disbursed"
    })
    journey_rows=db.query(CustomerJourneyRecord).options(load_only(
        CustomerJourneyRecord.customer_id, CustomerJourneyRecord.step_key,
        CustomerJourneyRecord.step_label, CustomerJourneyRecord.status
    )).filter(
        func.lower(CustomerJourneyRecord.step_key).in_([x.lower() for x in journey_keys])
    ).all()
    journey_stage_aliases={
        "approval": {"approval","approval_stage","approvalstage","credit_approval"},
        "e_sign": {"esign","e_sign","e-sign","esignature","e_signature"},
        "e_mandate": {"emandate","e_mandate","e-mandate","mandate","e_mandate_setup"},
        "disbursement": {"disbursement","disbursal","disbursed"}
    }
    journey_funnel={}
    alias_to_stage={alias:stage for stage,aliases in journey_stage_aliases.items() for alias in aliases}
    journey_by_stage=defaultdict(list)
    for row in journey_rows:
        key=str(row.step_key or "").strip().lower().replace(" ","_")
        label=str(row.step_label or "").strip().lower().replace(" ","_")
        stage=alias_to_stage.get(key) or alias_to_stage.get(label)
        if stage: journey_by_stage[stage].append(row)
    for stage in journey_stage_aliases:
        rows=journey_by_stage.get(stage,[])
        if rows:
            unique_ids={x.customer_id for x in rows if x.customer_id is not None}
            repeat_counts=Counter(x.customer_id for x in rows if x.customer_id is not None)
            completed=sum(str(x.status or "").lower() in {"completed","complete","done","success","successful"} for x in rows)
            dropped=sum(str(x.status or "").lower() in {"dropped","rejected","failed","cancelled"} for x in rows)
            pending=max(len(rows)-completed-dropped,0)
            journey_funnel[stage]={"applications":len(rows),"unique_users":len(unique_ids),"repeat_users":sum(max(v-1,0) for v in repeat_counts.values()),"completed":completed,"pending":pending,"dropped":dropped}
    collection=_collection_rows(customers,loans,by,states)
    agents=db.query(CollectionAgentRecord).options(load_only(
        CollectionAgentRecord.id, CollectionAgentRecord.agent_code,
        CollectionAgentRecord.name, CollectionAgentRecord.active
    )).all()

    # Aggregate collection actions in SQL instead of loading every action row
    # into Python. The reporting response only needs per-agent totals.
    action_agg=db.query(
        CollectionActionRecord.agent_id,
        CollectionActionRecord.action_type,
        CollectionActionRecord.status,
        func.count(CollectionActionRecord.id).label("action_count"),
        func.coalesce(func.sum(CollectionActionRecord.amount),0).label("amount_sum")
    ).group_by(
        CollectionActionRecord.agent_id,
        CollectionActionRecord.action_type,
        CollectionActionRecord.status
    ).all()
    action_totals=defaultdict(lambda:{"actions":0,"receipts":0,"collected_amount":0.0,"debit_requests":0,"pending_debit_requests":0})
    for row in action_agg:
        x=action_totals[row.agent_id]
        count=int(row.action_count or 0)
        x["actions"]+=count
        if row.action_type=="receipt" and row.status=="posted":
            x["receipts"]+=count
            x["collected_amount"]+=float(row.amount_sum or 0)
        if row.action_type=="debit_request":
            x["debit_requests"]+=count
            if row.status=="pending_provider":
                x["pending_debit_requests"]+=count
    agent_perf=[]
    for a in agents:
        x=action_totals[a.id]
        agent_perf.append({"agent_id":a.id,"agent_code":a.agent_code,"name":a.name,"active":bool(a.active),"actions":x["actions"],"receipts":x["receipts"],"collected_amount":money(x["collected_amount"]),"debit_requests":x["debit_requests"],"pending_debit_requests":x["pending_debit_requests"]})
    agent_perf.sort(key=lambda x:(-x["collected_amount"],x["agent_id"]))

    bank_monthly, bank_categories = _bank_matrix(transactions)
    risk_loans=[l for l in loans if l.scorecard_score is not None]
    decisions=Counter(l.scorecard_decision or "NOT_ASSESSED" for l in risk_loans)
    risk_scores=[float(l.scorecard_score) for l in risk_loans]
    risk_summary={"assessed_loans":len(risk_loans),"average_score":money(sum(risk_scores)/len(risk_scores)) if risk_scores else None,"max_score":125,"decisions":dict(decisions),"approval_80_90_100":{"80":sum(l.scorecard_approval_percent==80 for l in risk_loans),"90":sum(l.scorecard_approval_percent==90 for l in risk_loans),"100":sum(l.scorecard_approval_percent==100 for l in risk_loans)},"hard_reject_count":sum(bool(l.scorecard_hard_rejects and l.scorecard_hard_rejects not in ('[]','{}')) for l in risk_loans)}
    bank_summary={"transactions":len(transactions),"credits":money(sum(t.amount or 0 for t in transactions if str(t.direction).lower()=="credit")),"debits":money(sum(t.amount or 0 for t in transactions if str(t.direction).lower()=="debit")),"negative_balance_events":sum(t.balance is not None and float(t.balance)<0 for t in transactions),"monthly":[{"month":m,**v} for m,v in sorted(bank_monthly.items())],"top_categories":[{"category":k,"count":v} for k,v in bank_categories.most_common(10)]}
    loan_trend=[{"month":m,"applications":v["applications"],"disbursed_count":v["disbursed_count"],"disbursed_amount":v["disbursed_amount"]} for m,v in sorted(monthly.items())]

    customer_map={c.id:c for c in customers}
    loan_records=[{
        "loan_id":l.id,"customer_id":l.customer_id,
        "customer_code":getattr(customer_map.get(l.customer_id),"customer_code",None),
        "customer_name":getattr(customer_map.get(l.customer_id),"name",None) or "Customer",
        "mobile":getattr(customer_map.get(l.customer_id),"mobile",None),
        "business_name":getattr(customer_map.get(l.customer_id),"business_name",None),
        "loan_amount":money(l.sanctioned_amount or l.requested_amount),
        "requested_amount":money(l.requested_amount),
        "eligible_amount":money(l.eligible_amount),
        "sanctioned_amount":money(l.sanctioned_amount),
        "disbursed_amount":money(l.disbursed_amount),
        "outstanding_amount":money(l.outstanding_amount),
        "status":states[l.id],
        "stage":l.current_stage,
        "created_at":str(l.created_at) if l.created_at else None
    } for l in loans]

    loan_customer_map={l.id:l.customer_id for l in loans}
    repayment_records=[]
    for r in repayments:
        c=customer_map.get(loan_customer_map.get(r.loan_id))
        repayment_records.append({
            "id":r.id,"loan_id":r.loan_id,"customer_id":getattr(c,"id",None),
            "customer_code":getattr(c,"customer_code",None),
            "customer_name":getattr(c,"name",None) or "Customer",
            "due_date":str(r.due_date) if r.due_date else None,
            "due_amount":money(r.due_amount),"paid_amount":money(r.paid_amount),
            "unpaid_amount":money(max((r.due_amount or 0)-(r.paid_amount or 0),0)),
            "status":r.status,"dpd":calculate_dpd(r.due_date,r.paid_amount,r.due_amount)
        })

    customer_records=[{
        "customer_id":c.id,"customer_code":c.customer_code,"customer_name":c.name,
        "mobile":c.mobile,"email":c.email,"business_name":c.business_name,
        "kyc_status":c.kyc_status,"city":c.current_city
    } for c in customers]

    result = {
        "generated_at": datetime.utcnow().isoformat()+"Z", "customers": {"total":len(customers),"active":sum(c.kyc_status!="closed" for c in customers),"incomplete":sum(c.kyc_status!="verified" for c in customers),"kyc_verified":sum(c.kyc_status=="verified" for c in customers)},
        "applications":len(loans), "unique_users":len({l.customer_id for l in loans}), "repeat_users":sum(v>1 for v in Counter(l.customer_id for l in loans).values()),
        "pending":states_count["pending"], "rejected":states_count["rejected"], "disbursed_count":sum(bool(l.disbursed_amount) for l in loans),"active_loans":states_count["active"],"overdue_loans":states_count["overdue"],"repaid_loans":states_count["repaid"],
        "amounts":{"disbursed":money(sum(l.disbursed_amount or 0 for l in loans)),"outstanding":money(sum(l.outstanding_amount or 0 for l in loans if states[l.id] in {"active","overdue"})),"overdue":money(sum(max((r.due_amount or 0)-(r.paid_amount or 0),0) for r in repayments if calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0)),"due":money(sum(r.due_amount or 0 for r in repayments)),"paid":money(sum(r.paid_amount or 0 for r in repayments)),"unpaid":money(sum(max((r.due_amount or 0)-(r.paid_amount or 0),0) for r in repayments))},
        "documents":documents_count,"repayments":len(repayments),
        "customer_records":customer_records,"loan_records":loan_records,"repayment_records":repayment_records,
        "analytics_cards":{"unique_applicants":len({l.customer_id for l in loans}),"total_applications":len(loans),"rejected_loans":states_count["rejected"],"repaid_lms":states_count["repaid"],"overdue_lms":states_count["overdue"],"upcoming_lms":upcoming_lms,"due_today_lms":due_today_lms},
        "analytics_funnel":journey_funnel,
        "recent_loans":[{"id":l.id,"customer_id":l.customer_id,"amount":money(l.sanctioned_amount or l.requested_amount),"status":states[l.id],"created_at":str(l.created_at) if l.created_at else None} for l in loans[:20]],
        "monthly":monthly_rows,"loan_trend":loan_trend,"slabs":slabs,"repayment_status":repayment_status,"due_calendar":due_calendar,"collection":collection,"collection_agent_performance":agent_perf,"bank_analysis":bank_summary,"risk_score":risk_summary
    }
    _REPORT_CACHE["data"] = result
    _REPORT_CACHE["at"] = time.monotonic()
    response.headers["Cache-Control"] = "private, max-age=30, stale-while-revalidate=30"
    response.headers["X-Reporting-Cache"] = "MISS"
    return result
