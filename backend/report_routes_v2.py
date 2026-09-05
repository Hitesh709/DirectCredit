from collections import Counter
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord,LoanRecord,RepaymentRecord,BankTransactionRecord
from .analytics_routes import router as analytics_router
from .admin_auth import get_current_admin
from .profile_service import profile_payload
router=APIRouter(prefix="/reports",tags=["admin-reports"])
router.include_router(analytics_router)
def _rows(db): return db.query(CustomerRecord).all(),db.query(LoanRecord).all(),db.query(RepaymentRecord).all()
@router.get("/registration-users")
def registration_users(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 c,_,_=_rows(db); return [{"customer_id":x.id,"customer_code":x.customer_code,"name":x.name,"mobile":x.mobile,"business_name":x.business_name,"kyc_status":x.kyc_status,"created_at":str(x.created_at) if x.created_at else None} for x in sorted(c,key=lambda z:z.id,reverse=True)]
@router.get("/loan-pipeline")
def loan_pipeline(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=_rows(db); return {"total":len(l),"by_status":dict(Counter(x.status for x in l)),"rows":[{"loan_id":x.id,"customer_id":x.customer_id,"requested_amount":x.requested_amount,"sanctioned_amount":x.sanctioned_amount,"disbursed_amount":x.disbursed_amount,"status":x.status,"stage":x.current_stage} for x in sorted(l,key=lambda z:z.id,reverse=True)]}
@router.get("/disbursement")
def disbursement(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,_=_rows(db); return [{"loan_id":x.id,"customer_id":x.customer_id,"amount":x.disbursed_amount or 0,"status":x.status} for x in l if x.disbursed_amount]
@router.get("/repayment-collection")
def repayment_collection(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 _,l,r=_rows(db); return {"total_due":round(sum(x.due_amount or 0 for x in r),2),"total_paid":round(sum(x.paid_amount or 0 for x in r),2),"total_unpaid":round(sum(max(0,(x.due_amount or 0)-(x.paid_amount or 0)) for x in r),2),"loans":len(l),"repayments":len(r)}
@router.get("/accounting-ledger")
def accounting_ledger(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 from .servicing_models import AccountingEntry
 rows=db.query(AccountingEntry).order_by(AccountingEntry.entry_time,AccountingEntry.id).limit(10000).all(); return [{"id":x.id,"loan_id":x.loan_id,"customer_id":x.customer_id,"account":x.account,"entry_type":x.entry_type,"reference":x.reference,"debit":x.debit or 0,"credit":x.credit or 0,"narration":x.narration,"entry_time":str(x.entry_time) if x.entry_time else None} for x in rows]
@router.get("/customer/{customer_id}/profile")
def admin_customer_profile(customer_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data
@router.get("/customer/{customer_id}/bank-summary")
def admin_customer_bank_summary(customer_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["bank_analysis"]
@router.get("/customer/{customer_id}/bank-transactions")
def admin_customer_bank_transactions(customer_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    rows=db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id==customer_id).order_by(BankTransactionRecord.transaction_date.desc(),BankTransactionRecord.id.desc()).limit(5000).all()
    return [{"id":x.id,"transaction_date":x.transaction_date,"amount":x.amount,"direction":x.direction,"category":x.category,"description":x.description,"reference":x.reference,"balance":x.balance,"loan_id":x.loan_id} for x in rows]
