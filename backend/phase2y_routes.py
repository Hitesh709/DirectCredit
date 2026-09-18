from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2y_portfolio_risk import PHASE2Y_VERSION,aggregate,contract
router=APIRouter(prefix="/api/v1/portfolio-risk",tags=["phase-2y-portfolio-risk"])
class PortfolioRequest(BaseModel): loans:list[dict]=Field(default_factory=list)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/aggregate")
def aggregate_route(body:PortfolioRequest,admin=Depends(get_current_admin)): return aggregate(body.loans)
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2Y_VERSION}