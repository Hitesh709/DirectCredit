from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, inspect, text
import os
from .database import Base, engine, get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord
from .schemas import CustomerCreate, CustomerOut, LoanApplicationCreate, LoanApplicationOut, StatusUpdate, DocumentCreate
from .workflow import assess_amount, build_repayment_schedule
from .profile_service import profile_payload
from .api_services import router as service_router
from .reporting import router as reporting_router
from .seed_demo import seed_demo_data

app = FastAPI(title="DirectCredit API", version="0.5.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def migrate_customer_profile_columns():
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("customers")}
    additions = {
        "permanent_address": "TEXT",
        "gender": "VARCHAR(40)",
    }
    with engine.begin() as conn:
        for name, sql_type in additions.items():
            if name not in columns:
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN {name} {sql_type}"))

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    migrate_customer_profile_columns()
    if os.getenv("SEED_DEMO_DATA", "true").lower() in {"1", "true", "yes"}:
        db = next(get_db())
        try:
            seed_demo_data(db)
        finally:
            db.close()

app.include_router(service_router)
app.include_router(reporting_router)

@app.get("/")
def root():
    return {"application":"DirectCredit","status":"online","mode":"MVP","api_version":"0.5.0"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(func.count(CustomerRecord.id))
    return {"status":"healthy","database":"connected"}

@app.get("/api/version")
def version(): return {"name":"DirectCredit API","version":"0.5.0"}

@app.post("/api/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    c = CustomerRecord(**payload.model_dump()); db.add(c); db.commit(); db.refresh(c); return c

@app.get("/api/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()

@app.get("/api/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "Customer not found")
    return c

@app.patch("/api/customers/{customer_id}/profile", response_model=CustomerOut)
def update_customer_profile(customer_id: int, payload: CustomerCreate, db: Session = Depends(get_db)):
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "Customer not found")
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        if key != "name" or str(value or "").strip():
            setattr(c, key, value)
    db.commit(); db.refresh(c)
    return c

@app.get("/api/customers/{customer_id}/profile")
def customer_profile(customer_id: int, db: Session = Depends(get_db)):
    data = profile_payload(customer_id, db)
    if not data: raise HTTPException(404, "Customer not found")
    return data

@app.get("/api/customers/{customer_id}/bank-analysis")
def bank_analysis(customer_id: int, db: Session = Depends(get_db)):
    data = profile_payload(customer_id, db)
    if not data: raise HTTPException(404, "Customer not found")
    return data["bank_analysis"]

@app.get("/api/customers/{customer_id}/kyc-employment")
def kyc_employment(customer_id: int, db: Session = Depends(get_db)):
    data = profile_payload(customer_id, db)
    if not data: raise HTTPException(404, "Customer not found")
    return data["kyc_employment"]

@app.get("/api/customers/{customer_id}/risk-score")
def risk_score(customer_id: int, db: Session = Depends(get_db)):
    data = profile_payload(customer_id, db)
    if not data: raise HTTPException(404, "Customer not found")
    return data["risk_score"]

@app.get("/api/customers/{customer_id}/loan-trend")
def loan_trend(customer_id: int, db: Session = Depends(get_db)):
    data = profile_payload(customer_id, db)
    if not data: raise HTTPException(404, "Customer not found")
    return data["loan_trend"]

@app.post("/api/loans", response_model=LoanApplicationOut)
def create_loan(payload: LoanApplicationCreate, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord, payload.customer_id): raise HTTPException(404, "Customer not found")
    r = assess_amount(float(payload.requested_amount))
    loan = LoanRecord(customer_id=payload.customer_id, requested_amount=float(payload.requested_amount), eligible_amount=r["eligible_amount"], monthly_emi=round(r["eligible_amount"] / payload.tenure_months, 2), tenure_months=payload.tenure_months, product=payload.product, status="assessment", current_stage="ASSESSMENT")
    db.add(loan); db.commit(); db.refresh(loan); return loan

@app.get("/api/loans/{loan_id}", response_model=LoanApplicationOut)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "Loan application not found")
    return loan

@app.patch("/api/loans/{loan_id}/status", response_model=LoanApplicationOut)
def update_loan_status(loan_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "Loan application not found")
    loan.status = payload.status
    if payload.current_stage: loan.current_stage = payload.current_stage
    db.commit(); db.refresh(loan); return loan

@app.post("/api/loans/{loan_id}/repayment-schedule")
def create_schedule(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "Loan not found")
    amount = loan.sanctioned_amount or loan.eligible_amount
    db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).delete()
    schedule = build_repayment_schedule(loan_id, amount, loan.tenure_months)
    for item in schedule: db.add(RepaymentRecord(**item))
    loan.outstanding_amount = amount; db.commit(); return schedule

@app.get("/api/loans/{loan_id}/repayments")
def repayments(loan_id: int, db: Session = Depends(get_db)):
    return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()

@app.post("/api/documents")
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord, payload.customer_id): raise HTTPException(404, "Customer not found")
    d = DocumentRecord(**payload.model_dump()); db.add(d); db.commit(); db.refresh(d)
    return {"id":d.id,"status":"received","verification_status":d.verification_status}

@app.get("/api/customers/{customer_id}/documents")
def customer_documents(customer_id: int, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord, customer_id): raise HTTPException(404, "Customer not found")
    return db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()

@app.get("/api/admin/loans")
def admin_loans(db: Session = Depends(get_db)):
    return db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()

@app.get("/api/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db)):
    loans = db.query(LoanRecord).all()
    return {"applications":len(loans),"assessment":sum(x.status=="assessment" for x in loans),"sanctioned":sum(x.status=="sanctioned" for x in loans),"disbursed":sum(x.status=="disbursed" for x in loans),"repayment":sum(x.status=="repayment" for x in loans),"overdue":sum(x.status=="overdue" for x in loans),"total_sanctioned":sum(x.sanctioned_amount or 0 for x in loans),"total_outstanding":sum(x.outstanding_amount or 0 for x in loans),"customers":db.query(CustomerRecord).count()}
