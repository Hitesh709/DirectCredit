from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, CustomerKYCRecord, CustomerBankAccountRecord, DocumentRecord
from .auth import get_current_customer

router = APIRouter(prefix="/loan-request", tags=["loan-request"])
MIN_AMOUNT, MAX_AMOUNT = 5000.0, 15000.0
ALLOWED_TENURES = {3, 6, 9, 12}
ACTIVE_STATUSES = {"draft", "assessment", "sanctioned", "customer_approved", "esign_pending", "esigned", "mandate_pending", "mandate_active", "disbursement_pending", "disbursed", "active", "overdue"}
APPLICATION_STAGES = ["PAN", "AADHAAR", "PERSONAL", "ADDRESS", "BUSINESS", "BANKING", "DOCUMENTS", "REVIEW", "ASSESSMENT"]

class LoanRequest(BaseModel):
    product: str = Field(default="Micro Business Loan", min_length=1, max_length=120)
    requested_amount: float = Field(ge=MIN_AMOUNT, le=MAX_AMOUNT)
    tenure_months: int = Field(default=6, ge=1, le=60)

@router.post("/{customer_id}")
def create_request(customer_id: int, payload: LoanRequest, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    if payload.tenure_months not in ALLOWED_TENURES:
        raise HTTPException(422, "Supported tenure is 3, 6, 9 or 12 months")
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "Customer not found")
    existing = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id, LoanRecord.status.in_(ACTIVE_STATUSES)).order_by(LoanRecord.id.desc()).first()
    if existing:
        raise HTTPException(409, f"An active loan application already exists (Application #{existing.id}). Complete or close it before starting another application.")
    loan = LoanRecord(customer_id=customer_id, requested_amount=payload.requested_amount,
                      tenure_months=payload.tenure_months, product=payload.product,
                      status="draft", current_stage="PAN")
    db.add(loan); db.commit(); db.refresh(loan)
    return {"loan_id": loan.id, "customer_id": customer_id, "product": loan.product,
            "requested_amount": loan.requested_amount, "tenure_months": loan.tenure_months,
            "status": loan.status, "current_stage": loan.current_stage}

