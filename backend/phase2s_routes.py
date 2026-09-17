from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from .admin_auth import get_current_admin
from .phase2s_fraud import PHASE2S_VERSION, fraud_contract, evaluate_fraud

router = APIRouter(prefix="/api/v1/fraud", tags=["phase-2s-fraud"])

class FraudRequest(BaseModel):
    device_fingerprint: str | None = None
    ip_address: str | None = None
    mobile: str | None = None
    pan: str | None = None
    bank_account_fingerprint: str | None = None
    linked_customer_count: int = Field(default=0, ge=0)
    application_count_24h: int = Field(default=0, ge=0)
    application_count_7d: int = Field(default=0, ge=0)
    identity_match: str | None = None
    bank_owner_match: str | None = None
    geo_distance_km: float | None = Field(default=None, ge=0)
    suspicious_transactions: int = Field(default=0, ge=0)
    duplicate_document_count: int = Field(default=0, ge=0)
    external_signals: list[dict] = Field(default_factory=list)

@router.get("/contract")
def contract(admin=Depends(get_current_admin)):
    return fraud_contract()

@router.post("/evaluate")
def evaluate(body: FraudRequest, admin=Depends(get_current_admin)):
    return evaluate_fraud(**body.model_dump())

@router.get("/version")
def version(admin=Depends(get_current_admin)):
    return {"version": PHASE2S_VERSION}
