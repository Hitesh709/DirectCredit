from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from .database import Base, engine, get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord, RepaymentRecord
from .schemas import CustomerCreate, CustomerOut, LoanApplicationCreate, LoanApplicationOut, StatusUpdate, DocumentCreate
from .workflow import assess_amount, build_repayment_schedule

app = FastAPI(title="DirectCredit API", version="0.3.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"application": "DirectCredit", "status": "online", "mode": "MVP"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(func.count(CustomerRecord.id))
    return {"status": "healthy", "database": "connected"}

@app.get("/api/version")
def version():
    return {"name": "DirectCredit API", "version": "0.3.0"}

@app.post("/api/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = CustomerRecord(**payload.model_dump())
    db.add(customer); db.commit(); db.refresh(customer)
    return customer

@app.get("/api/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(CustomerRecord).order_by(CustomerRecord.id.desc()).all()

@app.get("/api/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(CustomerRecord, customer_id)
    if not customer: raise HTTPException(404, "Customer not found")
    return customer

@app.get("/api/customers/{customer_id}/profile")
def customer_profile(customer_id: int, db: Session = Depends(get_db)):
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "Customer not found")
    loans = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    loan_ids = [x.id for x in loans]
    repayments = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id.in_(loan_ids)).order_by(RepaymentRecord.id.desc()).all() if loan_ids else []
    documents = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    total = sum(x.sanctioned_amount or 0 for x in loans)
    outstanding = sum(x.outstanding_amount or 0 for x in loans)
    paid = sum(x.paid_amount for x in repayments)
    return {
        "customer": {k: getattr(c, k) for k in ["id","name","pan","mobile","email","address","current_city","business_name","business_type","date_of_birth","aadhaar_masked","marital_status","customer_type","occupation","monthly_income","work_experience_years","years_in_business","average_bank_balance","primary_bank","cibil_score","foir","existing_emi","dependents","kyc_status","email_verified","selfie_status","status"]},
        "metrics": {"total_loans": len(loans), "total_loan_amount": total, "outstanding_amount": outstanding, "amount_paid": paid, "credit_score": c.cibil_score},
        "loans": [{"id":x.id,"product":x.product,"requested_amount":x.requested_amount,"sanctioned_amount":x.sanctioned_amount,"disbursed_amount":x.disbursed_amount,"outstanding_amount":x.outstanding_amount,"monthly_emi":x.monthly_emi,"tenure_months":x.tenure_months,"interest_rate":x.interest_rate,"status":x.status,"current_stage":x.current_stage} for x in loans],
        "repayments": [{"id":r.id,"loan_id":r.loan_id,"installment":r.installment,"due_date":r.due_date,"due_amount":r.due_amount,"paid_amount":r.paid_amount,"status":r.status} for r in repayments],
        "documents": [{"id":d.id,"loan_id":d.loan_id,"document_type":d.document_type,"file_name":d.file_name,"verification_status":d.verification_status,"created_at":d.created_at} for d in documents],
        "tabs": {"profile": True, "contact": True, "bank_analysis": True, "kyc_employment": True, "risk_score": True}
    }

@app.post("/api/loans", response_model=LoanApplicationOut)
def create_loan(payload: LoanApplicationCreate, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord, payload.customer_id): raise HTTPException(404, "Customer not found")
    result = assess_amount(float(payload.requested_amount))
    loan = LoanRecord(customer_id=payload.customer_id, requested_amount=float(payload.requested_amount), eligible_amount=result["eligible_amount"], monthly_emi=round(result["eligible_amount"] / payload.tenure_months, 2), sanctioned_amount=0, disbursed_amount=0, outstanding_amount=0, tenure_months=payload.tenure_months, product=payload.product, status="assessment", current_stage="ASSESSMENT")
    db.add(loan); db.commit(); db.refresh(loan)
    return loan

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
    db.commit(); db.refresh(loan)
    return loan

@app.post("/api/loans/{loan_id}/repayment-schedule")
def create_schedule(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "Loan not found")
    amount = loan.sanctioned_amount or loan.eligible_amount
    schedule = build_repayment_schedule(loan_id, amount, loan.tenure_months)
    for item in schedule: db.add(RepaymentRecord(**item))
    loan.outstanding_amount = amount
    db.commit()
    return schedule

@app.get("/api/loans/{loan_id}/repayments")
def repayments(loan_id: int, db: Session = Depends(get_db)):
    return db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()

@app.post("/api/documents")
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    if not db.get(CustomerRecord, payload.customer_id): raise HTTPException(404, "Customer not found")
    doc = DocumentRecord(**payload.model_dump())
    db.add(doc); db.commit(); db.refresh(doc)
    return {"id": doc.id, "status": "received", "verification_status": doc.verification_status}

@app.get("/api/admin/loans")
def admin_loans(db: Session = Depends(get_db)):
    return db.query(LoanRecord).order_by(LoanRecord.id.desc()).all()

@app.get("/api/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db)):
    loans = db.query(LoanRecord).all()
    return {"applications": len(loans), "assessment": sum(x.status == "assessment" for x in loans), "sanctioned": sum(x.status == "sanctioned" for x in loans), "disbursed": sum(x.status == "disbursed" for x in loans), "repayment": sum(x.status == "repayment" for x in loans), "overdue": sum(x.status == "overdue" for x in loans), "total_sanctioned": sum(x.sanctioned_amount or 0 for x in loans), "total_outstanding": sum(x.outstanding_amount or 0 for x in loans)}