@router.get("/{customer_id}")
def list_requests(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id: raise HTTPException(403, "Customer session does not match this customer")
    rows = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    return [{"loan_id": r.id, "product": r.product, "requested_amount": r.requested_amount,
             "eligible_amount": r.eligible_amount, "tenure_months": r.tenure_months,
             "status": r.status, "current_stage": r.current_stage} for r in rows]


@router.get("/{customer_id}/active")
def active_request(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    loan = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id, LoanRecord.status.in_(ACTIVE_STATUSES)).order_by(LoanRecord.id.desc()).first()
    if not loan:
        return {"active": False, "application": None}
    return {"active": True, "application": {"loan_id": loan.id, "requested_amount": loan.requested_amount, "tenure_months": loan.tenure_months, "product": loan.product, "status": loan.status, "current_stage": loan.current_stage}}

@router.patch("/{customer_id}/{loan_id}/stage")
def update_application_stage(customer_id: int, loan_id: int, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    loan = db.get(LoanRecord, loan_id)
    if not loan or int(loan.customer_id) != customer_id:
        raise HTTPException(404, "Loan application not found")
    stage = str(payload.get("stage") or "").strip().upper()
    if stage not in APPLICATION_STAGES:
        raise HTTPException(422, "Unsupported application stage")
    current = str(loan.current_stage or "PAN").upper()
    if current in APPLICATION_STAGES and APPLICATION_STAGES.index(stage) < APPLICATION_STAGES.index(current):
        raise HTTPException(422, "Application cannot move backwards")
    loan.current_stage = stage
    if stage == "ASSESSMENT" and loan.status == "draft":
        loan.status = "assessment"
    db.commit(); db.refresh(loan)
    return {"updated": True, "loan_id": loan.id, "current_stage": loan.current_stage, "status": loan.status}

@router.patch("/{customer_id}/{loan_id}/kyc")
def save_kyc(customer_id: int, loan_id: int, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    loan = db.get(LoanRecord, loan_id)
    if not loan or int(loan.customer_id) != customer_id:
        raise HTTPException(404, "Loan application not found")
    customer = db.get(CustomerRecord, customer_id)
    if not customer: raise HTTPException(404, "Customer not found")
    pan = str(payload.get("pan") or "").strip().upper()
    aadhaar = "".join(ch for ch in str(payload.get("aadhaar") or "") if ch.isdigit())
    if pan:
        if len(pan) != 10: raise HTTPException(422, "Enter a valid PAN")
        customer.pan = pan
    if aadhaar:
        if len(aadhaar) != 12: raise HTTPException(422, "Enter a valid 12-digit Aadhaar number")
        customer.aadhaar_masked = "XXXX-XXXX-" + aadhaar[-4:]
    kyc = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    if not kyc:
        kyc = CustomerKYCRecord(customer_id=customer_id); db.add(kyc)
    if pan: kyc.pan_status = "pending"
    if aadhaar: kyc.identity_status = "pending"; kyc.aadhaar_reference = kyc.aadhaar_reference or "customer_portal"
    kyc.status = "pending"
    db.commit(); db.refresh(kyc)
    return {"saved": True, "customer_id": customer_id, "loan_id": loan_id, "pan": customer.pan, "aadhaar_masked": customer.aadhaar_masked, "kyc_status": kyc.status, "pan_status": kyc.pan_status, "identity_status": kyc.identity_status}

@router.post("/{customer_id}/{loan_id}/bank-account")
def save_bank_account(customer_id: int, loan_id: int, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id: raise HTTPException(403, "Customer session does not match this customer")
    loan = db.get(LoanRecord, loan_id)
    if not loan or int(loan.customer_id) != customer_id: raise HTTPException(404, "Loan application not found")
    bank_name = str(payload.get("bank_name") or "").strip()
    holder = str(payload.get("account_holder_name") or "").strip()
    masked = str(payload.get("account_number_masked") or "").strip()
    if not bank_name or not holder or not masked: raise HTTPException(422, "Bank name, account holder and account number are required")
    row = CustomerBankAccountRecord(customer_id=customer_id, bank_name=bank_name, account_holder_name=holder, account_number_masked=masked, ifsc=str(payload.get("ifsc") or "").strip().upper() or None, account_type=str(payload.get("account_type") or "SAVINGS").strip().upper(), is_primary=True, verification_status="pending")
    db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer_id).update({"is_primary": False})
    db.add(row); customer=db.get(CustomerRecord, customer_id); customer.primary_bank=bank_name
    db.commit(); db.refresh(row)
    return {"saved": True, "bank_account_id": row.id, "verification_status": row.verification_status}

@router.post("/{customer_id}/{loan_id}/document")
def save_application_document(customer_id: int, loan_id: int, payload: dict, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id: raise HTTPException(403, "Customer session does not match this customer")
    loan = db.get(LoanRecord, loan_id)
    if not loan or int(loan.customer_id) != customer_id: raise HTTPException(404, "Loan application not found")
    document_type = str(payload.get("document_type") or "").strip().upper()
    file_name = str(payload.get("file_name") or "").strip()
    if not document_type or not file_name: raise HTTPException(422, "Document type and file name are required")
    d = DocumentRecord(customer_id=customer_id, loan_id=loan_id, document_type=document_type, document_role="loan_application", file_name=file_name, mime_type=payload.get("mime_type"), file_size=int(payload.get("file_size") or 0), source="customer_portal", required=True, verification_status="pending")
    db.add(d); db.commit(); db.refresh(d)
    return {"saved": True, "document_id": d.id, "document_type": d.document_type, "verification_status": d.verification_status}
