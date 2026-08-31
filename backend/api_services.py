from fastapi import APIRouter
from .provider_gateway import provider_status, result
from .verification import validate_pan, validate_aadhaar

router = APIRouter(prefix="/api/services", tags=["verification-services"])

@router.get("/status")
def services_status():
    return {"services": provider_status()}

@router.post("/pan/validate")
def pan_validate(pan: str):
    return result("pan", validate_pan(pan))

@router.post("/aadhaar/validate")
def aadhaar_validate(aadhaar: str):
    return result("aadhaar", validate_aadhaar(aadhaar))
