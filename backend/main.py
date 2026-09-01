from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, inspect, text
import os
from .database import Base, engine, get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord
from .schemas import CustomerCreate, CustomerOut, CustomerLogin, LoanApplicationCreate, LoanApplicationOut, StatusUpdate, DocumentCreate
from .workflow import assess_amount, build_repayment_schedule
from .profile_service import profile_payload
from .api_services import router as service_router
from .reporting import router as reporting_router
from .seed_demo import seed_demo_data
from .auth import hash_password, verify_password, issue_demo_token, get_current_customer

app = FastAPI(title="DirectCredit API", version="0.7.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def migrate_customer_profile_columns():
    additions = {
        "permanent_address": ("customers", "TEXT"),
        "gender": ("customers", "VARCHAR(40)"),
        "disbursement_details": ("loan_applications", "TEXT"),
        "customer_code": ("customers", "VARCHAR(80)"),
        "login_id": ("customers", "VARCHAR(120)"),
        "password_hash": ("customers", "TEXT"),
    }
    with engine.begin() as conn:
        for name, (table, sql_type) in additions.items():
            try:
                columns = {c["name"] for c in inspect(conn).get_columns(table)}
                if name not in columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
            except Exception:
                pass
        for index_name, table, column in (
            ("uq_customers_customer_code", "customers", "customer_code"),
            ("uq_customers_login_id", "customers", "login_id"),
        ):
            try:
                conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"))
            except Exception:
                pass

def customer_public_payload(c: CustomerRecord) -> dict:
    """Return customer data safe for the UI; never return password_hash."""
    return {
        "id": c.id,
        "customer_code": c.customer_code or f"CUST{c.id:08d}",
        "login_id": c.login_id,
        "name": c.name,
        "pan": c.pan,
        "mobile": c.mobile,
        "email": c.email,
        "address": c.address,
        "permanent_address": c.permanent_address,
        "current_city": c.current_city,
        "gender": c.gender,
        "business_name": c.business_name,
        "business_type": c.business_type,
        "date_of_birth": c.date_of_birth,
        "aadhaar_masked": c.aadhaar_masked,
        "marital_status": c.marital_status,
        "customer_type": c.customer_type,
        "occupation": c.occupation,
        "monthly_income": c.monthly_income,
        "work_experience_years": c.work_experience_years,
        "years_in_business": c.years_in_business,
        "average_bank_balance": c.average_bank_balance,
        "primary_bank": c.primary_bank,
        "cibil_score": c.cibil_score,
        "foir": c.foir,
        "existing_emi": c.existing_emi,
        "dependents": c.dependents,
        "residence_ownership": c.residence_ownership,
        "residence_since": c.residence_since,
        "ownership_proof_name": c.ownership_proof_name,
        "ownership_proof_status": c.ownership_proof_status,
        "kyc_status": c.kyc_status,
        "email_verified": c.email_verified,
        "selfie_status": c.selfie_status,
    }

def assert_customer_access(customer_id: int, claims: dict):
    if int(claims.get("user_id", -1)) != int(customer_id):
        raise HTTPException(status_code=403, detail="Customer session does not match this customer")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine); migrate_customer_profile_columns()
    if os.getenv("SEED_DEMO_DATA", "true").lower() in {"1", "true", "yes"}:
        db = next(get_db())
        try: seed_demo_data(db)
        finally: db.close()

app.include_router(service_router); app.include_router(reporting_router)

