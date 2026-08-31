from pydantic import BaseModel, Field
from typing import Optional

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    pan: Optional[str] = None
    mobile: Optional[str] = None

class CustomerOut(CustomerCreate):
    id: int
    status: str

class LoanApplicationCreate(BaseModel):
    customer_id: int
    requested_amount: float = Field(gt=0, le=15000)

class LoanApplicationOut(LoanApplicationCreate):
    id: int
    eligible_amount: float
    monthly_emi: float
    status: str

class StatusUpdate(BaseModel):
    status: str
