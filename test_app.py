import itertools,unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
import predictive_api,jev_api,dashboard_api,jev_client,service_clients
from policy import FEATURES,LABELS,label
BODY={'failure_ind':False,'device_bounded':True,'device_linked':True,'credential_remed_manda':False,'remember_my_device':True}
class ServiceTests(unittest.TestCase):
    def test_prediction_and_validation(self):
        with TestClient(predictive_api.app) as c:
            for values in itertools.product([False,True],repeat=4):
                body={**BODY,**dict(zip(FEATURES,values))}
                self.assertEqual(c.post('/api/predict',json=body).json()['decision'],LABELS[label(body)])
            for body in [{},dict(BODY,failure_ind='true'),dict(BODY,unknown=1)]:self.assertEqual(c.post('/api/predict',json=body).status_code,422)
            self.assertEqual(c.post('/api/predict',json=dict(BODY,gps='0,0')).json()['decision'],'allow')
    def test_key_normalization(self):
        for token in ['test-key',' Bearer test-key ', '\"Bearer test-key\"', "Bearer 'test-key'"]:
            self.assertEqual(jev_client.normalize_key(token),'test-key')
        from fastapi import HTTPException
        for token in ['','test\nkey','test\x00key']:
            with self.assertRaises(HTTPException):jev_client.normalize_key(token)

    def test_cors_and_origin(self):
        with TestClient(predictive_api.app) as c:
            r=c.options('/api/predict',headers={'origin':'http://127.0.0.1:8000','access-control-request-method':'POST','access-control-request-headers':'content-type'})
            self.assertEqual(r.status_code,200);self.assertEqual(r.headers['access-control-allow-origin'],'http://127.0.0.1:8000')
            self.assertEqual(c.post('/api/predict',json=BODY,headers={'origin':'https://evil.example'}).status_code,403)
    def test_jev_verification_and_errors(self):
        jev_client.key=''
        with TestClient(jev_api.app) as c:
            self.assertEqual(c.post('/api/jev',json=BODY).json()['status'],'unconfigured')
            async def reply(url,**kw):
                self.assertEqual(kw['headers']['Authorization'],'Bearer test-key')
                self.assertEqual(set(kw['json']['state']),set(FEATURES))
                return httpx.Response(200,json={'answers':{'recommendation':{'choice':'allow','probabilities':{'allow':.8,'Challenge':.1,'Block':.1}}}},request=httpx.Request('POST',url))
            with patch.object(jev_client.client,'post',side_effect=reply):
                self.assertEqual(c.post('/api/settings',json={'api_key':'Bearer test-key'}).status_code,200)
                self.assertEqual(c.post('/api/jev',json=BODY).json()['decision'],'allow')
            async def fail(url,**kw):return httpx.Response(401,request=httpx.Request('POST',url))
            with patch.object(jev_client.client,'post',side_effect=fail):
                r=c.post('/api/settings',json={'api_key':'replacement'})
                self.assertEqual(r.status_code,400);self.assertNotIn('replacement',r.text)
                self.assertEqual(jev_client.key,'test-key')
            c.delete('/api/settings');self.assertFalse(c.get('/api/status').json()['jev_configured'])
    def test_gateway_uses_http_services(self):
        with TestClient(dashboard_api.app) as c:
            async def reply(method,url,json=None):
                return httpx.Response(200,json={'status':'ok','recommendation':'allow','decision':'allow','latency_ms':1},request=httpx.Request(method,url))
            with patch.object(service_clients.client,'request',side_effect=reply) as calls:
                r=c.post('/api/compare',json=BODY).json();self.assertEqual(r['xgboost']['decision'],'allow');self.assertEqual(calls.call_count,2)
                urls={v.args[1] for v in calls.call_args_list}
                self.assertEqual(urls,{'http://127.0.0.1:8001/api/predict','http://127.0.0.1:8002/api/jev'})
                b=c.post('/api/benchmark',json={'count':5,'include_jev':False}).json()
                self.assertEqual(b['summary']['xgboost']['successes'],5);self.assertEqual(b['summary']['jev']['skipped'],5)
            async def down(*a,**kw):raise httpx.ConnectError('offline')
            with patch.object(service_clients.client,'request',side_effect=down):
                self.assertEqual(c.post('/api/compare',json=BODY).json()['xgboost']['status'],'error')
if __name__=='__main__':unittest.main()
