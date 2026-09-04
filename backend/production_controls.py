import os,time
from collections import defaultdict,deque
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse

class RateLimiter:
    def __init__(self,limit=120,window=60): self.limit,self.window=limit,window; self.hits=defaultdict(deque)
    def allowed(self,key):
        now=time.time(); q=self.hits[key]
        while q and now-q[0]>self.window: q.popleft()
        if len(q)>=self.limit:return False
        q.append(now); return True
limiter=RateLimiter()

# Legacy endpoints in main.py predate the role-scoped routers. Keep the guard
# here so an old route cannot bypass the production authorization boundary.
LEGACY_ADMIN_PREFIXES=("/api/admin/", "/admin-data/")
LEGACY_CUSTOMER_PREFIXES=("/api/loans", "/api/documents")
LEGACY_PUBLIC=("/api/customer/login", "/api/version", "/health", "/")

def _claims_from_request(request:Request):
    from .auth import decode_token
    authorization=request.headers.get("authorization","")
    if not authorization.lower().startswith("bearer "):
        return None
    return decode_token(authorization.split(" ",1)[1].strip(), expected_type="access")

def _auth_guard(request:Request):
    path=request.url.path
    if path in LEGACY_PUBLIC:
        return None
    if path.startswith(LEGACY_ADMIN_PREFIXES):
        claims=_claims_from_request(request)
        if not claims or claims.get("role")!="admin":
            return JSONResponse(status_code=401,content={"detail":"Admin authentication required"})
    # Legacy loan/document routes are authenticated at the transport boundary.
    # Fine-grained customer ownership remains enforced by the canonical routers.
    if path.startswith(LEGACY_CUSTOMER_PREFIXES):
        claims=_claims_from_request(request)
        if not claims or claims.get("role") not in {"customer","admin"}:
            return JSONResponse(status_code=401,content={"detail":"Authentication required"})
    return None

def install_security(app):
    @app.middleware('http')
    async def security_middleware(request:Request,call_next):
        if request.url.path not in {'/health','/'}:
            key=request.client.host if request.client else 'unknown'
            if not limiter.allowed(key): return JSONResponse(status_code=429,content={'detail':'Rate limit exceeded'})
        guard=_auth_guard(request)
        if guard is not None: return guard
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'no-cache'
        if request.url.scheme=='https': response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
        return response

router=APIRouter(prefix='/api/admin/phase-76-100',tags=['production-readiness'])
@router.get('/security')
def security_contract(): return {'rate_limit_per_ip_per_minute':limiter.limit,'security_headers':True,'secrets_from_environment':True,'sensitive_data_logging_policy':'do not log credentials, full PAN/Aadhaar or tokens','legacy_route_authentication':True}
