"""Application authentication routes."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord
from .auth import hash_password, verify_password, issue_token, decode_token, get_current_customer
from .schemas import RegisterRequest, LoginRequest, RefreshRequest, PasswordRequest, EmailTokenRequest

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def _customer_payload(c: CustomerRecord) -> dict:
    return {"id": c.id, "customer_code": c.customer_code, "login_id": c.login_id, "name": c.name, "email": c.email, "mobile": c.mobile}


def _tokens(c: CustomerRecord) -> dict:
    return {
        "access_token": issue_token(c.id, "customer", "access", 1, c.session_version or 1),
        "refresh_token": issue_token(c.id, "customer", "refresh", 30, c.session_version or 1),
        "token_type": "bearer",
        "expires_in": 3600,
        "customer": _customer_payload(c),
    }


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    login_id = payload.login_id.strip()
    if db.query(CustomerRecord).filter(CustomerRecord.login_id == login_id).first(): raise HTTPException(409, "Login ID already exists")
    if payload.email and db.query(CustomerRecord).filter(CustomerRecord.email == payload.email).first(): raise HTTPException(409, "Email already exists")
    c = CustomerRecord(login_id=login_id, password_hash=hash_password(payload.password), name=payload.name.strip(), email=payload.email, mobile=payload.mobile, customer_type=payload.customer_type, occupation=payload.occupation, kyc_status="pending", email_verified="pending", selfie_status="pending", session_version=1)
    db.add(c); db.commit(); db.refresh(c); c.customer_code=f"CUST{c.id:08d}"; db.commit(); db.refresh(c)
    verification_token=issue_token(c.id,"customer","email_verify",24,c.session_version)
    result=_tokens(c); result["email_verification_token"]=verification_token; return result


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    c=db.query(CustomerRecord).filter(CustomerRecord.login_id==payload.login_id.strip()).first()
    if not c or not c.password_hash or not verify_password(payload.password,c.password_hash): raise HTTPException(401,"Invalid customer ID or password")
    return _tokens(c)


@router.post("/customer-mobile-login")
def customer_mobile_login(payload: dict, db: Session = Depends(get_db)):
    """Temporary mobile-only access for an existing customer record."""
    raw_mobile=str(payload.get("mobile") or "").strip(); mobile="".join(ch for ch in raw_mobile if ch.isdigit())
    if mobile.startswith("91") and len(mobile)==12: mobile=mobile[2:]
    if len(mobile)!=10: raise HTTPException(422,"Enter a 10-digit mobile number")
    c=db.query(CustomerRecord).filter(CustomerRecord.mobile.in_([mobile, f"+91{mobile}", f"91{mobile}"])).first()
    if not c: raise HTTPException(404,"No customer record is registered for this mobile number")
    return _tokens(c)


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    claims=decode_token(payload.refresh_token,expected_type="refresh")
    if not claims or claims.get("role") != "customer" or "session_version" not in claims: raise HTTPException(401,"Invalid or expired refresh token")
    c=db.get(CustomerRecord,int(claims["user_id"]))
    if not c or int(claims["session_version"]) != int(c.session_version or 1): raise HTTPException(401,"Customer session has been revoked")
    return {"access_token":issue_token(c.id,"customer","access",1,c.session_version or 1),"token_type":"bearer","expires_in":3600}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "): raise HTTPException(401,"Authentication required")
    token=authorization.split(" ",1)[1].strip(); claims=decode_token(token,expected_type="access")
    if not claims or claims.get("role") != "customer": raise HTTPException(401,"Invalid or expired customer session")
    c=db.get(CustomerRecord,int(claims["user_id"]))
    if not c or "session_version" not in claims or int(claims["session_version"]) != int(c.session_version or 1): raise HTTPException(401,"Customer session has already been revoked")
    c.session_version=int(c.session_version or 1)+1; db.commit()
    return {"status":"logged_out","customer_id":c.id}


@router.get("/customer-session")
def customer_session(claims: dict = Depends(get_current_customer)):
    return {"authenticated": True, "customer_id": int(claims["user_id"]), "session_version": int(claims["session_version"])}


@router.post("/verify-email")
def verify_email(payload: EmailTokenRequest, db: Session = Depends(get_db)):
    claims=decode_token(payload.token,expected_type="email_verify")
    if not claims: raise HTTPException(400,"Invalid or expired verification token")
    c=db.get(CustomerRecord,claims["user_id"])
    if not c: raise HTTPException(404,"Customer not found")
    c.email_verified="verified"; db.commit(); return {"status":"verified","customer_id":c.id}


@router.post("/forgot-password")
def forgot_password(payload: EmailTokenRequest, db: Session = Depends(get_db)):
    c=db.query(CustomerRecord).filter(CustomerRecord.email==payload.token.strip()).first()
    if not c: return {"status":"accepted"}
    return {"status":"accepted","reset_token":issue_token(c.id,"customer","password_reset",1,c.session_version or 1)}


@router.post("/reset-password")
def reset_password(payload: PasswordRequest, db: Session = Depends(get_db)):
    claims=decode_token(payload.token,expected_type="password_reset")
    if not claims: raise HTTPException(400,"Invalid or expired reset token")
    c=db.get(CustomerRecord,claims["user_id"])
    if not c: raise HTTPException(404,"Customer not found")
    c.password_hash=hash_password(payload.new_password); c.session_version=int(c.session_version or 1)+1; db.commit(); return {"status":"password_reset"}
