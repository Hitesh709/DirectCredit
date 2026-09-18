from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3w_self_improving import contract,improvement_cycle
router=APIRouter(prefix="/api/v1/self-improving",tags=["phase-3w"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/cycle")
def run_cycle(body:dict,admin=Depends(get_current_admin)): return improvement_cycle(**body)
