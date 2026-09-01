from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord

router = APIRouter(prefix="/api/admin", tags=["reporting"])


def loan_state(loan, repayment_rows):
    if any(r.status == "overdue" and (r.paid_amount or 0) < (r.due_amount or 0) for r in repayment_rows):
        return "overdue"
    if (loan.outstanding_amount or 0) <= 0 and (loan.disbursed_amount or 0) > 0:
        return "repaid"
    if (loan.disbursed_amount or 0) > 0 or loan.status in {"disbursed", "repayment", "active"}:
        return "active"
    if loan.status in {"rejected", "dropped"}:
        return "rejected"
    return "pending"


def money(v):
    return round(float(v or 0), 2)


@router.get("/reporting")
def reporting(db: Session = Depends(get_db)):
    customers = db.query(CustomerRecord).all()
    loans = db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()
    repayments = db.query(RepaymentRecord).all()
    documents = db.query(DocumentRecord).all()
    by_loan = defaultdict(list)
    for r in repayments:
        by_loan[r.loan_id].append(r)

    states = {l.id: loan_state(l, by_loan[l.id]) for l in loans}
    counts = Counter(states.values())
    applications = len(loans)
    unique_users = len({l.customer_id for l in loans})
    customer_loan_counts = Counter(l.customer_id for l in loans)
    repeat_users = sum(1 for n in customer_loan_counts.values() if n > 1)
    rejected = sum(1 for l in loans if l.status in {"rejected", "dropped"})
    pending = sum(1 for s in states.values() if s == "pending")
    disbursed = [l for l in loans if (l.disbursed_amount or 0) > 0 or states[l.id] in {"active", "overdue", "repaid"}]
    active = [l for l in loans if states[l.id] == "active"]
    overdue_loans = [l for l in loans if states[l.id] == "overdue"]
    repaid_loans = [l for l in loans if states[l.id] == "repaid"]

    total_disbursed = sum((l.disbursed_amount or l.sanctioned_amount or 0) for l in disbursed)
    outstanding = sum((l.outstanding_amount or 0) for l in active + overdue_loans)
    overdue_amount = sum(max((r.due_amount or 0) - (r.paid_amount or 0), 0) for r in repayments if r.status == "overdue")
    paid_amount = sum(r.paid_amount or 0 for r in repayments)
    due_amount = sum(r.due_amount or 0 for r in repayments)

    now = datetime.utcnow()
    month_rows = []
    for offset in range(11, -1, -1):
        first = (now.replace(day=1) - timedelta(days=offset * 28)).replace(day=1)
        if first.month == 12:
            next_month = first.replace(year=first.year + 1, month=1)
        else:
            next_month = first.replace(month=first.month + 1)
        created = [l for l in loans if l.created_at and first <= l.created_at.replace(tzinfo=None) < next_month]
        ds = [l for l in disbursed if l.created_at and first <= l.created_at.replace(tzinfo=None) < next_month]
        month_rows.append({
            "month": first.strftime("%b-%y"),
            "applications": len(created),
            "disbursed_count": len(ds),
            "disbursed_amount": money(sum((l.disbursed_amount or l.sanctioned_amount or 0) for l in ds))
        })

    slabs = [5000, 7500, 10000, 12500, 15000]
    slab_rows = []
    for amount in slabs:
        matching = [l for l in loans if round(l.sanctioned_amount or l.requested_amount or 0) == amount]
        ac = [l for l in matching if states[l.id] == "active"]
        od = [l for l in matching if states[l.id] == "overdue"]
        rp = [l for l in matching if states[l.id] == "repaid"]
        slab_rows.append({
            "amount": amount,
            "active_count": len(ac), "active_amount": money(sum(l.outstanding_amount or l.disbursed_amount or 0 for l in ac)),
            "overdue_count": len(od), "overdue_amount": money(sum(max(l.outstanding_amount or 0, 0) for l in od)),
            "repaid_count": len(rp), "repaid_amount": money(sum(l.disbursed_amount or l.sanctioned_amount or 0 for l in rp)),
            "total_count": len(matching)
        })

    repayment_status = defaultdict(lambda: {"count": 0, "due": 0.0, "paid": 0.0})
    today = date.today()
    for r in repayments:
        try:
            due = date.fromisoformat(str(r.due_date)[:10])
            dpd = max((today - due).days, 0) if (r.paid_amount or 0) < (r.due_amount or 0) else 0
        except Exception:
            dpd = 0
        if dpd >= 90: bucket = "NPA DPD 90+"
        elif dpd >= 61: bucket = "Overdue DPD 61–90"
        elif dpd >= 31: bucket = "Overdue DPD 31–60"
        elif dpd > 0: bucket = "Overdue DPD 1–30"
        elif (r.paid_amount or 0) >= (r.due_amount or 0): bucket = "On-Time / Paid"
        else: bucket = "Upcoming"
        x = repayment_status[bucket]
        x["count"] += 1; x["due"] += r.due_amount or 0; x["paid"] += r.paid_amount or 0

    due_calendar = defaultdict(lambda: {"count": 0, "due": 0.0, "paid": 0.0})
    for r in repayments:
        key = str(r.due_date)[:10]
        x = due_calendar[key]
        x["count"] += 1; x["due"] += r.due_amount or 0; x["paid"] += r.paid_amount or 0

    collection = []
    customer_map = {c.id: c for c in customers}
    for l in loans:
        od = sum(max((r.due_amount or 0) - (r.paid_amount or 0), 0) for r in by_loan[l.id] if r.status == "overdue")
        if od <= 0 and states[l.id] not in {"active", "repaid"}:
            continue
        c = customer_map.get(l.customer_id)
        if not c: continue
        collection.append({
            "loan_id": l.id, "customer_id": c.id, "name": c.name, "mobile": c.mobile,
            "loan_amount": money(l.sanctioned_amount or l.requested_amount), "outstanding": money(l.outstanding_amount),
            "overdue": money(od), "status": states[l.id], "bank": c.primary_bank, "mandate": "Not configured"
        })

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "customers": {"total": len(customers), "active": sum(c.status == "active" for c in customers), "kyc_verified": sum(c.kyc_status == "verified" for c in customers), "incomplete": sum(c.kyc_status != "verified" for c in customers)},
        "applications": applications, "unique_users": unique_users, "repeat_users": repeat_users,
        "pending": pending, "rejected": rejected, "disbursed_count": len(disbursed), "active_loans": len(active), "overdue_loans": len(overdue_loans), "repaid_loans": len(repaid_loans),
        "amounts": {"disbursed": money(total_disbursed), "outstanding": money(outstanding), "overdue": money(overdue_amount), "due": money(due_amount), "paid": money(paid_amount), "unpaid": money(max(due_amount - paid_amount, 0))},
        "documents": len(documents), "repayments": len(repayments), "monthly": month_rows, "slabs": slab_rows,
        "repayment_status": {k: {"count": v["count"], "due": money(v["due"]), "paid": money(v["paid"]), "unpaid": money(max(v["due"]-v["paid"],0))} for k,v in repayment_status.items()},
        "due_calendar": [{"date": k, **{x: money(v) if x != "count" else v for x,v in val.items()}} for k,val in sorted(due_calendar.items())],
        "collection": collection[:500],
        "recent_loans": [{"id": l.id, "customer_id": l.customer_id, "amount": money(l.sanctioned_amount or l.requested_amount), "status": states[l.id], "created_at": str(l.created_at) if l.created_at else None} for l in loans[:20]]
    }
