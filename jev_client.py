import os, time, math
import httpx
from fastapi import HTTPException
from policy import FEATURES, LABELS, POLICY, CRITERIA
from settings import JEV_ENDPOINT, JEV_MODEL
key = os.environ.get("TYPESAFE_API_KEY", "").strip()
client = None

def normalize_key(value):
    value=value.strip()
    # Handle both quoted tokens and quoted Authorization header values.
    for _ in range(2):
        if len(value)>=2 and value[0]==value[-1] and value[0] in ('"', "'"):
            value=value[1:-1].strip()
        if value.lower().startswith('bearer '):value=value[7:].strip()
    if not value or any(ch.isspace() or ord(ch)<32 or ord(ch)==127 for ch in value) or not value.isascii():
        raise HTTPException(400,'Paste only the API key, without spaces or line breaks.')
    return value

def payload(c):
    return {'model':JEV_MODEL,'state':{f:getattr(c,f) for f in FEATURES},'questions':{'recommendation':{'type':'choice','instructions':'Classify this login using this demonstration policy. '+POLICY,'criteria':CRITERIA}}}

async def jev(c, api_key=None):
    request_key=key if api_key is None else api_key
    if not request_key: return {'status':'unconfigured','error':'Configure a TypeSafe API key to measure JEV.','latency_ms':None}
    try: request_key=normalize_key(request_key)
    except HTTPException:
        return {'status':'error','error':'API key has invalid formatting. Supply only the token.','latency_ms':None}
    start=time.perf_counter()
    try:
        r=await client.post(JEV_ENDPOINT,json=payload(c),headers={'Authorization':'Bearer '+request_key})
        r.raise_for_status(); data=r.json(); a=data['answers']['recommendation']; p=a['probabilities']
        if a['choice'] not in LABELS or set(p)!=set(LABELS) or any(type(v) not in (float,int) or not math.isfinite(v) or v<0 or v>1 for v in p.values()) or abs(sum(p.values())-1)>.02: raise ValueError()
        return {'status':'ok','decision':a['choice'], 'recommendation':a['choice'],'probabilities':p,'latency_ms':(time.perf_counter()-start)*1000,'model':data.get('model','jev-latest'),'usage':data.get('usage')}
    except httpx.HTTPStatusError as e:
        code=e.response.status_code
        error={401:'Authentication rejected (401) by api.typesafe.ai. This does not identify the cause. Confirm the key issuer and endpoint, or run ./diagnose_jev.sh to test authentication separately from inference.',403:'JEV access denied (403). Check your TypeSafe account permissions and model access.',429:'JEV rate limit or quota reached (429). Check your TypeSafe account usage before retrying.'}.get(code,f'JEV returned HTTP {code}')
    except httpx.TimeoutException: error='JEV timed out after 20 seconds'
    except (ValueError,KeyError,TypeError): error='JEV returned an invalid choice response'
    except httpx.RequestError: error='JEV connection failed'
    return {'status':'error','error':error,'latency_ms':(time.perf_counter()-start)*1000}

