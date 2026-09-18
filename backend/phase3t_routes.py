from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3t_internal_audit import contract,finding
router=APIRouter(prefix="/api/v1/internal-audit",tags=["phase-3t"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/finding")
def make_finding(body:dict,admin=Depends(get_current_admin)): return finding(**body)
