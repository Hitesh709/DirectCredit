from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3i_operations_ai import contract,prioritize
router=APIRouter(prefix="/api/v1/operations-ai",tags=["phase-3i"])
@router.get("/contract")
def c(admin=Depends(get_current_admin)): return contract()
@router.post("/prioritize")
def r(body:dict,admin=Depends(get_current_admin)): return prioritize(**body)