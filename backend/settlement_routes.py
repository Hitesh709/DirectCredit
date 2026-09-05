"""Settlement, foreclosure and closure workflow for the sample operations screen."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import LoanRecord, SettlementRecord
from .admin_auth import get_current_admin
from .auth import get_current_customer
from .servicing_models import AccountingEntry

router=APIRouter(prefix="/settlement",tags=["settlement"])

class SettlementQuote(BaseModel):
    settlement_type:str=Field(default="partial_settlement",min_length=5,max_length=40)
    proposed_amount:float=Field(gt=0)
    reason:str|None=Field(default=None,max_length=1000)
    reference:str|None=Field(default=None,max_length=160)

class SettlementComplete(BaseModel):
    amount:float=Field(gt=0)
    reference:str=Field(min_length=3,max_length=160)
    method:str=Field(default="bank_transfer",min_length=2,max_length=40)

def _loan(loan_id,db):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    outstanding=round(float(loan.outstanding_amount or 0),2)
    if outstanding<=0: raise HTTPException(409,"loan_has_no_outstanding_balance")
    return loan,outstanding

@router.get("/loan/{loan_id}/quote")
def quote(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,outstanding=_loan(loan_id,db)
    interest=round(outstanding*max(0,float(loan.interest_rate or 0))/100/12,2)
    foreclosure=round(outstanding+interest,2)
    return {"loan_id":loan_id,"customer_id":loan.customer_id,"outstanding_principal":outstanding,"interest_estimate":interest,"foreclosure_amount":foreclosure,"settlement_options":["foreclosure","partial_settlement","writeoff"]}

@router.post("/loan/{loan_id}/quote")
def create_quote(loan_id:int,body:SettlementQuote,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,outstanding=_loan(loan_id,db); kind=body.settlement_type.strip().lower()
    if kind not in {"foreclosure","partial_settlement","writeoff"}: raise HTTPException(422,"unsupported_settlement_type")
    if body.proposed_amount>outstanding: raise HTTPException(422,"proposed_amount_exceeds_outstanding")
    waiver=round(outstanding-body.proposed_amount,2)
    row=SettlementRecord(loan_id=loan_id,customer_id=loan.customer_id,settlement_type=kind,outstanding_amount=outstanding,proposed_amount=body.proposed_amount,waiver_amount=waiver,status="quoted",reason=body.reason,reference=body.reference)
    db.add(row);db.commit();db.refresh(row)
    return {"settlement_id":row.id,"loan_id":loan_id,"type":kind,"outstanding_amount":outstanding,"proposed_amount":body.proposed_amount,"waiver_amount":waiver,"status":"quoted"}

@router.post("/{settlement_id}/approve")
def approve(settlement_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    row=db.get(SettlementRecord,settlement_id)
    if not row: raise HTTPException(404,"settlement_not_found")
    if row.status!="quoted": raise HTTPException(409,"settlement_not_in_quoted_state")
    row.approved_amount=row.proposed_amount;row.status="approved";row.approved_at=datetime.utcnow();db.commit()
    return {"settlement_id":row.id,"loan_id":row.loan_id,"approved_amount":row.approved_amount,"waiver_amount":row.waiver_amount,"status":row.status}

@router.post("/{settlement_id}/complete")
def complete(settlement_id:int,body:SettlementComplete,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    row=db.get(SettlementRecord,settlement_id)
    if not row: raise HTTPException(404,"settlement_not_found")
    if row.status!="approved": raise HTTPException(409,"settlement_not_approved")
    if body.amount < float(row.approved_amount or 0): raise HTTPException(422,"payment_below_approved_settlement")
    loan=db.get(LoanRecord,row.loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    loan.outstanding_amount=0;loan.status="closed";loan.current_stage="CLOSED";row.status="completed";row.reference=body.reference;db.add(AccountingEntry(loan_id=loan.id,customer_id=loan.customer_id,account="loan_receivable",entry_type="settlement_receipt",reference=body.reference,credit=row.approved_amount,narration=f"Settlement completed via {body.method}"));db.commit()
    return {"settlement_id":row.id,"loan_id":loan.id,"received":body.amount,"settled_amount":row.approved_amount,"waiver_amount":row.waiver_amount,"loan_status":loan.status,"noc_status":"ready_for_issue"}

@router.get("/loan/{loan_id}/history")
def history(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(SettlementRecord).filter(SettlementRecord.loan_id==loan_id).order_by(SettlementRecord.id.desc()).all()
    return [{"id":x.id,"type":x.settlement_type,"outstanding_amount":x.outstanding_amount,"proposed_amount":x.proposed_amount,"approved_amount":x.approved_amount,"waiver_amount":x.waiver_amount,"status":x.status,"reason":x.reason,"reference":x.reference,"created_at":str(x.created_at) if x.created_at else None} for x in rows]

@router.get("/customer/{loan_id}")
def customer_history(loan_id:int,db:Session=Depends(get_db),claims=Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan or int(loan.customer_id)!=int(claims.get("user_id",-1)): raise HTTPException(404,"loan_not_found")
    return {"loan_id":loan_id,"outstanding_amount":loan.outstanding_amount or 0,"settlements":[{"id":x.id,"type":x.settlement_type,"approved_amount":x.approved_amount,"status":x.status} for x in db.query(SettlementRecord).filter(SettlementRecord.loan_id==loan_id).order_by(SettlementRecord.id.desc()).all()]}
