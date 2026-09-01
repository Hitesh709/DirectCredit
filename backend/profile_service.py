from sqlalchemy.orm import Session
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord


def profile_payload(customer_id: int, db: Session) -> dict:
    c = db.get(CustomerRecord, customer_id)
    if not c:
        return None
    loans = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    ids = [x.id for x in loans]
    repayments = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id.in_(ids)).order_by(RepaymentRecord.id.desc()).all() if ids else []
    docs = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    sanctioned = sum(x.sanctioned_amount or 0 for x in loans)
    outstanding = sum(x.outstanding_amount or 0 for x in loans)
    paid = sum(x.paid_amount or 0 for x in repayments)
    overdue = sum(max((x.due_amount or 0) - (x.paid_amount or 0), 0) for x in repayments if x.status == "overdue")
    bank = {"total_transactions": None,"upi_transactions": None,"last_balance": None,"average_eod_balance": None,"average_monthly_credit": None,"average_monthly_debit": None,"monthly_breakdown": [],"status":"No bank transaction data connected"}
    risk_score = None if not c.cibil_score else min(100, max(0, round((c.cibil_score or 0) / 9 + max(0, 20 - (c.foir or 0) / 2), 1)))
    risk = {"total_score": risk_score,"risk_tier": ("Low" if risk_score is not None and risk_score >= 75 else "Medium" if risk_score is not None and risk_score >= 55 else "Not assessed"),"decision": "Eligible" if risk_score is not None and risk_score >= 55 else "Review required","age": None,"bank_verification": c.kyc_status,"credit_score": c.cibil_score,"credit_enquiries": None,"negative_balance": None,"monthly_income": c.monthly_income,"bank_vintage": None,"dpd_analysis": None,"debt_analysis": None,"cheque_return": None}
    customer={k:getattr(c,k) for k in ["id","name","pan","mobile","email","address","current_city","business_name","business_type","date_of_birth","aadhaar_masked","marital_status","customer_type","occupation","monthly_income","work_experience_years","years_in_business","average_bank_balance","primary_bank","cibil_score","foir","existing_emi","dependents","kyc_status","email_verified","selfie_status"]}
    customer["status"]="active"
    return {"customer":customer,"metrics":{"total_loans":len(loans),"total_loan_amount":sanctioned,"outstanding_amount":outstanding,"amount_paid":paid,"credit_score":c.cibil_score,"overdue_amount":overdue},"loans":[{"id":x.id,"product":x.product,"requested_amount":x.requested_amount,"sanctioned_amount":x.sanctioned_amount,"disbursed_amount":x.disbursed_amount,"outstanding_amount":x.outstanding_amount,"monthly_emi":x.monthly_emi,"tenure_months":x.tenure_months,"interest_rate":x.interest_rate,"status":x.status,"current_stage":x.current_stage} for x in loans],"repayments":[{"id":r.id,"loan_id":r.loan_id,"installment":r.installment,"due_date":r.due_date,"due_amount":r.due_amount,"paid_amount":r.paid_amount,"status":r.status} for r in repayments],"documents":[{"id":d.id,"loan_id":d.loan_id,"document_type":d.document_type,"file_name":d.file_name,"verification_status":d.verification_status,"created_at":str(d.created_at) if d.created_at else None} for d in docs],"bank_analysis":bank,"kyc_employment":{"kyc_status":c.kyc_status,"employment_type":c.occupation,"income":c.monthly_income,"work_experience_years":c.work_experience_years,"years_in_business":c.years_in_business,"emergency_contacts":[]},"risk_score":risk,"loan_trend":{"applications":len(loans),"pending_approvals":sum(x.status in {"assessment","review"} for x in loans),"due_repayments":sum(x.status == "repayment" for x in loans),"overdue_loans":sum(x.status == "overdue" for x in loans),"completed_loans":sum(x.status == "closed" for x in loans)},"tabs":["profile","contact","bank_analysis","kyc_employment","risk_score"]}
