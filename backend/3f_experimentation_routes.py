from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3f_experimentation import contract,assign
router=APIRouter(prefix="/api/v1/experiments",tags=["phase3f_experimentation"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/evaluate")
def evaluate(body:dict,admin=Depends(get_current_admin)): return assign(**body)