@app.get("/")
def root(): return {"application":"DirectCredit","status":"online","mode":"MVP","api_version":"0.7.0"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(func.count(CustomerRecord.id)); return {"status":"healthy","database":"connected"}

@app.get("/api/version")
def version(): return {"name":"DirectCredit API","version":"0.7.0"}

@app.post("/api/customer/login")
def customer_login(payload: CustomerLogin, db: Session = Depends(get_db)):
    login_id = payload.login_id.strip()
    customer = db.query(CustomerRecord).filter(CustomerRecord.login_id == login_id).first()
    if customer:
        if not customer.password_hash:
            if os.getenv("ALLOW_DEMO_CREDENTIAL_CLAIM", "true").lower() not in {"1", "true", "yes"}:
                raise HTTPException(401, "Customer credentials are not configured")
            customer.password_hash = hash_password(payload.password)
            db.commit(); db.refresh(customer)
        elif not verify_password(payload.password, customer.password_hash):
            raise HTTPException(401, "Invalid customer ID or password")
    else:
        customer = CustomerRecord(
            login_id=login_id,
            password_hash=hash_password(payload.password),
            name="New Customer",
            customer_type="Individual",
            occupation="Business",
            monthly_income=0,
            residence_ownership="",
            ownership_proof_status="pending",
            kyc_status="pending",
        )
        db.add(customer); db.commit(); db.refresh(customer)
        customer.customer_code = f"CUST{customer.id:08d}"
        db.commit(); db.refresh(customer)
    token = issue_demo_token(customer.id, "customer")
    return {"access_token": token, "token_type": "bearer", "customer": customer_public_payload(customer)}

@app.get("/api/customer/me")
def customer_me(claims: dict = Depends(get_current_customer), db: Session = Depends(get_db)):
    customer = db.get(CustomerRecord, int(claims["user_id"]))
    if not customer: raise HTTPException(404, "Customer not found")
    return customer_public_payload(customer)

@app.post("/api/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    c = CustomerRecord(**payload.model_dump()); db.add(c); db.commit(); db.refresh(c)
    if not c.customer_code: c.customer_code = f"CUST{c.id:08d}"; db.commit(); db.refresh(c)
    return c

@app.get("/api/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)): return db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()

@app.get("/api/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    c=db.get(CustomerRecord,customer_id)
    if not c: raise HTTPException(404,"Customer not found")
    return c

@app.patch("/api/customers/{customer_id}/profile", response_model=CustomerOut)
def update_customer_profile(customer_id: int, payload: CustomerCreate, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    c=db.get(CustomerRecord,customer_id)
    if not c: raise HTTPException(404,"Customer not found")
    for key,value in payload.model_dump(exclude_unset=True).items():
        if key == "pan" and value is None: continue
        if key != "name" or str(value or "").strip(): setattr(c,key,value)
    db.commit(); db.refresh(c); return c

@app.get("/api/customers/{customer_id}/profile")
def customer_profile(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data

@app.get("/api/customers/{customer_id}/bank-analysis")
def bank_analysis(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["bank_analysis"]

@app.get("/api/customers/{customer_id}/kyc-employment")
def kyc_employment(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["kyc_employment"]

@app.get("/api/customers/{customer_id}/risk-score")
def risk_score(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["risk_score"]

@app.get("/api/customers/{customer_id}/loan-trend")
def loan_trend(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    data=profile_payload(customer_id,db)
    if not data: raise HTTPException(404,"Customer not found")
    return data["loan_trend"]

@app.post("/api/loans", response_model=LoanApplicationOut)
def create_loan(payload: LoanApplicationCreate, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord,payload.customer_id): raise HTTPException(404,"Customer not found")
    r=assess_amount(float(payload.requested_amount)); loan=LoanRecord(customer_id=payload.customer_id,requested_amount=float(payload.requested_amount),eligible_amount=r["eligible_amount"],monthly_emi=round(r["eligible_amount"]/payload.tenure_months,2),tenure_months=payload.tenure_months,product=payload.product,status="assessment",current_stage="ASSESSMENT")
    db.add(loan);db.commit();db.refresh(loan);return loan

@app.get("/api/loans/{loan_id}", response_model=LoanApplicationOut)
def get_loan(loan_id:int,db:Session=Depends(get_db),claims: dict = Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    assert_customer_access(loan.customer_id, claims)
    return loan

@app.patch("/api/loans/{loan_id}/status", response_model=LoanApplicationOut)
def update_loan_status(loan_id:int,payload:StatusUpdate,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    loan.status=payload.status
    if payload.current_stage: loan.current_stage=payload.current_stage
    db.commit();db.refresh(loan);return loan

@app.post("/api/loans/{loan_id}/repayment-schedule")
def create_schedule(loan_id:int,db:Session=Depends(get_db)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan not found")
    amount=loan.sanctioned_amount or loan.eligible_amount;db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).delete()
    schedule=build_repayment_schedule(loan_id,amount,loan.tenure_months)
    for item in schedule: db.add(RepaymentRecord(**item))
    loan.outstanding_amount=amount;db.commit();return schedule

@app.get("/api/loans/{loan_id}/repayments")
def repayments(loan_id:int,db:Session=Depends(get_db),claims: dict = Depends(get_current_customer)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"Loan application not found")
    assert_customer_access(loan.customer_id, claims)
    return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).order_by(RepaymentRecord.installment).all()

@app.post("/api/documents")
def create_document(payload:DocumentCreate,db:Session=Depends(get_db)):
    if not db.get(CustomerRecord,payload.customer_id): raise HTTPException(404,"Customer not found")
    d=DocumentRecord(**payload.model_dump());db.add(d);db.commit();db.refresh(d);return {"id":d.id,"status":"received","verification_status":d.verification_status}

@app.get("/api/customers/{customer_id}/documents")
def customer_documents(customer_id:int,db:Session=Depends(get_db),claims: dict = Depends(get_current_customer)):
    assert_customer_access(customer_id, claims)
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"Customer not found")
    return db.query(DocumentRecord).filter(DocumentRecord.customer_id==customer_id).order_by(DocumentRecord.id.desc()).all()

@app.get("/api/admin/loans")
def admin_loans(db:Session=Depends(get_db)): return db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()

@app.get("/api/admin/dashboard")
def admin_dashboard(db:Session=Depends(get_db)):
    loans=db.query(LoanRecord).all()
    return {"applications":len(loans),"assessment":sum(x.status=="assessment" for x in loans),"sanctioned":sum(x.status=="sanctioned" for x in loans),"disbursed":sum(x.status=="disbursed" for x in loans),"repayment":sum(x.status=="repayment" for x in loans),"overdue":sum(x.status=="overdue" for x in loans),"total_sanctioned":sum(x.sanctioned_amount or 0 for x in loans),"total_outstanding":sum(x.outstanding_amount or 0 for x in loans),"customers":db.query(CustomerRecord).count()}