from __future__ import annotations
from datetime import datetime,date
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_customer
from .admin_auth import get_current_admin
from .db_models import LoanRecord,RepaymentRecord
from .repayment_contract import calculate_dpd,derive_status
from .servicing_models import DisbursementRecord,LedgerEntry,AccountingEntry
router=APIRouter(prefix="/servicing",tags=["loan-servicing"])
def customer_loan(i,c,d):
 l=d.get(LoanRecord,i)
 if not l: raise HTTPException(404,"Loan not found")
 if int(l.customer_id)!=int(c.get("user_id",-1)): raise HTTPException(403,"Loan access forbidden")
 return l
def rebuild_ledger(i,d):
 l=d.get(LoanRecord,i); d.query(LedgerEntry).filter(LedgerEntry.loan_id==i).delete(); bal=0.0
 for x in d.query(DisbursementRecord).filter(DisbursementRecord.loan_id==i,DisbursementRecord.status=="completed").order_by(DisbursementRecord.id):
  bal=round(bal+x.amount,2); d.add(LedgerEntry(loan_id=i,customer_id=l.customer_id,entry_type="disbursement",reference=x.reference,debit=x.amount,balance=bal,description="Loan disbursement"))
 for r in d.query(RepaymentRecord).filter(RepaymentRecord.loan_id==i).order_by(RepaymentRecord.installment):
  if r.paid_amount: bal=round(max(0,bal-r.paid_amount),2); d.add(LedgerEntry(loan_id=i,customer_id=l.customer_id,entry_type="repayment",reference=r.payment_reference,credit=r.paid_amount,balance=bal,description=f"Installment {r.installment} payment"))
