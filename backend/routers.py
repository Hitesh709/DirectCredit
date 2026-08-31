from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from typing import Optional
from .auth import decode_demo_token

router = APIRouter(prefix="/api")

def require_role(role: str):
    def dependency(authorization: Optional[str] = Header(default=None)):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        token = authorization.split(" ", 1)[1]
        claims = decode_demo_token(token)
        if not claims or claims["role"] != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims
    return dependency

@router.post("/auth/demo-login")
def demo_login(user_id: int = 1, role: str = "customer"):
    if role not in {"customer", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    from .auth import issue_demo_token
    return {"access_token": issue_demo_token(user_id, role), "token_type": "bearer", "role": role}

@router.get("/customer/me")
def customer_me(claims=Depends(require_role("customer"))):
    return {"user_id": claims["user_id"], "role": "customer"}

@router.get("/admin/me")
def admin_me(claims=Depends(require_role("admin"))):
    return {"user_id": claims["user_id"], "role": "admin"}

@router.post("/customer/documents")
async def upload_document(file: UploadFile = File(...), claims=Depends(require_role("customer"))):
    # Demo mode: metadata only. Secure object storage is required before production.
    return {"status": "received", "customer_id": claims["user_id"], "file_name": file.filename, "document_type": "pending_verification"}
