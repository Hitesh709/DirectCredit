from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func
from .database import Base

class CustomerRecord(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    pan = Column(String(20), unique=True, index=True)
    mobile = Column(String(30), index=True)
    email = Column(String(200))
    address = Column(Text)
    current_city = Column(String(100))
    business_name = Column(String(200))
    business_type = Column(String(120))
    date_of_birth = Column(String(20))
    aadhaar_masked = Column(String(30))
    marital_status = Column(String(40))
    customer_type = Column(String(40), default="Individual")
    occupation = Column(String(100), default="Business")
    monthly_income = Column(Float, default=0)
    work_experience_years = Column(Float, default=0)
    years_in_business = Column(Float, default=0)
    average_bank_balance = Column(Float, default=0)
    primary_bank = Column(String(120))
    cibil_score = Column(Integer, default=0)
    foir = Column(Float, default=0)
    existing_emi = Column(Float, default=0)
    dependents = Column(Integer, default=0)
    kyc_status = Column(String(40), default="pending")
    email_verified = Column(String(20), default="pending")
    selfie_status = Column(String(40), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LoanRecord(Base):
    __tablename__ = "loan_applications"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    requested_amount = Column(Float, nullable=False)
    eligible_amount = Column(Float, default=0)
    monthly_emi = Column(Float, default=0)
    sanctioned_amount = Column(Float, default=0)
    disbursed_amount = Column(Float, default=0)
    outstanding_amount = Column(Float, default=0)
    interest_rate = Column(Float, default=0)
    tenure_months = Column(Integer, default=6)
    status = Column(String(50), default="draft", index=True)
    current_stage = Column(String(50), default="PAN", index=True)
    product = Column(String(120), default="Micro Business Loan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    loan_id = Column(Integer, index=True)
    document_type = Column(String(80), nullable=False)
    file_name = Column(String(255), nullable=False)
    verification_status = Column(String(40), default="pending")
    storage_key = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RepaymentRecord(Base):
    __tablename__ = "repayments"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, index=True, nullable=False)
    installment = Column(Integer, nullable=False)
    due_date = Column(String(20), nullable=False)
    due_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)
    status = Column(String(30), default="upcoming", index=True)
