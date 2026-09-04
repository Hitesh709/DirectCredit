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

def install_security(app):
    @app.middleware('http')
    async def security_middleware(request:Request,call_next):
        if request.url.path not in {'/health','/'}:
            key=request.client.host if request.client else 'unknown'
            if not limiter.allowed(key): return JSONResponse(status_code=429,content={'detail':'Rate limit exceeded'})
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
def security_contract(): return {'rate_limit_per_ip_per_minute':limiter.limit,'security_headers':True,'secrets_from_environment':True,'sensitive_data_logging_policy':'do not log credentials, full PAN/Aadhaar or tokens'}
