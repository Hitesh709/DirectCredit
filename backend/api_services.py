import json
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord, CustomerJourneyRecord
from .provider_gateway import provider_status, result
from .verification import validate_pan, validate_aadhaar
from .loan_lifecycle import LOAN_STATUSES, LOAN_STAGES, STATUS_TO_STAGE, normalize_status, normalize_stage, transition_error, lifecycle_payload
from .document_service import router as document_router, migrate_document_columns
from .auth_routes import router as auth_router

migrate_document_columns()
router = APIRouter(prefix="/api/services", tags=["verification-services"])
router.include_router(document_router)
# Task 5 authentication is mounted through the main application router.
router.include_router(auth_router)

@router.get("/status")
def services_status(): return {"services": provider_status()}
@router.post("/pan/validate")
def pan_validate(pan: str): return result("pan", validate_pan(pan))
@router.post("/aadhaar/validate")
def aadhaar_validate(aadhaar: str): return result("aadhaar", validate_aadhaar(aadhaar))
@router.get("/loan-lifecycle/contract")
def loan_lifecycle_contract(): return {"statuses":list(LOAN_STATUSES),"stages":list(LOAN_STAGES),"status_to_stage":STATUS_TO_STAGE}
@router.get("/loans/{loan_id}/lifecycle")
def get_loan_lifecycle(loan_id:int,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    return lifecycle_payload(loan)
@router.post("/loans/{loan_id}/lifecycle")
def transition_loan_lifecycle(loan_id:int,payload:dict,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    try: current=normalize_status(loan.status); target=normalize_status(payload.get("status")); stage=normalize_stage(payload.get("current_stage"),target)
    except ValueError as exc: raise HTTPException(422,str(exc))
    error=transition_error(current,target)
    if error: raise HTTPException(409,error)
    loan.status=target; loan.current_stage=stage; db.commit(); db.refresh(loan); return lifecycle_payload(loan)

@router.post("/customers/{customer_id}/journey")
def sync_customer_journey(customer_id:int,payload:dict,db:Session=Depends(get_db)):
    customer=db.get(CustomerRecord,customer_id)
    if not customer: raise HTTPException(404,"Customer not found")
    c=payload.get("customer") or {}
    fields={"name":c.get("name"),"pan":c.get("pan"),"mobile":c.get("mobile"),"email":c.get("email"),"address":c.get("address"),"permanent_address":c.get("permanent_address"),"current_city":c.get("current_city"),"gender":c.get("gender"),"business_name":c.get("business_name"),"business_type":c.get("business_type"),"date_of_birth":c.get("date_of_birth"),"aadhaar_masked":c.get("aadhaar_masked"),"marital_status":c.get("marital_status"),"occupation":c.get("occupation"),"monthly_income":c.get("monthly_income",0),"work_experience_years":c.get("work_experience_years",0),"years_in_business":c.get("years_in_business",0),"average_bank_balance":c.get("average_bank_balance",0),"primary_bank":c.get("primary_bank"),"cibil_score":c.get("cibil_score",0),"foir":c.get("foir",0),"existing_emi":c.get("existing_emi",0),"dependents":c.get("dependents",0),"kyc_status":c.get("kyc_status","pending"),"email_verified":c.get("email_verified","pending"),"selfie_status":c.get("selfie_status","pending")}
    for key,value in fields.items():
        if value is not None and hasattr(customer,key): setattr(customer,key,value)
    lp=payload.get("loan") or {}; loan=db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).first(); requested=float(lp.get("requested_amount") or lp.get("sanctioned_amount") or 1)
    if not loan: loan=LoanRecord(customer_id=customer_id,requested_amount=requested); db.add(loan); db.flush()
    for key in ["requested_amount","eligible_amount","monthly_emi","sanctioned_amount","disbursed_amount","outstanding_amount","interest_rate","tenure_months","product"]:
        if key in lp and lp[key] is not None and hasattr(loan,key): setattr(loan,key,lp[key])
    if "status" in lp and lp["status"] is not None:
        try: loan.status=normalize_status(lp["status"])
        except ValueError as exc: raise HTTPException(422,str(exc))
    if "current_stage" in lp and lp["current_stage"] is not None:
        try: loan.current_stage=normalize_stage(lp["current_stage"],loan.status)
        except ValueError as exc: raise HTTPException(422,str(exc))
    elif loan.status: loan.current_stage=STATUS_TO_STAGE[normalize_status(loan.status)]
    if "disbursement_details" in lp: loan.disbursement_details=json.dumps(lp["disbursement_details"],ensure_ascii=False)
    steps=payload.get("steps") or []
    for index,step in enumerate(steps,1):
        key=str(step.get("key") or f"step_{index}"); record=db.query(CustomerJourneyRecord).filter(CustomerJourneyRecord.customer_id==customer_id,CustomerJourneyRecord.step_key==key).first()
        if not record: record=CustomerJourneyRecord(customer_id=customer_id,step_key=key); db.add(record)
        record.loan_id=loan.id; record.step_number=int(step.get("step_number") or index); record.step_label=step.get("label") or key; record.status=step.get("status") or "pending"; record.details=json.dumps(step.get("details") or {},ensure_ascii=False)
    for doc in payload.get("documents") or []:
        fn=str(doc.get("file_name") or doc.get("name") or "document"); dt=str(doc.get("document_type") or doc.get("type") or "Other Document"); existing=db.query(DocumentRecord).filter(DocumentRecord.customer_id==customer_id,DocumentRecord.file_name==fn,DocumentRecord.document_type==dt).first()
        if not existing: existing=DocumentRecord(customer_id=customer_id,loan_id=loan.id,document_type=dt,file_name=fn); db.add(existing)
        existing.loan_id=loan.id; existing.verification_status=doc.get("verification_status") or doc.get("status") or existing.verification_status; existing.storage_key=doc.get("storage_key") or existing.storage_key
    for item in payload.get("repayments") or []:
        installment=int(item.get("installment") or 0)
        if not installment: continue
        repayment=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan.id,RepaymentRecord.installment==installment).first()
        if not repayment: repayment=RepaymentRecord(loan_id=loan.id,installment=installment,due_date=str(item.get("due_date") or ""),due_amount=float(item.get("due_amount") or 0)); db.add(repayment)
        repayment.due_date=str(item.get("due_date") or repayment.due_date); repayment.due_amount=float(item.get("due_amount") or repayment.due_amount or 0); repayment.paid_amount=float(item.get("paid_amount") or 0); repayment.status=item.get("status") or repayment.status
    db.commit(); return {"status":"synced","customer_id":customer_id,"loan_id":loan.id,"canonical_status":normalize_status(loan.status),"canonical_stage":normalize_stage(loan.current_stage,loan.status),"journey_steps":len(steps),"documents":len(payload.get("documents") or []),"repayments":len(payload.get("repayments") or [])}

@router.get("/customers/{customer_id}/journey")
def get_customer_journey(customer_id:int,db:Session=Depends(get_db)):
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    rows=db.query(CustomerJourneyRecord).filter(CustomerJourneyRecord.customer_id==customer_id).order_by(CustomerJourneyRecord.step_number).all()
    return [{"step_key":r.step_key,"step_number":r.step_number,"step_label":r.step_label,"status":r.status,"details":json.loads(r.details or "{}")} for r in rows]
