from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func
from .database import Base

class DisbursementRecord(Base):
    __tablename__ = "disbursements"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String(160), index=True)
    method = Column(String(40))
    status = Column(String(40), default="pending", index=True)
    disbursed_at = Column(DateTime(timezone=True))
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LedgerEntry(Base):
    __tablename__ = "loan_ledger"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, index=True, nullable=False)
    entry_type = Column(String(40), nullable=False, index=True)
    reference = Column(String(160), index=True)
    debit = Column(Float, default=0)
    credit = Column(Float, default=0)
    balance = Column(Float, default=0)
    description = Column(String(255))
    entry_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class AccountingEntry(Base):
    __tablename__ = "accounting_ledger"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, index=True)
    customer_id = Column(Integer, index=True)
    account = Column(String(80), nullable=False, index=True)
    entry_type = Column(String(40), nullable=False, index=True)
    reference = Column(String(160), index=True)
    debit = Column(Float, default=0)
    credit = Column(Float, default=0)
    narration = Column(String(255))
    entry_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
