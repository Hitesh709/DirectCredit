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
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
install_security(app)
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or request_id(); request.state.request_id = rid
    response = await call_next(request); response.headers["X-Request-ID"] = rid; return response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields=[{"field":".".join(str(x) for x in item.get("loc",[]) if x!="body") or "request","message":item.get("msg","Invalid value"),"type":item.get("type","validation_error")} for item in exc.errors()]
    return JSONResponse(status_code=422,content=api_error("VALIDATION_ERROR","One or more request fields are invalid.",details=fields,request_id_value=request.state.request_id))
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code,safe_message=public_http_error(exc.status_code); message=safe_message if exc.status_code in {401,403} else str(exc.detail); details=None if exc.status_code in {401,403,404,500} else exc.detail
    return JSONResponse(status_code=exc.status_code,content=api_error(code,message,details=details,request_id_value=request.state.request_id))
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception): return JSONResponse(status_code=500,content=api_error("INTERNAL_ERROR","An unexpected server error occurred.",request_id_value=request.state.request_id))
def customer_public_payload(c): return {"id":c.id,"customer_code":c.customer_code or f"CUST{c.id:08d}","login_id":c.login_id,"name":c.name,"pan":c.pan,"mobile":c.mobile,"email":c.email,"address":c.address,"permanent_address":c.permanent_address,"current_city":c.current_city,"gender":c.gender,"business_name":c.business_name,"business_type":c.business_type,"date_of_birth":c.date_of_birth,"aadhaar_masked":c.aadhaar_masked,"marital_status":c.marital_status,"customer_type":c.customer_type,"occupation":c.occupation,"monthly_income":c.monthly_income,"work_experience_years":c.work_experience_years,"years_in_business":c.years_in_business,"average_bank_balance":c.average_bank_balance,"primary_bank":c.primary_bank,"cibil_score":c.cibil_score,"foir":c.foir,"existing_emi":c.existing_emi,"dependents":c.dependents,"residence_ownership":c.residence_ownership,"residence_since":c.residence_since,"ownership_proof_name":c.ownership_proof_name,"ownership_proof_status":c.ownership_proof_status,"kyc_status":c.kyc_status,"email_verified":c.email_verified,"selfie_status":c.selfie_status}
def assert_customer_access(customer_id,claims):
    if int(claims.get("user_id",-1))!=int(customer_id): raise HTTPException(403,"Customer session does not match this customer")
def audit_http(request,db,**kwargs): record_event(db,**audit_request_context(request,kwargs.pop('claims',None)),**kwargs)
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
def customer_login(payload: CustomerLogin, request: Request, db: Session = Depends(get_db)):
    login_id=payload.login_id.strip(); customer=db.query(CustomerRecord).filter(CustomerRecord.login_id==login_id).first()
    if not customer: raise HTTPException(401,"Invalid customer credentials")
    if not customer.password_hash or not verify_password(payload.password,customer.password_hash): raise HTTPException(401,"Invalid customer credentials")
    return {"access_token":issue_demo_token(str(customer.id),"customer",session_version=customer.session_version),"token_type":"bearer","customer":customer_public_payload(customer)}
