"""Restrict local service hosts and cross-origin browser access."""
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from settings import DASHBOARD_URL

def configure(app):
    origins=list({DASHBOARD_URL,DASHBOARD_URL.replace('127.0.0.1','localhost')})
    @app.middleware('http')
    async def local_only(request,call_next):
        host=request.headers.get('host','').split(':')[0]
        origin=request.headers.get('origin')
        if host not in ('127.0.0.1','localhost','testserver') or (origin and origin not in origins):
            return JSONResponse({'detail':'Local access only'},status_code=403)
        return await call_next(request)
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST','DELETE'],allow_headers=['Content-Type'])
