from pathlib import Path
import sys

# Render currently starts this module as `uvicorn main:app` from /backend.
# Make the backend package resolvable so its relative imports work in that mode.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "backend"

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord
from .schemas import CustomerCreate, CustomerOut, CustomerLogin, LoanApplicationCreate, LoanApplicationOut, StatusUpdate, DocumentCreate
from .workflow import assess_amount, build_repayment_schedule
from .profile_service import profile_payload
from .api_services import router as service_router
from .reporting import router as reporting_router
from .audit_routes import router as audit_router
from .auth import hash_password, verify_password, issue_demo_token, get_current_customer
from .migration_runner import migrate_database
from .api_response import error as api_error, public_http_error, request_id
from .audit_service import record_event, audit_request_context
from .production_controls import install_security
app = FastAPI(title="DirectCredit API", version="0.8.0")
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
install_security(app)
@app.middleware("http")
async def correlation_middleware(request:Request,call_next):
    rid=request.headers.get("X-Request-ID") or request_id(); request.state.request_id=rid; response=await call_next(request); response.headers["X-Request-ID"]=rid; return response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request:Request,exc:RequestValidationError):
    fields=[{"field":".".join(str(x) for x in item.get("loc",[]) if x!="body") or "request","message":item.get("msg","Invalid value"),"type":item.get("type","validation_error")} for item in exc.errors()]
    return JSONResponse(status_code=422,content=api_error("VALIDATION_ERROR","One or more request fields are invalid.",details=fields,request_id_value=request.state.request_id))
@app.exception_handler(HTTPException)
async def http_exception_handler(request:Request,exc:HTTPException):
    code,safe_message=public_http_error(exc.status_code); message=safe_message if exc.status_code in {401,403} else str(exc.detail); details=None if exc.status_code in {401,403,404,500} else exc.detail
    return JSONResponse(status_code=exc.status_code,content=api_error(code,message,details=details,request_id_value=request.state.request_id))
@app.exception_handler(Exception)
async def unhandled_exception_handler(request:Request,exc:Exception): return JSONResponse(status_code=500,content=api_error("INTERNAL_ERROR","An unexpected server error occurred.",request_id_value=request.state.request_id))
def customer_public_payload(c:CustomerRecord)->dict:
    return {"id":c.id,"customer_code":c.customer_code or f"CUST{c.id:08d}","login_id":c.login_id,"name":c.name,"pan":c.pan,"mobile":c.mobile,"email":c.email,"address":c.address,"permanent_address":c.permanent_address,"current_city":c.current_city,"gender":c.gender,"business_name":c.business_name,"business_type":c.business_type,"date_of_birth":c.date_of_birth,"aadhaar_masked":c.aadhaar_masked,"marital_status":c.marital_status,"customer_type":c.customer_type,"occupation":c.occupation,"monthly_income":c.monthly_income,"work_experience_years":c.work_experience_years,"years_in_business":c.years_in_business,"average_bank_balance":c.average_bank_balance,"primary_bank":c.primary_bank,"cibil_score":c.cibil_score,"foir":c.foir,"existing_emi":c.existing_emi,"dependents":c.dependents,"residence_ownership":c.residence_ownership,"residence_since":c.residence_since,"ownership_proof_name":c.ownership_proof_name,"ownership_proof_status":c.ownership_proof_status,"kyc_status":c.kyc_status,"email_verified":c.email_verified,"selfie_status":c.selfie_status}
def assert_customer_access(customer_id:int,claims:dict):
    if int(claims.get("user_id",-1))!=int(customer_id): raise HTTPException(403,"Customer session does not match this customer")
def audit_http(request:Request,db:Session,*,action:str,entity_type:str,entity_id=None,customer_id=None,loan_id=None,claims=None,outcome="success",reason_code=None,details=None):
    ctx=audit_request_context(request,claims); record_event(db,action=action,entity_type=entity_type,entity_id=entity_id,customer_id=customer_id,loan_id=loan_id,outcome=outcome,reason_code=reason_code,details=details,**ctx)
