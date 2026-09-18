from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3k_events import contract,event
router=APIRouter(prefix="/api/v1/events",tags=["phase-3k"])
@router.get("/contract")
def c(admin=Depends(get_current_admin)): return contract()
@router.post("/event")
def e(body:dict,admin=Depends(get_current_admin)): return event(**body)