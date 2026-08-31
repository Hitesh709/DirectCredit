from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func
from .database import Base

if Base is not None:
    class CustomerRecord(Base):
        __tablename__ = "customers"
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(200), nullable=False)
        pan = Column(String(20), unique=True, index=True)
        mobile = Column(String(30), index=True)
        status = Column(String(30), default="active")
        created_at = Column(DateTime(timezone=True), server_default=func.now())

    class LoanRecord(Base):
        __tablename__ = "loan_applications"
        id = Column(Integer, primary_key=True, index=True)
        customer_id = Column(Integer, index=True, nullable=False)
        requested_amount = Column(Float, nullable=False)
        eligible_amount = Column(Float, default=0)
        monthly_emi = Column(Float, default=0)
        status = Column(String(50), default="draft", index=True)
        current_stage = Column(String(50), default="PAN")
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
