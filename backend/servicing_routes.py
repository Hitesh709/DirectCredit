from __future__ import annotations
from datetime import datetime, date
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_customer
from .admin_auth import get_current_admin
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord
from .repayment_contract import calculate_dpd, derive_status, repayment_payload
from .servicing_models import DisbursementRecord, LedgerEntry, AccountingEntry

router = APIRouter(prefix="/api/servicing", tags=["loan-servicing"])

def customer_loan(loan_id, claims, db):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan not found")
    if int(loan.customer_id)!=int(claims.get("user_id",-1)): raise HTTPException(403,"Loan access forbidden")
    return loan

def rebuild_ledger(loan_id, db):
    loan=db.get(LoanRecord,loan_id)
    if not loan: return
    db.query(LedgerEntry).filter(LedgerEntry.loan_id==loan_id).delete()
    balance=0.0
    disb=db.query(DisbursementRecord).filter(DisbursementRecord.loan_id==loan_id,DisbursementRecord.status=="completed").order_by(DisbursementRecord.id).all()
    for x in disb:
        balance=round(balance+float(x.amount or 0),2)
        db.add(LedgerEntry(loan_id=loan.id,customer_id=loan.customer_id,entry_type="disbursement",reference=x.reference,debit=x.amount,balance=balance,description="Loan disbursement"))
    rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()
    for r in rows:
        paid=float(r.paid_amount or 0)
        if paid:
            balance=round(max(0,balance-paid),2)
            db.add(LedgerEntry(loan_id=loan.id,customer_id=loan.customer_id,entry_type="repayment",reference=r.payment_reference,credit=paid,balance=balance,description=f"Installment {r.installment} payment"))
    return balance

