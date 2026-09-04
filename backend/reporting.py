from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord
from .analytics_routes import router as analytics_router
from .report_routes import router as report_router
from .admin_auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["reporting"])
router.include_router(analytics_router)
router.include_router(report_router)

def loan_state(loan, repayment_rows):
    if any(r.status == "overdue" and (r.paid_amount or 0) < (r.due_amount or 0) for r in repayment_rows): return "overdue"
    if (loan.outstanding_amount or 0) <= 0 and (loan.disbursed_amount or 0) > 0: return "repaid"
    if (loan.disbursed_amount or 0) > 0 or loan.status in {"disbursed", "repayment", "active"}: return "active"
    if loan.status in {"rejected", "dropped"}: return "rejected"
    return "pending"

def money(v): return round(float(v or 0), 2)

@router.get("/reporting")
def reporting(db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    customers = db.query(CustomerRecord).all()
    loans = db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()
    repayments = db.query(RepaymentRecord).all()
    documents = db.query(DocumentRecord).all()
    by = defaultdict(list)
    for r in repayments: by[r.loan_id].append(r)
    states = {l.id: loan_state(l, by[l.id]) for l in loans}
    dis = [l for l in loans if l.disbursed_amount or states[l.id] in {"active", "overdue", "repaid"}]
    active = [l for l in loans if states[l.id] == "active"]
    overdue = [l for l in loans if states[l.id] == "overdue"]
    return {"generated_at": datetime.utcnow().isoformat()+"Z", "customers": {"total": len(customers), "kyc_verified": sum(c.kyc_status == "verified" for c in customers)}, "applications": len(loans), "unique_users": len({l.customer_id for l in loans}), "pending": sum(s == "pending" for s in states.values()), "rejected": sum(l.status in {"rejected", "dropped"} for l in loans), "disbursed_count": len(dis), "active_loans": len(active), "overdue_loans": len(overdue), "repaid_loans": sum(s == "repaid" for s in states.values()), "amounts": {"disbursed": money(sum(l.disbursed_amount or l.sanctioned_amount or 0 for l in dis)), "outstanding": money(sum(l.outstanding_amount or 0 for l in active+overdue)), "overdue": money(sum(max((r.due_amount or 0)-(r.paid_amount or 0), 0) for r in repayments if r.status == "overdue")), "due": money(sum(r.due_amount or 0 for r in repayments)), "paid": money(sum(r.paid_amount or 0 for r in repayments))}, "documents": len(documents), "repayments": len(repayments), "recent_loans": [{"id": l.id, "customer_id": l.customer_id, "amount": money(l.sanctioned_amount or l.requested_amount), "status": states[l.id]} for l in loans[:20]]}