@app.on_event("startup")
def startup(): migrate_database()
app.include_router(service_router); app.include_router(reporting_router); app.include_router(audit_router)
@app.get("/")
def root(): return {"application":"DirectCredit","status":"online","mode":"production-ready","api_version":"0.8.0"}
@app.get("/health")
def health(db:Session=Depends(get_db)): db.execute(func.count(CustomerRecord.id)); return {"status":"healthy","database":"connected"}
@app.get("/api/version")
def version(): return {"name":"DirectCredit API","version":"0.8.0"}
@app.post("/api/customer/login")
def customer_login(payload:CustomerLogin,request:Request,db:Session=Depends(get_db)):
    login_id=payload.login_id.strip(); customer=db.query(CustomerRecord).filter(CustomerRecord.login_id==login_id).first()
    if customer:
        if not customer.password_hash:
            if os.getenv("ALLOW_DEMO_CREDENTIAL_CLAIM","true").lower() not in {"1","true","yes"}: raise HTTPException(401,"Customer credentials are not configured")
            customer.password_hash=hash_password(payload.password); db.commit(); db.refresh(customer)
        elif not verify_password(payload.password,customer.password_hash): audit_http(request,db,action="CUSTOMER_LOGIN",entity_type="customer",entity_id=customer.id,customer_id=customer.id,outcome="failure",reason_code="INVALID_CREDENTIALS"); db.commit(); raise HTTPException(401,"Invalid customer ID or password")
    else:
        customer=CustomerRecord(login_id=login_id,password_hash=hash_password(payload.password),name="",customer_type="Individual",occupation="",monthly_income=0,residence_ownership="",ownership_proof_status="pending",kyc_status="pending"); db.add(customer); db.commit(); db.refresh(customer); customer.customer_code=f"CUST{customer.id:08d}"; db.commit(); db.refresh(customer)
    audit_http(request,db,action="CUSTOMER_LOGIN",entity_type="customer",entity_id=customer.id,customer_id=customer.id,details={"login_id":login_id}); db.commit(); return {"access_token":issue_demo_token(customer.id,"customer"),"token_type":"bearer","customer":customer_public_payload(customer)}
@app.get("/api/customer/me")
def customer_me(claims:dict=Depends(get_current_customer),db:Session=Depends(get_db)):
    customer=db.get(CustomerRecord,int(claims["user_id"]))
    if not customer: raise HTTPException(404,"Customer not found")
    return customer_public_payload(customer)
@app.post("/api/customers",response_model=CustomerOut)
def create_customer(payload:CustomerCreate,request:Request,db:Session=Depends(get_db)):
    c=CustomerRecord(**payload.model_dump()); db.add(c); db.commit(); db.refresh(c)
    if not c.customer_code: c.customer_code=f"CUST{c.id:08d}"; db.commit(); db.refresh(c)
    audit_http(request,db,action="CUSTOMER_CREATED",entity_type="customer",entity_id=c.id,customer_id=c.id,details={"customer_code":c.customer_code}); db.commit(); return c
@app.get("/api/customers",response_model=list[CustomerOut])
def list_customers(db:Session=Depends(get_db)): return db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()
@app.get("/api/customers/{customer_id}",response_model=CustomerOut)
def get_customer(customer_id:int,db:Session=Depends(get_db)):
    c=db.get(CustomerRecord,customer_id)
    if not c: raise HTTPException(404,"Customer not found")
    return c
@app.patch("/api/customers/{customer_id}/profile",response_model=CustomerOut)
def update_customer_profile(customer_id:int,payload:CustomerCreate,request:Request,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); c=db.get(CustomerRecord,customer_id)
    if not c: raise HTTPException(404,"Customer not found")
    for key,value in payload.model_dump(exclude_unset=True).items():
        if key=="pan" and value is None: continue
        if key!="name" or str(value or "").strip(): setattr(c,key,value)
    db.commit(); db.refresh(c); audit_http(request,db,action="CUSTOMER_PROFILE_UPDATED",entity_type="customer",entity_id=c.id,customer_id=c.id,claims=claims); db.commit(); return c
