from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2u_underwriting import PHASE2U_VERSION,underwriting_summary,contract
router=APIRouter(prefix="/api/v1/underwriting-ai",tags=["phase-2u-underwriting-ai"])
class UnderwritingRequest(BaseModel):
 customer:dict=Field(default_factory=dict); loan:dict=Field(default_factory=dict); risk:dict=Field(default_factory=dict); compliance:dict=Field(default_factory=dict); fraud:dict=Field(default_factory=dict); evidence:dict=Field(default_factory=dict)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/summary")
def summary(body:UnderwritingRequest,admin=Depends(get_current_admin)): return underwriting_summary(**body.model_dump())
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2U_VERSION}