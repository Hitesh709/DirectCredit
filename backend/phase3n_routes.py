from fastapi import APIRouter, Depends
from .admin_auth import get_current_admin
from .phase3n_multi_product import contract,catalog
router=APIRouter(prefix="/api/v1/products",tags=["phase-3n"])
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/catalog")
def get_catalog(body:dict,admin=Depends(get_current_admin)): return catalog(**body)
