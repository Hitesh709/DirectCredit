import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord, CustomerJourneyRecord
from .provider_gateway import provider_status, result
from .verification import validate_pan, validate_aadhaar
from .loan_lifecycle import LOAN_STATUSES, LOAN_STAGES, STATUS_TO_STAGE, normalize_status, normalize_stage, transition_error, lifecycle_payload
from .document_service import router as document_router, migrate_document_columns
from .auth_routes import router as auth_router
from .repayment_routes import router as repayment_router
from .customer_profile_routes import router as customer_profile_router
from .auth import get_current_customer

migrate_document_columns()
router = APIRouter(prefix="/api/services", tags=["verification-services"])
router.include_router(document_router)
router.include_router(auth_router)
router.include_router(repayment_router)
router.include_router(customer_profile_router)

@router.get("/status")
def services_status():
    return {"services": provider_status()}

@router.post("/pan/validate")
def pan_validate(pan: str):
    return result("pan", validate_pan(pan))

@router.post("/aadhaar/validate")
def aadhaar_validate(aadhaar: str):
    return result("aadhaar", validate_aadhaar(aadhaar))

@router.get("/loan-lifecycle/contract")
def loan_lifecycle_contract():
    return {"statuses":list(LOAN_STATUSES),"stages":list(LOAN_STAGES),"status_to_stage":STATUS_TO_STAGE}

@router.get("/loans/{loan_id}/lifecycle")
def get_loan_lifecycle(loan_id:int,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    return lifecycle_payload(loan)
