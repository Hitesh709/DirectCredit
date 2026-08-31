from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from .models import Customer, LoanApplication
from .schemas import CustomerCreate, CustomerOut, LoanApplicationCreate, LoanApplicationOut, StatusUpdate
from .store import customers, applications, next_id

app = FastAPI(title="DirectCredit API", version="0.2.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"application": "DirectCredit", "status": "online", "mode": "demo"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/version")
def version():
    return {"name": "DirectCredit API", "version": "0.2.0"}

@app.post("/api/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate):
    customer_id = next_id("customer")
    customer = Customer(id=customer_id, name=payload.name, pan=payload.pan, mobile=payload.mobile)
    customers[customer_id] = customer
    return customer

@app.get("/api/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    customer = customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/api/loans", response_model=LoanApplicationOut)
def create_loan(payload: LoanApplicationCreate):
    if payload.customer_id not in customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    amount = float(payload.requested_amount)
    eligible = amount
    monthly_emi = round(amount / 6, 2)
    loan_id = next_id("application")
    loan = LoanApplication(id=loan_id, customer_id=payload.customer_id, requested_amount=amount, eligible_amount=eligible, monthly_emi=monthly_emi, status="assessment")
    applications[loan_id] = loan
    return loan

@app.get("/api/loans/{loan_id}", response_model=LoanApplicationOut)
def get_loan(loan_id: int):
    loan = applications.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    return loan

@app.patch("/api/loans/{loan_id}/status", response_model=LoanApplicationOut)
def update_loan_status(loan_id: int, payload: StatusUpdate):
    loan = applications.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    loan.status = payload.status
    return loan

@app.get("/api/admin/loans")
def admin_loans():
    return list(applications.values())
