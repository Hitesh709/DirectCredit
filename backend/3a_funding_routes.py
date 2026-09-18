from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3a_funding import contract,funding_capacity
router=APIRouter(prefix="/api/v1/funding",tags=["phase3a_funding"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/evaluate")
def evaluate(body:dict,admin=Depends(get_current_admin)): return funding_capacity(**body)
