import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .phase2j_collections_intelligence import build_priority, collection_bucket, overdue_amount
from .phase2i_collections import dpd
from .phase2l_field_operations import PHASE2L_VERSION, field_operations_contract, normalize_disposition, normalize_visit_outcome

router=APIRouter(prefix="/api/v1/field-operations",tags=["phase-2l-field-operations"])

class CallLog(BaseModel):
    disposition:str=Field(min_length=2,max_length=40)
    reference:str=Field(min_length=3,max_length=160)
    notes:str|None=Field(default=None,max_length=1500)
    callback_at:str|None=Field(default=None,max_length=30)

class VisitLog(BaseModel):
    outcome:str=Field(min_length=2,max_length=50)
    reference:str=Field(min_length=3,max_length=160)
    notes:str|None=Field(default=None,max_length=1500)
    latitude:float|None=None
    longitude:float|None=None
    visited_at:str|None=Field(default=None,max_length=30)

class AssignmentRequest(BaseModel):
    agent_id:int
    reference:str=Field(min_length=3,max_length=160)
    notes:str|None=Field(default=None,max_length=1000)

def _loan(loan_id,db):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    customer=db.get(CustomerRecord,loan.customer_id)
    if not customer: raise HTTPException(404,"customer_not_found")
    return loan,customer

def _audit(db,loan,customer,action,reference,notes):
    if db.query(CollectionActionRecord).filter(CollectionActionRecord.reference==reference).first(): raise HTTPException(409,"collection_reference_already_exists")
    row=CollectionActionRecord(loan_id=loan.id,customer_id=customer.id,action_type=action,amount=0,reference=reference,status="recorded",notes=json.dumps(notes,ensure_ascii=False))
    db.add(row); db.commit(); db.refresh(row); return row

def _priority(loan,db):
    from .phase2j_collections_intelligence import collection_bucket, overdue_amount
    rows=db.query(__import__('backend.db_models',fromlist=['RepaymentRecord']).RepaymentRecord).filter(__import__('backend.db_models',fromlist=['RepaymentRecord']).RepaymentRecord.loan_id==loan.id).all()
    overdue,max_dpd=overdue_amount(rows); bucket=collection_bucket(max_dpd); p=build_priority(bucket,overdue,max_dpd)
    return overdue,max_dpd,p

@router.get("/contract")
def contract(): return field_operations_contract()

@router.get("/queue")
def queue(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    out=[]
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all():
        overdue,max_dpd,p=_priority(loan,db)
        if overdue<=0: continue
        out.append({"loan_id":loan.id,"customer_id":loan.customer_id,"dpd":max_dpd,"overdue_amount":overdue,"priority_score":p.score,"urgency":p.urgency})
    return sorted(out,key=lambda x:(-x["priority_score"],-x["overdue_amount"],x["loan_id"]))

@router.post("/loan/{loan_id}/assign")
def assign(loan_id:int,body:AssignmentRequest,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,customer=_loan(loan_id,db); overdue,max_dpd,p=_priority(loan,db)
    if overdue<=0: raise HTTPException(409,"no_overdue_amount")
    row=_audit(db,loan,customer,"agent_assignment",body.reference,{"agent_id":body.agent_id,"priority_score":p.score,"urgency":p.urgency,"dpd":max_dpd,"notes":body.notes,"assigned_at":datetime.utcnow().isoformat()})
    return {"assignment_id":row.id,"loan_id":loan.id,"agent_id":body.agent_id,"status":"recorded","priority_score":p.score}

@router.post("/loan/{loan_id}/call")
def call(loan_id:int,body:CallLog,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,customer=_loan(loan_id,db)
    try: disposition=normalize_disposition(body.disposition)
    except ValueError as e: raise HTTPException(422,str(e))
    row=_audit(db,loan,customer,"collection_call",body.reference,{"disposition":disposition,"notes":body.notes,"callback_at":body.callback_at,"called_at":datetime.utcnow().isoformat()})
    return {"call_id":row.id,"loan_id":loan.id,"disposition":disposition,"status":"recorded"}

@router.post("/loan/{loan_id}/visit")
def visit(loan_id:int,body:VisitLog,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,customer=_loan(loan_id,db)
    try: outcome=normalize_visit_outcome(body.outcome)
    except ValueError as e: raise HTTPException(422,str(e))
    geo={"latitude":body.latitude,"longitude":body.longitude} if body.latitude is not None and body.longitude is not None else None
    row=_audit(db,loan,customer,"field_visit",body.reference,{"outcome":outcome,"notes":body.notes,"geo":geo,"visited_at":body.visited_at or datetime.utcnow().isoformat()})
    return {"visit_id":row.id,"loan_id":loan.id,"outcome":outcome,"geo_recorded":geo is not None,"status":"recorded"}

@router.get("/loan/{loan_id}/timeline")
def timeline(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan,_=_loan(loan_id,db)
    rows=db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id,CollectionActionRecord.action_type.in_(["agent_assignment","collection_call","field_visit"])).order_by(CollectionActionRecord.id.desc()).all()
    return [{"id":x.id,"action":x.action_type,"reference":x.reference,"status":x.status,"created_at":str(x.created_at) if x.created_at else None,"details":json.loads(x.notes or "{}")} for x in rows]
