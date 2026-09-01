from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from .database import engine, get_db
from .db_models import CustomerRecord, LoanRecord, DocumentRecord
from .schemas import DocumentCreate
from .auth import get_current_customer

router = APIRouter(prefix="/api/documents", tags=["documents"])

DOCUMENT_TYPES = {
    "PAN", "AADHAAR", "SELFIE", "BANK_STATEMENT", "BUSINESS_PROOF",
    "OWNERSHIP_PROOF", "RENT_AGREEMENT", "ADDRESS_PROOF", "INCOME_PROOF",
    "OTHER"
}
DOCUMENT_STATUSES = {"pending", "under_review", "verified", "rejected"}


def migrate_document_columns():
    additions = {
        "document_role": ("documents", "VARCHAR(80)"),
        "mime_type": ("documents", "VARCHAR(120)"),
        "file_size": ("documents", "INTEGER DEFAULT 0"),
        "checksum": ("documents", "VARCHAR(128)"),
        "source": ("documents", "VARCHAR(40) DEFAULT 'customer_portal'"),
        "required": ("documents", "BOOLEAN DEFAULT FALSE"),
        "verified_by": ("documents", "VARCHAR(120)"),
        "verified_at": ("documents", "TIMESTAMP"),
        "rejection_reason": ("documents", "TEXT"),
        "storage_provider": ("documents", "VARCHAR(50)"),
    }
    with engine.begin() as conn:
        for name, (table, sql_type) in additions.items():
            columns = {c["name"] for c in inspect(conn).get_columns(table)}
            if name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
                except Exception:
                    pass


def _document_payload(d: DocumentRecord):
    return {
        "id": d.id, "customer_id": d.customer_id, "loan_id": d.loan_id,
        "document_type": d.document_type, "document_role": d.document_role,
        "file_name": d.file_name, "mime_type": d.mime_type, "file_size": d.file_size or 0,
        "checksum": d.checksum, "source": d.source, "required": bool(d.required),
        "verification_status": d.verification_status, "verified_by": d.verified_by,
        "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        "rejection_reason": d.rejection_reason, "storage_provider": d.storage_provider,
        "storage_key": d.storage_key, "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.post("/register")
def register_document(payload: DocumentCreate, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != payload.customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    customer = db.get(CustomerRecord, payload.customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    if payload.loan_id is not None:
        loan = db.get(LoanRecord, payload.loan_id)
        if not loan or loan.customer_id != payload.customer_id:
            raise HTTPException(400, "Loan does not belong to this customer")
    if payload.verification_status not in DOCUMENT_STATUSES:
        raise HTTPException(400, "Invalid document verification status")
    doc_type = payload.document_type.strip().upper().replace(" ", "_")
    if doc_type not in DOCUMENT_TYPES:
        doc_type = "OTHER"
    values = payload.model_dump()
    values["document_type"] = doc_type
    existing = db.query(DocumentRecord).filter(
        DocumentRecord.customer_id == payload.customer_id,
        DocumentRecord.loan_id == payload.loan_id,
        DocumentRecord.document_type == doc_type,
        DocumentRecord.file_name == payload.file_name,
    ).first()
    if existing:
        for key, value in values.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        if payload.verification_status != "verified":
            existing.verified_by = None
            existing.verified_at = None
        db.commit(); db.refresh(existing)
        return _document_payload(existing)
    doc = DocumentRecord(**values)
    db.add(doc); db.commit(); db.refresh(doc)
    return _document_payload(doc)


@router.get("/customer/{customer_id}")
def customer_document_master(customer_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    if int(claims.get("user_id", -1)) != customer_id:
        raise HTTPException(403, "Customer session does not match this customer")
    if not db.get(CustomerRecord, customer_id):
        raise HTTPException(404, "Customer not found")
    docs = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    return [_document_payload(d) for d in docs]


@router.get("/loan/{loan_id}")
def loan_document_master(loan_id: int, db: Session = Depends(get_db), claims: dict = Depends(get_current_customer)):
    loan = db.get(LoanRecord, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    if int(claims.get("user_id", -1)) != loan.customer_id:
        raise HTTPException(403, "Customer session does not match this loan")
    docs = db.query(DocumentRecord).filter(DocumentRecord.loan_id == loan_id).order_by(DocumentRecord.id.desc()).all()
    return [_document_payload(d) for d in docs]


@router.get("/admin/master")
def admin_document_master(db: Session = Depends(get_db)):
    docs = db.query(DocumentRecord).order_by(DocumentRecord.id.desc()).all()
    return [_document_payload(d) for d in docs]


@router.patch("/admin/{document_id}/verification")
def update_verification(document_id: int, payload: dict, db: Session = Depends(get_db)):
    doc = db.get(DocumentRecord, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    status = str(payload.get("verification_status") or "").lower()
    if status not in DOCUMENT_STATUSES:
        raise HTTPException(400, "Invalid document verification status")
    doc.verification_status = status
    doc.verified_by = payload.get("verified_by")
    doc.rejection_reason = payload.get("rejection_reason")
    doc.verified_at = datetime.now(timezone.utc) if status == "verified" else None
    db.commit(); db.refresh(doc)
    return _document_payload(doc)
