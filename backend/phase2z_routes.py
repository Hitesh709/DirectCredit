from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2z_treasury import PHASE2Z_VERSION,liquidity,contract
router=APIRouter(prefix="/api/v1/treasury",tags=["phase-2z-treasury"])
class TreasuryRequest(BaseModel):
 cash:float=Field(default=0,ge=0); expected_disbursements:float=Field(default=0,ge=0); expected_collections:float=Field(default=0,ge=0); funding_available:float=Field(default=0,ge=0)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/liquidity")
def liquidity_route(body:TreasuryRequest,admin=Depends(get_current_admin)): return liquidity(**body.model_dump())
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2Z_VERSION}