@app.get("/api/customers/{customer_id}/profile")
def customer_profile(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data
@app.get("/api/customers/{customer_id}/bank-analysis")
def bank_analysis(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["bank_analysis"]
@app.get("/api/customers/{customer_id}/kyc-employment")
def kyc_employment(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["kyc_employment"]
@app.get("/api/customers/{customer_id}/risk-score")
def risk_score(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["risk_score"]
@app.get("/api/customers/{customer_id}/loan-trend")
def loan_trend(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims); data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["loan_trend"]
@app.get("/api/customers/{customer_id}/loans")
def customer_loans(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims)
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    return db.query(LoanRecord).filter(LoanRecord.customer_id==customer_id).order_by(LoanRecord.id.desc()).all()
@app.post("/api/loans",response_model=LoanApplicationOut)
def create_loan(payload:LoanApplicationCreate,request:Request,db:Session=Depends(get_db)):
    if not db.get(CustomerRecord,payload.customer_id): raise HTTPException(404,"Customer not found")
    r=assess_amount(float(payload.requested_amount)); loan=LoanRecord(customer_id=payload.customer_id,requested_amount=float(payload.requested_amount),eligible_amount=r["eligible_amount"],monthly_emi=round(r["eligible_amount"]/payload.tenure_months,2),tenure_months=payload.tenure_months,product=payload.product,status="assessment",current_stage="ASSESSMENT"); db.add(loan); db.commit(); db.refresh(loan); audit_http(request,db,action="LOAN_APPLICATION_CREATED",entity_type="loan_application",entity_id=loan.id,customer_id=loan.customer_id,loan_id=loan.id,details={"requested_amount":loan.requested_amount,"product":loan.product,"tenure_months":loan.tenure_months}); db.commit(); return loan
@app.get("/api/loans/{loan_id}",response_model=LoanApplicationOut)
def get_loan(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    assert_customer_access(loan.customer_id,claims); return loan
@app.patch("/api/loans/{loan_id}/status",response_model=LoanApplicationOut)
def update_loan_status(loan_id:int,payload:StatusUpdate,request:Request,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    old_status=loan.status; loan.status=payload.status
    if payload.current_stage: loan.current_stage=payload.current_stage
    db.commit(); db.refresh(loan); audit_http(request,db,action="LOAN_STATUS_UPDATED",entity_type="loan_application",entity_id=loan.id,customer_id=loan.customer_id,loan_id=loan.id,details={"from_status":old_status,"to_status":loan.status,"current_stage":loan.current_stage}); db.commit(); return loan
@app.post("/api/loans/{loan_id}/repayment-schedule")
def create_schedule(loan_id:int,request:Request,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan not found")
    amount=loan.sanctioned_amount or loan.eligible_amount; db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).delete(); schedule=build_repayment_schedule(loan_id,amount,loan.tenure_months)
    for item in schedule: db.add(RepaymentRecord(**item))
    loan.outstanding_amount=amount; db.commit(); audit_http(request,db,action="REPAYMENT_SCHEDULE_CREATED",entity_type="loan_application",entity_id=loan.id,customer_id=loan.customer_id,loan_id=loan.id,details={"installments":len(schedule),"amount":amount}); db.commit(); return schedule
@app.get("/api/loans/{loan_id}/repayments")
def repayments(loan_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    assert_customer_access(loan.customer_id,claims); return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()
@app.post("/api/documents")
def create_document(payload:DocumentCreate,request:Request,db:Session=Depends(get_db)):
    if not db.get(CustomerRecord,payload.customer_id): raise HTTPException(404,"Customer not found")
    d=DocumentRecord(**payload.model_dump()); db.add(d); db.commit(); db.refresh(d); audit_http(request,db,action="DOCUMENT_RECEIVED",entity_type="document",entity_id=d.id,customer_id=d.customer_id,loan_id=d.loan_id,details={"document_type":d.document_type,"document_role":d.document_role,"verification_status":d.verification_status}); db.commit(); return {"id":d.id,"status":"received","verification_status":d.verification_status}
@app.get("/api/customers/{customer_id}/documents")
def customer_documents(customer_id:int,db:Session=Depends(get_db),claims:dict=Depends(get_current_customer)):
    assert_customer_access(customer_id,claims)
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    return db.query(DocumentRecord).filter(DocumentRecord.customer_id==customer_id).order_by(DocumentRecord.id.desc()).all()
@app.get("/api/admin/loans")
def admin_loans(db:Session=Depends(get_db)): return db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()
@app.get("/api/admin/dashboard")
def admin_dashboard(db:Session=Depends(get_db)):
    loans=db.query(LoanRecord).all(); return {"applications":len(loans),"assessment":sum(x.status=="assessment" for x in loans),"sanctioned":sum(x.status=="sanctioned" for x in loans),"disbursed":sum(x.status=="disbursed" for x in loans),"repayment":sum(x.status=="repayment" for x in loans),"overdue":sum(x.status=="overdue" for x in loans),"repaid":sum(x.status=="repaid" for x in loans)}
