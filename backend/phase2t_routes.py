from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from .admin_auth import get_current_admin
from .phase2t_risk import PHASE2T_VERSION, calculate_risk, risk_contract

router = APIRouter(prefix="/api/v1/credit-risk", tags=["phase-2t-credit-risk"])

class RiskRequest(BaseModel):
    scorecard_score: float = 0
    scorecard_max: float = 125
    foir: float = 0
    cibil_score: int = 0
    bank_bounces_3m: int = Field(default=0, ge=0)
    ecs_returns_12m: int = Field(default=0, ge=0)
    business_vintage_years: float = Field(default=0, ge=0)
    active_dpd: bool = False
    fraud_score: float = Field(default=0, ge=0, le=100)
    overdue_amount: float = Field(default=0, ge=0)
    sanctioned_amount: float = Field(default=0, ge=0)
    outstanding_amount: float = Field(default=0, ge=0)
    pd_override: float | None = Field(default=None, ge=0, le=1)
    lgd_override: float | None = Field(default=None, ge=0, le=1)
    ead_override: float | None = Field(default=None, ge=0)

@router.get("/contract")
def contract(admin=Depends(get_current_admin)): return risk_contract()

@router.post("/evaluate")
def evaluate(body: RiskRequest, admin=Depends(get_current_admin)):
    return {**calculate_risk(**body.model_dump()), "engine_version": PHASE2T_VERSION}

@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version": PHASE2T_VERSION}
