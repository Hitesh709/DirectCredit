from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3f_experimentation import contract, assign

router=APIRouter(prefix="/api/v1/experiments",tags=["phase-3f"])

@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()

@router.post("/assign")
def assign_variant(body:dict,admin=Depends(get_current_admin)):
    return assign(body.get("experiment_id"),body.get("subject_id"),body.get("variants",[]))
