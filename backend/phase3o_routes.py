from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3o_repeat_borrower import contract,profile
router=APIRouter(prefix="/api/v1/repeat-borrower",tags=["phase-3o"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/profile")
def get_profile(body:dict,admin=Depends(get_current_admin)): return profile(**body)
