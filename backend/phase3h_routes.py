from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3h_collections_ai import contract,recommend
router=APIRouter(prefix="/api/v1/collections-ai",tags=["phase-3h"])
@router.get("/contract")
def c(admin=Depends(get_current_admin)): return contract()
@router.post("/recommend")
def r(body:dict,admin=Depends(get_current_admin)): return recommend(**body)