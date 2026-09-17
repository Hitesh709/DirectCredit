from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import LoanRecord, RepaymentRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .phase2i_collections import collection_bucket, overdue_amount
from .phase2n_strategy import PHASE2N_VERSION, build_allocation, strategy_contract
import json

router=APIRouter(prefix="/api/v1/collections/strategy",tags=["phase-2n-strategy"])

def _loan_context(loan_id,db):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).all()
    overdue,max_dpd=overdue_amount(rows)
    bucket=collection_bucket(max_dpd)
    actions=db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id).all()
    mandate_active=False; active_ptp=False; failed_debit=False
    for a in actions:
        try: d=json.loads(a.notes or "{}")
        except Exception: d={}
        if d.get("mandate_status")=="ACTIVE": mandate_active=True
        if a.action_type in ("promise_to_pay","ptp") and str(d.get("status","")).upper() not in {"KEPT","CANCELLED"}: active_ptp=True
        if a.action_type in ("auto_debit","debit_request") and str(d.get("status","")).upper() in {"FAILED","FAILURE"}: failed_debit=True
    return loan,overdue,max_dpd,bucket,mandate_active,active_ptp,failed_debit

@router.get("/contract")
def contract(): return strategy_contract()

@router.get("/loan/{loan_id}/plan")
def loan_plan(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,overdue,max_dpd,bucket,mandate,ptp,failed=_loan_context(loan_id,db)
    return {"loan_id":loan.id,"customer_id":loan.customer_id,"bucket":bucket,"dpd":max_dpd,"overdue_amount":overdue,"strategy":build_allocation(loan_id=loan.id,bucket=bucket,overdue_amount=overdue,max_dpd=max_dpd,agents=[],mandate_active=mandate,active_ptp=ptp,failed_debit=failed).__dict__,"engine_version":PHASE2N_VERSION}

@router.post("/loan/{loan_id}/allocate")
def allocate(loan_id:int,payload:dict,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,overdue,max_dpd,bucket,mandate,ptp,failed=_loan_context(loan_id,db)
    agents=payload.get("agents") or []
    decision=build_allocation(loan_id=loan.id,bucket=bucket,overdue_amount=overdue,max_dpd=max_dpd,agents=agents,mandate_active=mandate,active_ptp=ptp,failed_debit=failed)
    return {"loan_id":loan.id,"customer_id":loan.customer_id,"decision":decision.__dict__,"engine_version":PHASE2N_VERSION}

@router.get("/queue")
def queue(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    out=[]
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all():
        _,overdue,max_dpd,bucket,mandate,ptp,failed=_loan_context(loan.id,db)
        if overdue<=0: continue
        d=build_allocation(loan_id=loan.id,bucket=bucket,overdue_amount=overdue,max_dpd=max_dpd,agents=[],mandate_active=mandate,active_ptp=ptp,failed_debit=failed)
        out.append({"loan_id":loan.id,"customer_id":loan.customer_id,"bucket":bucket,"dpd":max_dpd,"overdue_amount":overdue,"strategy":d.strategy,"score":d.score,"sla_hours":d.sla_hours,"reason_codes":list(d.reason_codes)})
    return sorted(out,key=lambda x:(-x["score"],-x["overdue_amount"],x["loan_id"]))
