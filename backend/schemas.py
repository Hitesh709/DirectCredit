from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    pan: Optional[str] = None; mobile: Optional[str] = None; email: Optional[str] = None; address: Optional[str] = None; permanent_address: Optional[str] = None; current_city: Optional[str] = None; gender: Optional[str] = None; business_name: Optional[str] = None; business_type: Optional[str] = None; date_of_birth: Optional[str] = None; aadhaar_masked: Optional[str] = None; marital_status: Optional[str] = None
    customer_type: str = "Individual"; occupation: str = "Business"; monthly_income: float = 0; work_experience_years: float = 0; years_in_business: float = 0; average_bank_balance: float = 0; primary_bank: Optional[str] = None; cibil_score: int = 0; foir: float = 0; existing_emi: float = 0; dependents: int = 0; residence_ownership: Optional[str] = None; residence_since: Optional[str] = None; ownership_proof_name: Optional[str] = None; ownership_proof_status: Optional[str] = None
class CustomerOut(CustomerCreate): id: int; status: str = "active"
class CustomerLogin(BaseModel):
    """Legacy credential login schema retained only for compatibility; the endpoint is disabled."""
    login_id: str = Field(min_length=1,max_length=120); password: str = Field(min_length=1,max_length=200)
    @field_validator('login_id')
    @classmethod
    def legacy_login_disabled(cls,value):
        raise ValueError('Legacy customer ID/password login is disabled. Use the mobile-only customer access flow.')
class CustomerRegistrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    mobile: str = Field(min_length=10, max_length=16)
    email: Optional[str] = Field(default=None, max_length=200)
    customer_type: str = Field(default="Individual", max_length=40)
    occupation: str = Field(default="Business", max_length=100)
    business_name: Optional[str] = Field(default=None, max_length=200)
    business_type: Optional[str] = Field(default=None, max_length=120)
    current_city: Optional[str] = Field(default=None, max_length=100)
class PersonalProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    gender: Optional[str] = Field(default=None, max_length=40)
    date_of_birth: Optional[str] = Field(default=None, max_length=20)
    marital_status: Optional[str] = Field(default=None, max_length=40)
    address: Optional[str] = None
    permanent_address: Optional[str] = None
    current_city: Optional[str] = Field(default=None, max_length=100)
    residence_ownership: Optional[str] = Field(default=None, max_length=50)
    residence_since: Optional[str] = Field(default=None, max_length=50)
class EmploymentBusinessUpdate(BaseModel):
    occupation: Optional[str] = Field(default=None, max_length=100)
    customer_type: Optional[str] = Field(default=None, max_length=40)
    business_name: Optional[str] = Field(default=None, max_length=200)
    business_type: Optional[str] = Field(default=None, max_length=120)
    monthly_income: Optional[float] = Field(default=None, ge=0)
    work_experience_years: Optional[float] = Field(default=None, ge=0)
    years_in_business: Optional[float] = Field(default=None, ge=0)
    average_bank_balance: Optional[float] = Field(default=None, ge=0)
    primary_bank: Optional[str] = Field(default=None, max_length=120)
    existing_emi: Optional[float] = Field(default=None, ge=0)
    dependents: Optional[int] = Field(default=None, ge=0)
class AddressResidenceUpdate(BaseModel):
    address: Optional[str] = Field(default=None, min_length=1)
    permanent_address: Optional[str] = Field(default=None, min_length=1)
    current_city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    residence_ownership: Optional[str] = Field(default=None, min_length=1, max_length=50)
    residence_since: Optional[str] = Field(default=None, min_length=1, max_length=50)
class ResidenceProofCreate(BaseModel):
    document_type: str = Field(default="RESIDENCE_PROOF", min_length=1, max_length=80)
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: Optional[str] = Field(default=None, max_length=120)
    file_size: int = Field(default=0, ge=0)
    checksum: Optional[str] = Field(default=None, max_length=128)
    storage_provider: Optional[str] = Field(default=None, max_length=50)
    storage_key: Optional[str] = None
class RegisterRequest(BaseModel): name: str = Field(min_length=1,max_length=200); login_id: str = Field(min_length=1,max_length=120); password: str = Field(min_length=8,max_length=200); email: Optional[str] = None; mobile: Optional[str] = None; customer_type: str = "Individual"; occupation: str = "Business"
class LoginRequest(BaseModel): login_id: str = Field(min_length=1,max_length=120); password: str = Field(min_length=8,max_length=200)
class RefreshRequest(BaseModel): refresh_token: str = Field(min_length=20)
class EmailTokenRequest(BaseModel): token: str = Field(min_length=1)
class PasswordRequest(BaseModel): token: str = Field(min_length=20); new_password: str = Field(min_length=8,max_length=200)
class LoanApplicationCreate(BaseModel): customer_id: int; requested_amount: float = Field(gt=0,le=15000); product: str = "Micro Business Loan"; tenure_months: int = Field(default=6,ge=1,le=60)
class LoanApplicationOut(LoanApplicationCreate): id: int; eligible_amount: float; monthly_emi: float; sanctioned_amount: float; disbursed_amount: float; outstanding_amount: float; status: str; current_stage: str
class StatusUpdate(BaseModel): status: str; current_stage: Optional[str] = None
class DocumentCreate(BaseModel):
    customer_id: int; loan_id: Optional[int] = None; document_type: str = Field(min_length=1,max_length=80); document_role: str = "supporting"; file_name: str = Field(min_length=1,max_length=255); mime_type: Optional[str] = None; file_size: int = Field(default=0,ge=0); checksum: Optional[str] = None; source: str = "customer_portal"; required: bool = False; verification_status: str = "pending"; verified_by: Optional[str] = None; rejection_reason: Optional[str] = None; storage_provider: Optional[str] = None; storage_key: Optional[str] = None
