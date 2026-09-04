from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_customer
from .db_models import CustomerRecord, LoanRecord
from .mbl_scorecard import calculate, VERSION, MAX_POINTS
from .eligibility_engine import MIN_LOAN, MAX_LOAN
router=APIRouter(prefix="/eligibility",tags=["eligibility"])
class LoanRequest(BaseModel):
    amount:int=Field(ge=MIN_LOAN,le=MAX_LOAN); tenure_months:int=Field(ge=1,le=36); product:str="MBL"
class AssessmentInput(BaseModel):
    # Raw evidence inputs are accepted here; the score is always calculated server-side.
    ownership_proof:str=""; business_owned:bool=False; residence_owned:bool=False
    business_geography:str=""; age:int=0; cibil_unsecured_enquiries_30d:int=0
    cibil_repayment:str=""; cibil_adverse_last_3y:bool=False; unsecured_loans_50k_plus:int=0
    avg_monthly_bank_credits:float=0; bank_bounces_3m:int=0; aqb:float=0; ecs_returns_12m:int=0
    business_type:str=""; business_vintage_years:float=0; business_stock:float=0
    monthly_emi_obligation:float=0; foir:float=0; trade_validations:int=0; gst_years:float=0
    gstr3b_avg_monthly_turnover:float=0; itr_income:float=0; mobile_stability_years:float=0
    monthly_income:float|None=None; existing_emi:float|None=None
    bureau_score:float|None=None; banking_score:float|None=None

def owns(customer_id,claims):
    if int(claims.get("user_id",-1))!=int(customer_id): raise HTTPException(403,"customer_scope_forbidden")

@router.post("/{customer_id}/request")
def create_or_update_request(customer_id:int,body:LoanRequest,db:Session=Depends(get_db),current=Depends(get_current_customer)):
    owns(customer_id,current); customer=db.get(CustomerRecord,customer_id)
    if not customer: raise HTTPException(404,"customer_not_found")
    loan=db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan: loan=LoanRecord(customer_id=customer_id,requested_amount=body.amount,tenure_months=body.tenure_months,product=body.product,status="draft",current_stage="PAN"); db.add(loan)
    else: loan.requested_amount=body.amount; loan.tenure_months=body.tenure_months; loan.product=body.product
    db.commit(); db.refresh(loan); return {"loan_id":loan.id,"customer_id":customer_id,"requested_amount":loan.requested_amount,"tenure_months":loan.tenure_months,"product":loan.product,"status":loan.status}

@router.post("/{customer_id}/assess")
def assess_customer(customer_id:int,body:AssessmentInput,db:Session=Depends(get_db),current=Depends(get_current_customer)):
    owns(customer_id,current); loan=db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan: raise HTTPException(404,"loan_request_not_found")
    inputs=body.model_dump(exclude_none=True)
    result=calculate(inputs)
    # Persist only the decision-facing fields available on the canonical loan record.
    loan.status="sanctioned" if result.decision=="APPROVE" else "assessment"
    loan.current_stage="SANCTION" if result.decision=="APPROVE" else "ASSESSMENT"
    loan.eligible_amount=int(round(float(loan.requested_amount or 0)*result.approval_percent/100))
    db.commit()
    payload=result.payload(); payload.update({"loan_id":loan.id,"customer_id":customer_id,"requested_amount":loan.requested_amount,"scorecard_version":VERSION,"max_score":MAX_POINTS})
    return payload

@router.get("/{customer_id}")
def get_eligibility(customer_id:int,db:Session=Depends(get_db),current=Depends(get_current_customer)):
    owns(customer_id,current); loan=db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan: return {"loan":None,"decision":"NOT_ASSESSED","scorecard_version":VERSION}
    return {"loan_id":loan.id,"customer_id":customer_id,"requested_amount":loan.requested_amount,"eligible_amount":loan.eligible_amount,"tenure_months":loan.tenure_months,"status":loan.status,"decision":"ASSESSMENT_RECORDED","scorecard_version":VERSION}
