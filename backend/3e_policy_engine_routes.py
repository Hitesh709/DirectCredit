from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3e_policy_engine import contract,evaluate_rules
router=APIRouter(prefix="/api/v1/dynamic-policy",tags=["phase3e_policy_engine"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/evaluate")
def evaluate(body:dict,admin=Depends(get_current_admin)): return evaluate_rules(**body)
