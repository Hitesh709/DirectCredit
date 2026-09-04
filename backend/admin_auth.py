from typing import Optional
import os
from fastapi import Header, HTTPException
from .auth import decode_token

def get_current_admin(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Admin authentication required")
    token = authorization.split(" ", 1)[1].strip()
    # Preferred: signed application token carrying role=admin.
    claims = decode_token(token, expected_type="access")
    if claims and claims.get("role") == "admin":
        return claims
    # Optional machine/admin token for operations where an admin principal is not yet provisioned.
    configured = os.getenv("ADMIN_API_TOKEN", "").strip()
    if configured and token == configured:
        return {"role": "admin", "user_id": "configured-admin", "type": "access"}
    raise HTTPException(403, "Admin role required")
