"""HTTP invocation of independent backend services for benchmark/gateway."""
import httpx
from fastapi import HTTPException
from settings import PREDICTIVE_URL,JEV_URL
client=None
async def call(base,path,data=None,method='POST'):
    try:
        response=await client.request(method,base+path,json=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code,'Backend rejected the request') from None
    except (httpx.RequestError,ValueError):
        raise HTTPException(503,'Backend service unavailable: '+base) from None
async def invocation(base,path,request):
    try:return await call(base,path,request.model_dump())
    except HTTPException as e:return {'status':'error','error':e.detail,'latency_ms':None}
async def predictive_request(request):return await invocation(PREDICTIVE_URL,'/api/predict',request)
async def jev_request(request):return await invocation(JEV_URL,'/api/jev',request)
async def jev_status():return await call(JEV_URL,'/api/status',method='GET')
