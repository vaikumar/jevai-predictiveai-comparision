"""Serve dashboard assets/configuration and coordinate benchmark HTTP calls."""
import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from settings import ROOT,CONFIG,PREDICTIVE_URL
from schema import LoginRequest
from service_security import configure
import service_clients
from benchmark import benchmark

class BenchmarkRequest(BaseModel):
    count:int=Field(default=20,ge=5,le=100)
    include_jev:bool=False
@asynccontextmanager
async def lifespan(app):
    service_clients.client=httpx.AsyncClient(timeout=25,follow_redirects=False)
    yield
    await service_clients.client.aclose()
app=FastAPI(title='Decision Lab dashboard and benchmarks',lifespan=lifespan)
configure(app)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
@app.get('/health')
def health():return {'status':'ok','service':'dashboard'}
@app.get('/api/config')
def config():return CONFIG
@app.get('/api/status')
async def status():
    a,b=await asyncio.gather(service_clients.call(PREDICTIVE_URL,'/api/status',method='GET'),service_clients.jev_status())
    return {**a,**b}
@app.post('/api/compare')
async def compare(request:LoginRequest):
    a,b=await asyncio.gather(service_clients.predictive_request(request),service_clients.jev_request(request))
    return {'request':request.model_dump(),'xgboost':a,'jev':b}
@app.post('/api/benchmark')
async def run_benchmark(request:BenchmarkRequest):return await benchmark(request)
