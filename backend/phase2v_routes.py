from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from .admin_auth import get_current_admin
from .phase2v_documents import PHASE2V_VERSION,assess_documents,contract
router=APIRouter(prefix="/api/v1/document-intelligence",tags=["phase-2v-document-intelligence"])
class DocumentRequest(BaseModel): documents:list[dict]=Field(default_factory=list)
@router.get("/contract")
def get_contract(admin=Depends(get_current_admin)): return contract()
@router.post("/assess")
def assess(body:DocumentRequest,admin=Depends(get_current_admin)): return assess_documents(body.documents)
@router.get("/version")
def version(admin=Depends(get_current_admin)): return {"version":PHASE2V_VERSION}