@router.get("/loan/{loan_id}/ledger")
def loan_ledger(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    customer_loan(loan_id,claims,db)
    rows=db.query(LedgerEntry).filter(LedgerEntry.loan_id==loan_id).order_by(LedgerEntry.entry_time,LedgerEntry.id).all()
    return [{"id":r.id,"entry_type":r.entry_type,"reference":r.reference,"debit":r.debit or 0,"credit":r.credit or 0,"balance":r.balance or 0,"description":r.description,"entry_time":r.entry_time.isoformat() if r.entry_time else None} for r in rows]

class DisbursementRequest(BaseModel):
    amount: float = Field(gt=0)
    reference: str = Field(min_length=3,max_length=160)
    method: str = Field(default="bank_transfer",min_length=2,max_length=40)

@router.post("/admin/loan/{loan_id}/disbursement")
def record_disbursement(loan_id:int,body:DisbursementRequest,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan not found")
    if loan.status not in {"disbursement_pending","sanctioned","customer_approved","mandate_active"}: raise HTTPException(409,"Loan is not ready for disbursement")
    if body.amount>float(loan.sanctioned_amount or loan.eligible_amount or 0): raise HTTPException(422,"Disbursement exceeds sanctioned amount")
    row=DisbursementRecord(loan_id=loan.id,customer_id=loan.customer_id,amount=body.amount,reference=body.reference,method=body.method,status="completed",disbursed_at=datetime.utcnow())
    db.add(row); loan.disbursed_amount=round(float(loan.disbursed_amount or 0)+body.amount,2); loan.outstanding_amount=loan.disbursed_amount; loan.status="active"; loan.current_stage="REPAYMENT"
    db.flush(); rebuild_ledger(loan_id,db); db.add(AccountingEntry(loan_id=loan.id,customer_id=loan.customer_id,account="loan_receivable",entry_type="disbursement",reference=body.reference,debit=body.amount,credit=0,narration="Loan disbursement")); db.commit(); db.refresh(row)
    return {"disbursement_id":row.id,"loan_id":loan.id,"amount":row.amount,"status":row.status,"disbursed_amount":loan.disbursed_amount}

@router.get("/loan/{loan_id}/disbursements")
def disbursements(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    customer_loan(loan_id,claims,db)
    rows=db.query(DisbursementRecord).filter(DisbursementRecord.loan_id==loan_id).order_by(DisbursementRecord.id.desc()).all()
    return [{"id":r.id,"amount":r.amount,"reference":r.reference,"method":r.method,"status":r.status,"disbursed_at":r.disbursed_at.isoformat() if r.disbursed_at else None} for r in rows]

class Payment(BaseModel):
    amount: float = Field(gt=0)
    reference: str = Field(min_length=3,max_length=160)
    method: str = Field(default="upi",min_length=2,max_length=40)

@router.post("/loan/{loan_id}/repayment")
def repayment(loan_id:int,body:Payment,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    loan=customer_loan(loan_id,claims,db); remaining=body.amount
    rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()
    for r in rows:
        bal=max(0,float(r.due_amount or 0)-float(r.paid_amount or 0))
        if bal<=0 or remaining<=0: continue
        a=min(bal,remaining); r.paid_amount=round(float(r.paid_amount or 0)+a,2); r.payment_reference=body.reference; r.payment_method=body.method; r.paid_at=datetime.utcnow(); r.status=derive_status(r.due_date,r.due_amount,r.paid_amount); remaining=round(remaining-a,2)
    loan.outstanding_amount=round(sum(max(0,float(r.due_amount or 0)-float(r.paid_amount or 0)) for r in rows),2)
    loan.status="repaid" if loan.outstanding_amount<=0 else ("overdue" if any(calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0 for r in rows if r.paid_amount<r.due_amount) else "active")
    rebuild_ledger(loan_id,db)
    db.add(AccountingEntry(loan_id=loan.id,customer_id=loan.customer_id,account="loan_receivable",entry_type="repayment",reference=body.reference,debit=0,credit=body.amount-remaining,narration="Customer repayment"))
    db.commit()
    return {"loan_id":loan_id,"received":body.amount,"unallocated":remaining,"outstanding_amount":loan.outstanding_amount,"status":loan.status}

@router.get("/loan/{loan_id}/dpd")
def loan_dpd(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    customer_loan(loan_id,claims,db); rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).all(); today=date.today()
    values=[{"repayment_id":r.id,"installment":r.installment,"dpd":calculate_dpd(r.due_date,r.paid_amount,r.due_amount,today),"status":r.status} for r in rows]
    return {"loan_id":loan_id,"max_dpd":max([x["dpd"] for x in values] or [0]),"installments":values}

@router.get("/loan/{loan_id}/foreclosure")
def foreclosure(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    loan=customer_loan(loan_id,claims,db); principal=max(0,float(loan.outstanding_amount or 0)); rate=max(0,float(loan.interest_rate or 0)); annual_interest=principal*rate/100; estimate=round(principal+annual_interest/12,2)
    return {"loan_id":loan_id,"outstanding_principal":round(principal,2),"interest_rate":rate,"estimated_foreclosure_amount":estimate,"method":"principal_plus_one_month_interest"}

@router.get("/admin/collections")
def collections(status:str|None=None,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loans=db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all(); out=[]
    for l in loans:
        rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==l.id).all(); overdue=sum(max(0,float(r.due_amount or 0)-float(r.paid_amount or 0)) for r in rows if calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0)
        if status and ("overdue" if overdue else "current")!=status: continue
        out.append({"loan_id":l.id,"customer_id":l.customer_id,"outstanding":l.outstanding_amount or 0,"overdue":round(overdue,2),"status":"overdue" if overdue else "current"})
    return out

@router.post("/admin/loan/{loan_id}/close")
def close_loan(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan not found")
    if float(loan.outstanding_amount or 0)>0: raise HTTPException(409,"Loan has outstanding balance")
    loan.status="closed"; loan.current_stage="CLOSED"; db.commit()
    return {"loan_id":loan_id,"status":"closed","noc_status":"ready_for_issue"}

@router.get("/admin/accounting")
def accounting(loan_id:int|None=None,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    q=db.query(AccountingEntry).order_by(AccountingEntry.entry_time,AccountingEntry.id)
    if loan_id: q=q.filter(AccountingEntry.loan_id==loan_id)
    rows=q.limit(5000).all()
    return [{"id":r.id,"loan_id":r.loan_id,"customer_id":r.customer_id,"account":r.account,"entry_type":r.entry_type,"reference":r.reference,"debit":r.debit or 0,"credit":r.credit or 0,"narration":r.narration,"entry_time":r.entry_time.isoformat() if r.entry_time else None} for r in rows]
