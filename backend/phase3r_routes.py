from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3r_observability import contract,health
router=APIRouter(prefix="/api/v1/observability",tags=["phase-3r"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/health")
def get_health(body:dict,admin=Depends(get_current_admin)): return health(**body)
