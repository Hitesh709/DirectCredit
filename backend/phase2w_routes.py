from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2w_cashflow import PHASE2W_VERSION,analyze_transactions,contract
router=APIRouter(prefix="/api/v1/cashflow",tags=["phase-2w-cashflow"])
class CashflowRequest(BaseModel): transactions:list[dict]=Field(default_factory=list)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/analyze")
def analyze(body:CashflowRequest,admin=Depends(get_current_admin)): return analyze_transactions(body.transactions)
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2W_VERSION}