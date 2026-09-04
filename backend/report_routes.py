from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd

router=APIRouter(prefix="/api/admin/reports",tags=["admin-reports"])

@router.get("/registrations")
def registrations(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).limit(5000).all()
    return [{"customer_id":x.id,"customer_code":x.customer_code,"name":x.name,"mobile":x.mobile,"business_name":x.business_name,"kyc_status":x.kyc_status,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@router.get("/loan-pipeline")
def loan_pipeline(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(LoanRecord).order_by(LoanRecord.id.desc()).limit(5000).all()
    return [{"loan_id":x.id,"customer_id":x.customer_id,"requested_amount":x.requested_amount,"eligible_amount":x.eligible_amount,"sanctioned_amount":x.sanctioned_amount,"disbursed_amount":x.disbursed_amount,"status":x.status,"stage":x.current_stage,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@router.get("/disbursements")
def disbursement_report(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(LoanRecord).filter(LoanRecord.disbursed_amount>0).order_by(LoanRecord.id.desc()).limit(5000).all()
    return [{"loan_id":x.id,"customer_id":x.customer_id,"amount":x.disbursed_amount,"status":x.status,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@router.get("/repayments")
def repayment_report(status:str|None=None,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(RepaymentRecord).order_by(RepaymentRecord.due_date,RepaymentRecord.installment).limit(10000).all(); out=[]
    for x in rows:
        dpd=calculate_dpd(x.due_date,x.paid_amount,x.due_amount); derived="paid" if x.paid_amount>=x.due_amount else ("overdue" if dpd>0 else "upcoming")
        if status and derived!=status: continue
        out.append({"repayment_id":x.id,"loan_id":x.loan_id,"installment":x.installment,"due_date":x.due_date,"due_amount":x.due_amount,"paid_amount":x.paid_amount or 0,"unpaid_amount":max(0,(x.due_amount or 0)-(x.paid_amount or 0)),"status":derived,"dpd":dpd,"payment_reference":x.payment_reference})
    return out

@router.get("/accounting-trial-balance")
def trial_balance(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    from .servicing_models import AccountingEntry
    rows=db.query(AccountingEntry).all(); accounts={}
    for x in rows:
        a=accounts.setdefault(x.account,{"debit":0.0,"credit":0.0}); a["debit"]+=x.debit or 0; a["credit"]+=x.credit or 0
    return {"generated_at":datetime.utcnow().isoformat()+"Z","accounts":[{"account":k,"debit":round(v["debit"],2),"credit":round(v["credit"],2),"net":round(v["debit"]-v["credit"],2)} for k,v in sorted(accounts.items())]}
