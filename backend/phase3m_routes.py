from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3m_partner_ecosystem import contract,onboard
router=APIRouter(prefix="/api/v1/partners",tags=["phase-3m"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/onboard")
def do_onboard(body:dict,admin=Depends(get_current_admin)): return onboard(**body)
