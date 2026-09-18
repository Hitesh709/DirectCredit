from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3d_pricing import contract, profitability

router=APIRouter(prefix="/api/v1/pricing",tags=["phase-3d"])

@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()

@router.post("/profitability")
def get_profitability(body:dict,admin=Depends(get_current_admin)): return profitability(**body)
