from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3v_autonomous_operations import contract,plan
router=APIRouter(prefix="/api/v1/autonomous-ops",tags=["phase-3v"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/plan")
def make_plan(body:dict,admin=Depends(get_current_admin)): return plan(**body)
