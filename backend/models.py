from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Customer:
    id: int
    name: str
    pan: Optional[str] = None
    mobile: Optional[str] = None
    status: str = "active"
    created_at: datetime = datetime.utcnow()

@dataclass
class LoanApplication:
    id: int
    customer_id: int
    requested_amount: float
    eligible_amount: float = 0
    status: str = "draft"
    monthly_emi: float = 0
    created_at: datetime = datetime.utcnow()

@dataclass
class Repayment:
    id: int
    loan_id: int
    due_amount: float
    paid_amount: float = 0
    status: str = "upcoming"
    due_date: Optional[str] = None
