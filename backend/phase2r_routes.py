from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .admin_auth import get_current_admin
from .db_models import CustomerRecord, CustomerKYCRecord, CustomerBankAccountRecord, CustomerConsentRecord, AuditEventRecord
from .phase2r_compliance import PHASE2R_VERSION, compliance_contract, evaluate_compliance

router = APIRouter(prefix="/api/v1/compliance", tags=["phase-2r-compliance"])

@router.get("/contract")
def contract():
    return compliance_contract()

@router.get("/customer/{customer_id}")
def customer_compliance(customer_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    customer = db.get(CustomerRecord, customer_id)
    if not customer:
        raise HTTPException(404, "customer_not_found")
    kyc = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    bank = db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer_id, CustomerBankAccountRecord.is_primary == True).first()
    consents = db.query(CustomerConsentRecord).filter(CustomerConsentRecord.customer_id == customer_id).all()
    audit_count = db.query(AuditEventRecord).filter(AuditEventRecord.customer_id == customer_id).count()
    result = evaluate_compliance(
        kyc_status=kyc.status if kyc else customer.kyc_status,
        pan_status=kyc.pan_status if kyc else None,
        identity_status=kyc.identity_status if kyc else customer.selfie_status,
        address_status=kyc.address_status if kyc else None,
        business_status=kyc.business_status if kyc else None,
        primary_bank_status=bank.verification_status if bank else None,
        consents=[{
            "consent_type": c.consent_type,
            "accepted": c.accepted,
            "withdrawn_at": c.withdrawn_at,
        } for c in consents],
        audit_event_count=audit_count,
    )
    result["customer_id"] = customer_id
    result["engine_version"] = PHASE2R_VERSION
    return result

@router.get("/queue")
def compliance_queue(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(CustomerRecord).order_by(CustomerRecord.id).all()
    items = []
    for customer in rows:
        kyc = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer.id).first()
        bank = db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer.id, CustomerBankAccountRecord.is_primary == True).first()
        consents = db.query(CustomerConsentRecord).filter(CustomerConsentRecord.customer_id == customer.id).all()
        audit_count = db.query(AuditEventRecord).filter(AuditEventRecord.customer_id == customer.id).count()
        result = evaluate_compliance(
            kyc_status=kyc.status if kyc else customer.kyc_status,
            pan_status=kyc.pan_status if kyc else None,
            identity_status=kyc.identity_status if kyc else customer.selfie_status,
            address_status=kyc.address_status if kyc else None,
            business_status=kyc.business_status if kyc else None,
            primary_bank_status=bank.verification_status if bank else None,
            consents=[{"consent_type": c.consent_type, "accepted": c.accepted, "withdrawn_at": c.withdrawn_at} for c in consents],
            audit_event_count=audit_count,
        )
        if result["status"] != "PASS":
            items.append({"customer_id": customer.id, "status": result["status"], "review_checks": result["review_checks"], "failed_checks": result["failed_checks"]})
    return {"version": PHASE2R_VERSION, "count": len(items), "items": items}
