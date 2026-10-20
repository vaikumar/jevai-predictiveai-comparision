"""Standalone predictive inference service. Start on port 8001."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from schema import LoginRequest
from predictor import load_model, predict, training_metrics
from service_security import configure

@asynccontextmanager
async def lifespan(app):
    load_model()
    predict(LoginRequest(failure_ind=False,device_bounded=True,device_linked=True,credential_remed_manda=False,remember_my_device=True))
    yield
app=FastAPI(title='Predictive AI service',lifespan=lifespan)
configure(app)
@app.get('/health')
def health():return {'status':'ok','service':'predictive'}
@app.get('/api/status')
def status():return {'training':training_metrics()}
@app.post('/api/predict')
def prediction(request:LoginRequest):return predict(request)
