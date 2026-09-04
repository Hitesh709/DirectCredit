import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, CustomerJourneyRecord
from .provider_gateway import provider_status, result
from .verification import validate_pan, validate_aadhaar
from .loan_lifecycle import LOAN_STATUSES, LOAN_STAGES, STATUS_TO_STAGE, normalize_status, normalize_stage, lifecycle_payload
from .document_service import router as document_router, migrate_document_columns
from .auth_routes import router as auth_router
from .repayment_routes import router as repayment_router
from .customer_profile_routes import router as customer_profile_router
from .auth import get_current_customer
from .loan_request_routes import router as loan_request_router
from .eligibility_routes import router as eligibility_router
from .servicing_routes import router as servicing_router
from .analytics_routes import router as analytics_router
from .report_routes_v2 import router as report_router
from .phase_76_100 import router as phase_76_100_router
migrate_document_columns()
router=APIRouter(prefix="/api/services",tags=["verification-services"])
for child in (document_router,auth_router,repayment_router,customer_profile_router,loan_request_router,eligibility_router,servicing_router,analytics_router,report_router,phase_76_100_router): router.include_router(child)
@router.get("/status")
def services_status(): return {"services":provider_status()}
@router.post("/pan/validate")
def pan_validate(pan:str): return result("pan",validate_pan(pan))
@router.post("/aadhaar/validate")
def aadhaar_validate(aadhaar:str): return result("aadhaar",validate_aadhaar(aadhaar))
@router.get("/loan-lifecycle/contract")
def loan_lifecycle_contract(): return {"statuses":list(LOAN_STATUSES),"stages":list(LOAN_STAGES),"status_to_stage":STATUS_TO_STAGE}
@router.get("/loans/{loan_id}/lifecycle")
def get_loan_lifecycle(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    if int(loan.customer_id)!=int(claims.get("user_id",-1)): raise HTTPException(403,"Loan access forbidden")
    return lifecycle_payload(loan)
@router.post("/loans/{loan_id}/lifecycle")
def transition_loan_lifecycle(loan_id:int,payload:dict,db:Session=Depends(get_db)): raise HTTPException(403,"Direct lifecycle transition is disabled; use authorized admin operations")
@router.post("/customers/{customer_id}/journey")
def sync_customer_journey(customer_id:int,payload:dict,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    if int(claims.get("user_id",-1))!=int(customer_id): raise HTTPException(403,"Customer session does not match customer")
    customer=db.get(CustomerRecord,customer_id)
    if not customer: raise HTTPException(404,"Customer not found")
    c=payload.get("customer") or {}
    for key in ["name","pan","mobile","email","address","permanent_address","current_city","gender","business_name","business_type","date_of_birth","aadhaar_masked","marital_status","occupation","monthly_income","work_experience_years","years_in_business","average_bank_balance","primary_bank","cibil_score","foir","existing_emi","dependents","kyc_status","email_verified","selfie_status"]:
        if c.get(key) is not None and hasattr(customer,key): setattr(customer,key,c[key])
    lp=payload.get("loan") or {}; loan_id=lp.get("id"); loan=db.get(LoanRecord,int(loan_id)) if loan_id is not None and str(loan_id).isdigit() else None
    if loan is None: loan=db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).first()
    if loan is None and lp.get("requested_amount") is not None:
        requested=float(lp["requested_amount"])
        if requested<5000 or requested>15000: raise HTTPException(422,"Loan amount must be between ₹5,000 and ₹15,000")
        loan=LoanRecord(customer_id=customer_id,requested_amount=requested,status="assessment",current_stage="ASSESSMENT"); db.add(loan); db.flush()
    if loan is not None:
        if loan.customer_id!=customer_id: raise HTTPException(403,"Loan does not belong to this customer")
        for key in ["requested_amount","interest_rate","tenure_months","product"]:
            if key in lp and lp[key] is not None: setattr(loan,key,lp[key])
        if "status" in lp or "current_stage" in lp: raise HTTPException(403,"Customer cannot change loan lifecycle")
    for index,step in enumerate(payload.get("steps") or [],1):
        key=str(step.get("key") or f"step_{index}"); record=db.query(CustomerJourneyRecord).filter(CustomerJourneyRecord.customer_id==customer_id,CustomerJourneyRecord.step_key==key).first()
        if not record: record=CustomerJourneyRecord(customer_id=customer_id,step_key=key); db.add(record)
        record.loan_id=loan.id if loan else None; record.step_number=int(step.get("step_number") or index); record.step_label=step.get("label") or key; record.status=step.get("status") or "pending"; record.details=json.dumps(step.get("details") or {},ensure_ascii=False)
    db.commit(); return {"status":"synced","customer_id":customer_id,"loan_id":loan.id if loan else None,"canonical_status":normalize_status(loan.status) if loan else None,"canonical_stage":normalize_stage(loan.current_stage,loan.status) if loan else None,"journey_steps":len(payload.get("steps") or [])}
@router.get("/customers/{customer_id}/journey")
def get_customer_journey(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    if int(claims.get("user_id",-1))!=int(customer_id): raise HTTPException(403,"Customer session does not match customer")
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    rows=db.query(CustomerJourneyRecord).filter(CustomerJourneyRecord.customer_id==customer_id).order_by(CustomerJourneyRecord.step_number).all(); return [{"step_key":r.step_key,"step_number":r.step_number,"step_label":r.step_label,"status":r.status,"details":json.loads(r.details or "{}")} for r in rows]
