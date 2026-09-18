from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3u_model_governance import contract,register
router=APIRouter(prefix="/api/v1/model-governance",tags=["phase-3u"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/register")
def register_model(body:dict,admin=Depends(get_current_admin)): return register(**body)
