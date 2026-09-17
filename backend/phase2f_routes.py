"""Phase 2F customer-scoped e-sign and e-mandate orchestration APIs."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .auth import get_current_customer
from .database import get_db
from .db_models import AuditEventRecord, CustomerConsentRecord, CustomerEventRecord, LoanRecord
from .phase2e_offer_engine import offer_is_active, parse_offer
from .phase2f_execution import (PHASE2F_VERSION, build_esign_request, build_mandate_request,
                                execution_contract, provider_config, verify_callback)

router = APIRouter(prefix="/api/v1/execution", tags=["loan-execution"])

def _owner(customer_id, claims):
    if int(claims.get("user_id", -1)) != int(customer_id): raise HTTPException(403, "customer_scope_forbidden")

def _loan(db, customer_id, loan_id):
    loan=db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    if int(loan.customer_id)!=int(customer_id): raise HTTPException(403,"loan_access_forbidden")
    return loan

def _payload(loan):
    try: p=json.loads(loan.disbursement_details or "{}")
    except (TypeError,ValueError): p={}
    return p

def _save(loan,p): loan.disbursement_details=json.dumps(p,ensure_ascii=False)

def _audit(db,customer_id,loan_id,action,outcome,reason,details):
    db.add(AuditEventRecord(event_id=str(uuid.uuid4()),actor_type="customer",actor_id=str(customer_id),action=action,
      entity_type="loan_execution",entity_id=str(loan_id),customer_id=customer_id,loan_id=loan_id,source="phase2f",
      outcome=outcome,reason_code=reason,details=json.dumps(details,ensure_ascii=False)))

@router.get("/contract")
def contract(): return execution_contract()

@router.get("/{customer_id}/{loan_id}/status")
def status(customer_id:int,loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    _owner(customer_id,claims); loan=_loan(db,customer_id,loan_id); p=_payload(loan)
    return {"phase":PHASE2F_VERSION,"loan_status":loan.status,"stage":loan.current_stage,
            "esign":p.get("esign",{"status":"NOT_STARTED"}),"mandate":p.get("mandate",{"status":"NOT_STARTED"})}

@router.post("/{customer_id}/{loan_id}/esign/start")
def esign_start(customer_id:int,loan_id:int,agreement_version:str="KFS-AGREEMENT-v1",db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    _owner(customer_id,claims); loan=_loan(db,customer_id,loan_id); offer=parse_offer(loan)
    if not offer or offer.get("offer_status")!="ACCEPTED": raise HTTPException(409,"accepted_offer_required")
    p=_payload(loan); existing=p.get("esign")
    if existing and existing.get("status") in ("PENDING","SIGNED"): return {"status":"existing_request","esign":existing}
    req=build_esign_request(customer_id=customer_id,loan_id=loan_id,offer_id=offer["offer_id"],agreement_version=agreement_version)
    p["esign"]=req; _save(loan,p)
    if req["status"]=="PENDING": loan.status="esign_pending"; loan.current_stage="E_SIGN"
    db.add(CustomerEventRecord(customer_id=customer_id,event_type="ESIGN_REQUESTED",event_status="completed",source="phase2f",actor_type="customer",actor_id=str(customer_id),details=json.dumps(req)))
    _audit(db,customer_id,loan_id,"esign_requested","success",req.get("reason","esign_request_created"),req); db.commit()
    return {"status":"created","esign":req}

@router.post("/{customer_id}/{loan_id}/esign/callback")
def esign_callback(customer_id:int,loan_id:int,status_value:str,request_id:str|None=None,signature:str|None=Header(default=None),db:Session=Depends(get_db)):
    loan=_loan(db,customer_id,loan_id); secret=__import__('os').getenv("DC_ESIGN_CALLBACK_SECRET","")
    body=json.dumps({"customer_id":customer_id,"loan_id":loan_id,"status":status_value,"request_id":request_id},sort_keys=True)
    if not verify_callback(body,signature or "",secret): raise HTTPException(401,"invalid_callback_signature")
    if status_value.upper() not in ("SIGNED","FAILED","EXPIRED"): raise HTTPException(422,"unsupported_esign_status")
    p=_payload(loan); req=p.get("esign",{})
    if request_id and req.get("request_id") and request_id!=req["request_id"]: raise HTTPException(409,"request_id_mismatch")
    req["status"]=status_value.upper(); req["completed_at"]=datetime.now(timezone.utc).isoformat(); p["esign"]=req; _save(loan,p)
    if req["status"]=="SIGNED": loan.status="esigned"; loan.current_stage="E_SIGN"
    else: loan.status="customer_approved"; loan.current_stage="CUSTOMER_APPROVAL"
    _audit(db,customer_id,loan_id,"esign_callback","success","provider_callback",req); db.commit()
    return {"status":"processed","esign":req,"loan_status":loan.status}

@router.post("/{customer_id}/{loan_id}/mandate/start")
def mandate_start(customer_id:int,loan_id:int,mandate_type:str="UPI_AUTOPAY",db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    _owner(customer_id,claims); loan=_loan(db,customer_id,loan_id); offer=parse_offer(loan)
    if not offer or offer.get("offer_status")!="ACCEPTED": raise HTTPException(409,"accepted_offer_required")
    p=_payload(loan); esign=p.get("esign",{})
    if esign.get("status")!="SIGNED": raise HTTPException(409,"completed_esign_required")
    consent=db.query(CustomerConsentRecord).filter(CustomerConsentRecord.customer_id==customer_id,CustomerConsentRecord.accepted==True,CustomerConsentRecord.withdrawn_at==None).all()
    if not consent: raise HTTPException(409,"active_customer_consent_required")
    existing=p.get("mandate")
    if existing and existing.get("status") in ("PENDING","ACTIVE"): return {"status":"existing_request","mandate":existing}
    req=build_mandate_request(customer_id=customer_id,loan_id=loan_id,offer_id=offer["offer_id"],emi=float(loan.monthly_emi or offer.get("emi",0)),requested_amount=float(loan.requested_amount or 0),mandate_type=mandate_type)
    p["mandate"]=req; _save(loan,p)
    if req["status"]=="PENDING": loan.status="mandate_pending"; loan.current_stage="E_MANDATE"
    db.add(CustomerEventRecord(customer_id=customer_id,event_type="MANDATE_REQUESTED",event_status="completed",source="phase2f",actor_type="customer",actor_id=str(customer_id),details=json.dumps(req)))
    _audit(db,customer_id,loan_id,"mandate_requested","success",req.get("reason","mandate_request_created"),req); db.commit()
    return {"status":"created","mandate":req}

@router.post("/{customer_id}/{loan_id}/mandate/callback")
def mandate_callback(customer_id:int,loan_id:int,status_value:str,request_id:str|None=None,signature:str|None=Header(default=None),db:Session=Depends(get_db)):
    loan=_loan(db,customer_id,loan_id); secret=__import__('os').getenv("DC_MANDATE_CALLBACK_SECRET","")
    body=json.dumps({"customer_id":customer_id,"loan_id":loan_id,"status":status_value,"request_id":request_id},sort_keys=True)
    if not verify_callback(body,signature or "",secret): raise HTTPException(401,"invalid_callback_signature")
    if status_value.upper() not in ("ACTIVE","FAILED","CANCELLED"): raise HTTPException(422,"unsupported_mandate_status")
    p=_payload(loan); req=p.get("mandate",{})
    if request_id and req.get("request_id") and request_id!=req["request_id"]: raise HTTPException(409,"request_id_mismatch")
    req["status"]=status_value.upper(); req["updated_at"]=datetime.now(timezone.utc).isoformat(); p["mandate"]=req; _save(loan,p)
    if req["status"]=="ACTIVE": loan.status="disbursement_pending"; loan.current_stage="DISBURSEMENT"
    else: loan.status="esigned"; loan.current_stage="E_SIGN"
    _audit(db,customer_id,loan_id,"mandate_callback","success","provider_callback",req); db.commit()
    return {"status":"processed","mandate":req,"loan_status":loan.status}
