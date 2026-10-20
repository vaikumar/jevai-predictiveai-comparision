"""Standalone JEV service. Only this process holds the provider credential."""
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from schema import LoginRequest
from service_security import configure
from settings import JEV_ENDPOINT, JEV_MODEL
import jev_client

class SettingsRequest(BaseModel):
    api_key:str=Field(min_length=1,max_length=512)
@asynccontextmanager
async def lifespan(app):
    jev_client.client=httpx.AsyncClient(timeout=20,follow_redirects=False)
    yield
    await jev_client.client.aclose()
app=FastAPI(title='JEV AI service',lifespan=lifespan)
configure(app)
@app.get('/health')
def health():return {'status':'ok','service':'jev'}
@app.get('/api/status')
def status():return {'jev_configured':bool(jev_client.key),'jev_endpoint':JEV_ENDPOINT,'model':JEV_MODEL}
@app.post('/api/jev')
async def decision(request:LoginRequest):return await jev_client.jev(request)
@app.post('/api/settings')
async def settings(request:SettingsRequest):
    candidate=jev_client.normalize_key(request.api_key)
    example=LoginRequest(failure_ind=False,device_bounded=True,device_linked=True,credential_remed_manda=False,remember_my_device=True)
    result=await jev_client.jev(example,api_key=candidate)
    if result['status']!='ok':raise HTTPException(400,result['error'])
    jev_client.key=candidate
    return {'configured':True,'verified':True}
@app.delete('/api/settings')
def disconnect():
    jev_client.key=''
    return {'configured':False}
