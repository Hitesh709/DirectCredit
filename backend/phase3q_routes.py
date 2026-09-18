from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3q_disaster_recovery import contract,recovery_status
router=APIRouter(prefix="/api/v1/disaster-recovery",tags=["phase-3q"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/status")
def get_status(body:dict,admin=Depends(get_current_admin)): return recovery_status(**body)
