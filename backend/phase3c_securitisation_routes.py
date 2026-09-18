from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3c_securitisation import contract, pool

router=APIRouter(prefix="/api/v1/securitisation",tags=["phase-3c"])

@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()

@router.post("/pool")
def get_pool(body:dict,admin=Depends(get_current_admin)): return pool(body.get("loans",[]))
