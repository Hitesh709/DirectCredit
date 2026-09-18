from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3p_security import contract,posture
router=APIRouter(prefix="/api/v1/security",tags=["phase-3p"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/posture")
def get_posture(body:dict,admin=Depends(get_current_admin)): return posture(**body)
