"""Task 5: complete application authentication without requiring an email vendor.
Email/forgot-password endpoints generate signed one-time tokens. In production, deliver
those tokens through the company's approved email/SMS provider instead of returning them.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from .database import get_db
from .db_models import CustomerRecord
from .auth import hash_password, verify_password, issue_token, decode_token, revoke_token
from .schemas import RegisterRequest, LoginRequest, RefreshRequest, PasswordRequest, EmailTokenRequest

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    login_id = payload.login_id.strip()
    if db.query(CustomerRecord).filter(CustomerRecord.login_id == login_id).first():
        raise HTTPException(409, "Login ID already exists")
    if payload.email and db.query(CustomerRecord).filter(CustomerRecord.email == payload.email).first():
        raise HTTPException(409, "Email already exists")
    c = CustomerRecord(login_id=login_id, password_hash=hash_password(payload.password), name=payload.name.strip(), email=payload.email, mobile=payload.mobile, customer_type=payload.customer_type, occupation=payload.occupation, kyc_status="pending", email_verified="pending", selfie_status="pending")
    db.add(c); db.commit(); db.refresh(c)
    c.customer_code = f"CUST{c.id:08d}"; db.commit(); db.refresh(c)
    verification_token = issue_token(c.id, "customer", "email_verify", 24)
    return {"customer": {"id": c.id, "customer_code": c.customer_code, "login_id": c.login_id, "name": c.name, "email": c.email}, "access_token": issue_token(c.id, "customer", "access", 1), "refresh_token": issue_token(c.id, "customer", "refresh", 30), "email_verification_token": verification_token}

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    c = db.query(CustomerRecord).filter(CustomerRecord.login_id == payload.login_id.strip()).first()
    if not c or not c.password_hash or not verify_password(payload.password, c.password_hash):
        raise HTTPException(401, "Invalid customer ID or password")
    return {"access_token": issue_token(c.id, "customer", "access", 1), "refresh_token": issue_token(c.id, "customer", "refresh", 30), "token_type": "bearer", "expires_in": 3600}

@router.post("/refresh")
def refresh(payload: RefreshRequest):
    claims = decode_token(payload.refresh_token, expected_type="refresh")
    if not claims: raise HTTPException(401, "Invalid or expired refresh token")
    return {"access_token": issue_token(claims["user_id"], claims["role"], "access", 1), "token_type": "bearer", "expires_in": 3600}

@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_token(token)
    if not claims: raise HTTPException(401, "Invalid or expired token")
    revoke_token(token)
    return {"status": "logged_out"}

@router.post("/verify-email")
def verify_email(payload: EmailTokenRequest, db: Session = Depends(get_db)):
    claims = decode_token(payload.token, expected_type="email_verify")
    if not claims: raise HTTPException(400, "Invalid or expired verification token")
    c = db.get(CustomerRecord, claims["user_id"])
    if not c: raise HTTPException(404, "Customer not found")
    c.email_verified = "verified"; db.commit()
    return {"status": "verified", "customer_id": c.id}

@router.post("/forgot-password")
def forgot_password(payload: EmailTokenRequest, db: Session = Depends(get_db)):
    c = db.query(CustomerRecord).filter(CustomerRecord.email == payload.token.strip()).first()
    # Do not disclose whether an email exists in a production UI. The token is returned
    # here only for local/demo testing because no external email service is configured.
    if not c: return {"status": "accepted"}
    return {"status": "accepted", "reset_token": issue_token(c.id, "customer", "password_reset", 1)}

@router.post("/reset-password")
def reset_password(payload: PasswordRequest, db: Session = Depends(get_db)):
    claims = decode_token(payload.token, expected_type="password_reset")
    if not claims: raise HTTPException(400, "Invalid or expired reset token")
    c = db.get(CustomerRecord, claims["user_id"])
    if not c: raise HTTPException(404, "Customer not found")
    c.password_hash = hash_password(payload.new_password); db.commit()
    return {"status": "password_reset"}
