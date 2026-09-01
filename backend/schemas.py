from pydantic import BaseModel, Field
from typing import Optional

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    pan: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    permanent_address: Optional[str] = None
    current_city: Optional[str] = None
    gender: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    date_of_birth: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    marital_status: Optional[str] = None
    customer_type: str = "Individual"
    occupation: str = "Business"
    monthly_income: float = 0
    work_experience_years: float = 0
    years_in_business: float = 0
    average_bank_balance: float = 0
    primary_bank: Optional[str] = None
    cibil_score: int = 0
    foir: float = 0
    existing_emi: float = 0
    dependents: int = 0

class CustomerOut(CustomerCreate):
    id: int
    status: str = "active"

class LoanApplicationCreate(BaseModel):
    customer_id: int
    requested_amount: float = Field(gt=0, le=15000)
    product: str = "Micro Business Loan"
    tenure_months: int = Field(default=6, ge=1, le=60)

class LoanApplicationOut(LoanApplicationCreate):
    id: int
    eligible_amount: float
    monthly_emi: float
    sanctioned_amount: float
    disbursed_amount: float
    outstanding_amount: float
    status: str
    current_stage: str

class StatusUpdate(BaseModel):
    status: str
    current_stage: Optional[str] = None

class DocumentCreate(BaseModel):
    customer_id: int
    loan_id: Optional[int] = None
    document_type: str
    file_name: str
    verification_status: str = "pending"
