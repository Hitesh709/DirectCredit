from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3s_regulatory_reporting import contract,report
router=APIRouter(prefix="/api/v1/regulatory-reporting",tags=["phase-3s"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/report")
def make_report(body:dict,admin=Depends(get_current_admin)): return report(**body)
