from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3l_api_platform import contract
router=APIRouter(prefix="/api/v1/api-platform",tags=["phase-3l"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
