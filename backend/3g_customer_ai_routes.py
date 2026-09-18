from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3g_customer_ai import contract,response
router=APIRouter(prefix="/api/v1/customer-ai",tags=["phase3g_customer_ai"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/evaluate")
def evaluate(body:dict,admin=Depends(get_current_admin)): return response(**body)
