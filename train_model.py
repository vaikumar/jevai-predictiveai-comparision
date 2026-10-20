import json
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, log_loss, confusion_matrix
from schema import LoginRequest
from policy import ROOT, LABELS, FEATURES, POLICY, features
from synthetic_data import generate

def train():
    records,y=generate(6000,42); test,yt=generate(1200,99)
    x=np.array([features(r) for r in records]); xt=np.array([features(r) for r in test])
    m=XGBClassifier(n_estimators=60,max_depth=3,learning_rate=.1,objective='multi:softprob',num_class=3,n_jobs=2,random_state=42)
    m.fit(x,y);p=m.predict_proba(xt);pred=p.argmax(axis=1)
    metrics={'accuracy':float(accuracy_score(yt,pred)), 'macro_f1':float(f1_score(yt,pred,average='macro')), 'log_loss':float(log_loss(yt,p)), 'confusion_matrix':confusion_matrix(yt,pred).tolist(), 'train_rows':6000,'test_rows':1200,'train_seed':42,'test_seed':99,'labels':LABELS,'features':FEATURES,'policy':POLICY,'class_counts':{k:int((y==i).sum()) for i,k in enumerate(LABELS)},'description':'Synthetic rule imitation with only 16 distinct signal combinations. High accuracy is expected and is not fraud-detection evidence.'}
    (ROOT/'artifacts').mkdir(exist_ok=True);m.save_model(ROOT/'artifacts/model.json')
    (ROOT/'artifacts/metrics.json').write_text(json.dumps(metrics,indent=2))
    for name,rs,ys in [('synthetic-train.jsonl',records,y),('synthetic-test.jsonl',test,yt)]:
        with (ROOT/'artifacts'/name).open('w') as f:
            for r,v in zip(rs,ys): f.write(json.dumps({'request':r,'decision':LABELS[int(v)]})+'\n')
    examples=[LoginRequest(failure_ind=False,device_bounded=True,device_linked=True,credential_remed_manda=False,remember_my_device=True).model_dump(),LoginRequest(failure_ind=True,device_bounded=False,device_linked=False,credential_remed_manda=False,remember_my_device=True).model_dump(),LoginRequest(failure_ind=True,device_bounded=False,device_linked=False,credential_remed_manda=True,remember_my_device=False).model_dump()]
    (ROOT/'static/examples.json').write_text(json.dumps(examples,indent=2))
    (ROOT/'artifacts/sample-request.json').write_text(json.dumps(examples[1],indent=2))
    print(json.dumps(metrics,indent=2))
if __name__=='__main__':train()
