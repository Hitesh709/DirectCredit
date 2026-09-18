from fastapi import APIRouter,Depends
from .admin_auth import get_current_admin
from .phase3j_data_platform import contract,dataset_contract,quality
router=APIRouter(prefix="/api/v1/data-platform",tags=["phase-3j"])
@router.get("/contract")
def c(admin=Depends(get_current_admin)): return contract()
@router.post("/dataset")
def d(body:dict,admin=Depends(get_current_admin)): return dataset_contract(**body)
@router.post("/quality")
def q(body:dict,admin=Depends(get_current_admin)): return quality(**body)