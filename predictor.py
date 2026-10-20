import json, time
import numpy as np
from xgboost import XGBClassifier
from policy import ROOT, LABELS, features
model = XGBClassifier()

def load_model():
    if not (ROOT / "artifacts/model.json").exists():
        raise RuntimeError("Model missing. Run ./train.sh before starting the predictive service.")
    model.load_model(ROOT / "artifacts/model.json")

def training_metrics():
    return json.loads((ROOT / "artifacts/metrics.json").read_text())

def predict(c):
    start=time.perf_counter()
    p=model.predict_proba(np.array([features(c)]))[0]
    return {'status':'ok','decision':LABELS[int(p.argmax())], 'recommendation':LABELS[int(p.argmax())],'probabilities':dict(zip(LABELS,map(float,p))),'latency_ms':(time.perf_counter()-start)*1000,'model':'xgboost-login-demo-v2'}

