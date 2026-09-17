import json
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, CollectionActionRecord, CustomerPreferenceRecord
from .admin_auth import get_current_admin
from .phase2i_collections import dpd
from .phase2j_collections_intelligence import latest_ptp
from .phase2k_communication import PHASE2K_VERSION, communication_plan, communication_contract

router = APIRouter(prefix="/api/v1/communications", tags=["phase-2k-communications"])

class CommunicationRequest(BaseModel):
    event: str = Field(min_length=3, max_length=40)
    channel: str | None = Field(default=None, max_length=30)
    reference: str = Field(min_length=3, max_length=160)
    scheduled_for: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)

class DeliveryCallback(BaseModel):
    reference: str = Field(min_length=3, max_length=160)
    status: str = Field(min_length=2, max_length=30)
    provider_reference: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=500)

def _loan(loan_id, db):
    loan=db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    customer=db.get(CustomerRecord, loan.customer_id)
    if not customer: raise HTTPException(404,"customer_not_found")
    return loan, customer

def _prefs(customer_id, db):
    row=db.query(CustomerPreferenceRecord).filter(CustomerPreferenceRecord.customer_id==customer_id).first()
    if not row: return {}
    return {"sms":bool(row.sms),"whatsapp":bool(row.whatsapp),"email":bool(row.email),"phone":bool(row.phone),"transactional_only":bool(row.transactional_only)}

def _rows(loan_id, db): return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()

def _loan_dpd(rows):
    return max([dpd(r.due_date,r.paid_amount,r.due_amount) for r in rows] or [0])

@router.get("/contract")
def contract(): return communication_contract()

@router.get("/loan/{loan_id}/plan")
def plan(loan_id:int, event:str, db:Session=Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer=_loan(loan_id,db); rows=_rows(loan_id,db); ptp=latest_ptp(db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id).all())
    p=communication_plan(event,_loan_dpd(rows),_prefs(customer.id,db),bool(ptp))
    return {"loan_id":loan_id,"customer_id":customer.id,"event":p.event,"template":p.template,"channels":list(p.channels),"reason":p.reason,"engine_version":PHASE2K_VERSION}

@router.post("/loan/{loan_id}/schedule")
def schedule(loan_id:int, body:CommunicationRequest, db:Session=Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer=_loan(loan_id,db)
    if db.query(CollectionActionRecord).filter(CollectionActionRecord.reference==body.reference).first(): raise HTTPException(409,"communication_reference_already_exists")
    rows=_rows(loan_id,db); ptp=latest_ptp(db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id).all())
    p=communication_plan(body.event,_loan_dpd(rows),_prefs(customer.id,db),bool(ptp))
    channel=(body.channel or (p.channels[0] if p.channels else "")).lower()
    if channel not in p.channels: raise HTTPException(409,"channel_not_enabled_for_customer")
    notes={"event":p.event,"template":p.template,"channel":channel,"scheduled_for":body.scheduled_for or datetime.utcnow().isoformat(),"reason":p.reason,"notes":body.notes,"engine_version":PHASE2K_VERSION}
    row=CollectionActionRecord(loan_id=loan.id,customer_id=customer.id,action_type="communication",amount=0,reference=body.reference,status="scheduled",notes=json.dumps(notes,ensure_ascii=False))
    db.add(row); db.commit(); db.refresh(row)
    return {"communication_id":row.id,"loan_id":loan.id,"event":p.event,"template":p.template,"channel":channel,"status":"scheduled","scheduled_for":notes["scheduled_for"]}

@router.post("/loan/{loan_id}/delivery-callback")
def delivery_callback(loan_id:int, body:DeliveryCallback, db:Session=Depends(get_db), admin=Depends(get_current_admin)):
    loan,_=_loan(loan_id,db)
    row=db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id,CollectionActionRecord.reference==body.reference,CollectionActionRecord.action_type=="communication").first()
    if not row: raise HTTPException(404,"communication_not_found")
    status=body.status.strip().upper()
    mapping={"DELIVERED":"delivered","SENT":"sent","FAILED":"failed","READ":"read"}
    if status not in mapping: raise HTTPException(422,"unsupported_delivery_status")
    row.status=mapping[status]; row.notes=(row.notes or "")+" | provider="+(body.provider_reference or "")+(" | reason="+body.reason if body.reason else "")
    db.commit()
    return {"communication_id":row.id,"status":row.status}

@router.get("/loan/{loan_id}/history")
def history(loan_id:int, db:Session=Depends(get_db), admin=Depends(get_current_admin)):
    loan,_=_loan(loan_id,db)
    rows=db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id,CollectionActionRecord.action_type=="communication").order_by(CollectionActionRecord.id.desc()).all()
    return [{"id":x.id,"reference":x.reference,"status":x.status,"created_at":str(x.created_at) if x.created_at else None,"details":json.loads(x.notes or "{}")} for x in rows]
