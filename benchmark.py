import asyncio, time, uuid
import numpy as np
from fastapi import HTTPException
from policy import LABELS
from schema import LoginRequest as Customer
from synthetic_data import generate
from service_clients import predictive_request, jev_request, jev_status
busy = asyncio.Lock()

def summarize(rows,engine,elapsed):
    results=[r[engine] for r in rows]; ok=[(r,r[engine]) for r in rows if r[engine]['status']=='ok']
    lat=[v['latency_ms'] for _,v in ok]
    return {'attempts':len(rows),'successes':len(ok),'errors':sum(r['status']=='error' for r in results),'skipped':sum(r['status']=='unconfigured' for r in results),'success_rate':len(ok)/len(rows),'p50_ms':float(np.percentile(lat,50)) if lat else None,'p95_ms':float(np.percentile(lat,95)) if lat else None,'accuracy':sum(v['recommendation']==r['expected'] for r,v in ok)/len(ok) if ok else None,'correct_per_attempt':sum(v['recommendation']==r['expected'] for r,v in ok)/len(rows),'macro_f1':None,'run_successes_per_second':len(ok)/elapsed}

async def benchmark(b):
    if busy.locked(): raise HTTPException(409,'A benchmark is already running')
    if b.include_jev and not (await jev_status()).get('jev_configured'): raise HTTPException(400,'Configure JEV before running a paired benchmark')
    async with busy:
        x,y=generate(1200,99); rows=[]; started=time.perf_counter()
        for i in range(b.count):
            c=Customer(**x[i])
            a,d=await asyncio.gather(predictive_request(c),jev_request(c) if b.include_jev else asyncio.sleep(0,result={'status':'unconfigured','latency_ms':None}))
            rows.append({'request':c.model_dump(),'expected':LABELS[int(y[i])],'xgboost':a,'jev':d})
        elapsed=time.perf_counter()-started
        summary={e:summarize(rows,e,elapsed) for e in ('xgboost','jev')}
        from sklearn.metrics import f1_score
        for e in summary:
            good=[r for r in rows if r[e]['status']=='ok']
            if good: summary[e]['macro_f1']=float(f1_score([r['expected'] for r in good],[r[e]['recommendation'] for r in good],labels=LABELS,average='macro',zero_division=0))
        paired=[r for r in rows if r['jev']['status']=='ok' and r['xgboost']['status']=='ok']
        return {'run_id':str(uuid.uuid4()),'timestamp':time.time(),'count':b.count,'elapsed_seconds':elapsed,'summary':summary,'agreement':sum(r['xgboost']['recommendation']==r['jev']['recommendation'] for r in paired)/len(paired) if paired else None,'rows':rows,'methodology':'Fixed synthetic holdout seed 99; warmed local model; paired calls concurrent, rows sequential; service latency excludes browser transport; JEV includes upstream network; no retries; accuracy/F1 use successful responses only; correct_per_attempt includes failures. Throughput is whole-run completion rate, not capacity.'}
