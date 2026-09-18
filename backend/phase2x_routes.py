from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2x_tax import PHASE2X_VERSION,reconcile_tax,contract
router=APIRouter(prefix="/api/v1/tax-intelligence",tags=["phase-2x-tax-intelligence"])
class TaxRequest(BaseModel):
 gst_monthly_turnover:float=Field(default=0,ge=0); itr_income:float=Field(default=0,ge=0); bank_monthly_credits:float=Field(default=0,ge=0); gst_filing_status:str="unknown"; months:int=Field(default=0,ge=0)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/reconcile")
def reconcile(body:TaxRequest,admin=Depends(get_current_admin)): return reconcile_tax(**body.model_dump())
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2X_VERSION}