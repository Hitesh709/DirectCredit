from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3b_investor_reporting import contract,report
router=APIRouter(prefix="/api/v1/investor-reporting",tags=["phase3b_investor_reporting"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/evaluate")
def evaluate(body:dict,admin=Depends(get_current_admin)): return report(**body)
