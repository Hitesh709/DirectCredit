from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.sql import func
from .database import Base

class CustomerRecord(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(80), unique=True, index=True)
    login_id = Column(String(120), unique=True, index=True)
    password_hash = Column(Text)
    name = Column(String(200), nullable=False)
    pan = Column(String(20), unique=True, index=True)
    mobile = Column(String(30), index=True)
    email = Column(String(200))
    address = Column(Text)
    permanent_address = Column(Text)
    current_city = Column(String(100))
    gender = Column(String(40))
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
    residence_ownership = Column(String(50))
    residence_since = Column(String(50))
    ownership_proof_name = Column(String(255))
    ownership_proof_status = Column(String(40), default="pending")
    kyc_status = Column(String(40), default="pending")
    email_verified = Column(String(20), default="pending")
    selfie_status = Column(String(40), default="pending")

class RevokedTokenRecord(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    role = Column(String(40))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())

class LoanRecord(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    requested_amount = Column(Float, default=0)
    eligible_amount = Column(Float, default=0)
    sanctioned_amount = Column(Float, default=0)
    disbursed_amount = Column(Float, default=0)
    outstanding_amount = Column(Float, default=0)
    monthly_emi = Column(Float, default=0)
    product = Column(String(120), default="Micro Business Loan")
    tenure_months = Column(Integer, default=6)
    status = Column(String(40), default="draft")
    current_stage = Column(String(80), default="application")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    document_type = Column(String(80), nullable=False)
    document_role = Column(String(40), default="supporting")
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(120))
    file_size = Column(Integer, default=0)
    checksum = Column(String(128))
    source = Column(String(80), default="customer_portal")
    required = Column(Boolean, default=False)
    verification_status = Column(String(40), default="pending")
    verified_by = Column(String(120))
    verified_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    storage_provider = Column(String(80))
    storage_key = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RepaymentRecord(Base):
    __tablename__ = "repayments"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, index=True)
    installment_no = Column(Integer, default=1)
    due_date = Column(String(30))
    due_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    status = Column(String(40), default="upcoming")
    payment_reference = Column(String(160), index=True)
    payment_method = Column(String(40))
    paid_at = Column(DateTime(timezone=True))
    bounce_reason = Column(Text)

class CustomerJourneyRecord(Base):
    __tablename__ = "customer_journey"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    loan_id = Column(Integer, nullable=True, index=True)
    stage = Column(String(80))
    status = Column(String(40))
    payload = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEventRecord(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    actor_type = Column(String(40), nullable=False)
    actor_id = Column(String(120))
    action = Column(String(120), nullable=False)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(String(120))
    request_id = Column(String(120), index=True)
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