@router.get("/loan/{loan_id}/ledger")
def ledger(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
 customer_loan(loan_id,claims,db); return [{"id":x.id,"entry_type":x.entry_type,"reference":x.reference,"debit":x.debit or 0,"credit":x.credit or 0,"balance":x.balance or 0,"description":x.description} for x in db.query(LedgerEntry).filter(LedgerEntry.loan_id==loan_id).order_by(LedgerEntry.id)]
class Disbursement(BaseModel): amount:float=Field(gt=0); reference:str=Field(min_length=3,max_length=160); method:str="bank_transfer"
@router.post("/admin/loan/{loan_id}/disbursement")
def disburse(loan_id:int,b:Disbursement,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 l=db.get(LoanRecord,loan_id)
 if not l: raise HTTPException(404,"Loan not found")
 if l.status not in {"disbursement_pending","sanctioned","customer_approved","mandate_active"}: raise HTTPException(409,"Loan is not ready for disbursement")
 if b.amount>float(l.sanctioned_amount or l.eligible_amount or 0)-float(l.disbursed_amount or 0): raise HTTPException(422,"Disbursement exceeds remaining sanctioned amount")
 db.add(DisbursementRecord(loan_id=loan_id,customer_id=l.customer_id,amount=b.amount,reference=b.reference,method=b.method,status="completed",disbursed_at=datetime.utcnow())); l.disbursed_amount=round(float(l.disbursed_amount or 0)+b.amount,2); l.outstanding_amount=l.disbursed_amount; l.status="active"; l.current_stage="REPAYMENT"; db.flush(); rebuild_ledger(loan_id,db); db.add(AccountingEntry(loan_id=loan_id,customer_id=l.customer_id,account="loan_receivable",entry_type="disbursement",reference=b.reference,debit=b.amount,narration="Loan disbursement")); db.commit(); return {"loan_id":loan_id,"amount":b.amount,"status":"completed","disbursed_amount":l.disbursed_amount}
@router.get("/loan/{loan_id}/disbursements")
def disbursements(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
 customer_loan(loan_id,claims,db); return [{"id":x.id,"amount":x.amount,"reference":x.reference,"method":x.method,"status":x.status,"disbursed_at":str(x.disbursed_at) if x.disbursed_at else None} for x in db.query(DisbursementRecord).filter(DisbursementRecord.loan_id==loan_id).all()]
class Payment(BaseModel): amount:float=Field(gt=0); reference:str=Field(min_length=3,max_length=160); method:str="upi"
@router.post("/loan/{loan_id}/repayment")
def repayment(loan_id:int,b:Payment,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
 l=customer_loan(loan_id,claims,db); rem=b.amount; rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()
 if not rows: raise HTTPException(409,"No repayment schedule exists")
 for r in rows:
  bal=max(0,float(r.due_amount or 0)-float(r.paid_amount or 0)); a=min(bal,rem)
  if a<=0: continue
  r.paid_amount=round(float(r.paid_amount or 0)+a,2); r.payment_reference=b.reference; r.payment_method=b.method; r.paid_at=datetime.utcnow(); r.status=derive_status(r.due_date,r.due_amount,r.paid_amount); rem=round(rem-a,2)
 l.outstanding_amount=round(sum(max(0,float(r.due_amount or 0)-float(r.paid_amount or 0)) for r in rows),2); l.status="repaid" if l.outstanding_amount<=0 else ("overdue" if any(calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0 for r in rows if r.paid_amount<r.due_amount) else "active"); rebuild_ledger(loan_id,db); db.add(AccountingEntry(loan_id=loan_id,customer_id=l.customer_id,account="loan_receivable",entry_type="repayment",reference=b.reference,credit=b.amount-rem,narration="Customer repayment")); db.commit(); return {"loan_id":loan_id,"received":b.amount,"unallocated":rem,"outstanding_amount":l.outstanding_amount,"status":l.status}
@router.get("/loan/{loan_id}/dpd")
def dpd(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
 customer_loan(loan_id,claims,db); v=[{"repayment_id":r.id,"installment":r.installment,"dpd":calculate_dpd(r.due_date,r.paid_amount,r.due_amount),"status":r.status} for r in db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id)]; return {"loan_id":loan_id,"max_dpd":max([x["dpd"] for x in v] or [0]),"installments":v}
@router.get("/loan/{loan_id}/foreclosure")
def foreclosure(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
 l=customer_loan(loan_id,claims,db); p=max(0,float(l.outstanding_amount or 0)); interest=round(p*max(0,float(l.interest_rate or 0))/100/12,2); return {"loan_id":loan_id,"outstanding_principal":p,"interest_estimate":interest,"estimated_foreclosure_amount":round(p+interest,2)}
@router.get("/admin/collections")
def collections(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 out=[]
 for l in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all():
  rs=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==l.id).all(); od=sum(max(0,float(r.due_amount or 0)-float(r.paid_amount or 0)) for r in rs if calculate_dpd(r.due_date,r.paid_amount,r.due_amount)>0); out.append({"loan_id":l.id,"customer_id":l.customer_id,"outstanding":l.outstanding_amount or 0,"overdue":round(od,2),"status":"overdue" if od else "current"})
 return out
@router.post("/admin/loan/{loan_id}/close")
def close(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 l=db.get(LoanRecord,loan_id)
 if not l: raise HTTPException(404,"Loan not found")
 if float(l.outstanding_amount or 0)>0: raise HTTPException(409,"Loan has outstanding balance")
 l.status="closed"; l.current_stage="CLOSED"; db.commit(); return {"loan_id":loan_id,"status":"closed","noc_status":"ready_for_issue"}
@router.get("/admin/accounting")
def accounting(loan_id:int|None=None,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
 q=db.query(AccountingEntry).order_by(AccountingEntry.id); 
 if loan_id: q=q.filter(AccountingEntry.loan_id==loan_id)
 return [{"id":x.id,"loan_id":x.loan_id,"customer_id":x.customer_id,"account":x.account,"entry_type":x.entry_type,"reference":x.reference,"debit":x.debit or 0,"credit":x.credit or 0,"narration":x.narration} for x in q.limit(10000)]
