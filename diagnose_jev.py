"""Credential-safe authentication check, independent of dashboard and inference."""
import getpass, os
import httpx
from fastapi import HTTPException
from jev_client import normalize_key

def main():
    token=os.environ.get('TYPESAFE_API_KEY','') or getpass.getpass('TypeSafe API key (hidden): ')
    try:token=normalize_key(token)
    except HTTPException:
        print('Invalid formatting: use only the complete token.');return 2
    proxy_present=any(os.environ.get(k) for k in ('HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','https_proxy','http_proxy','all_proxy'))
    print('Target: https://api.typesafe.ai/v1/models')
    print('Proxy environment configured:',proxy_present)
    try:
        with httpx.Client(timeout=20,follow_redirects=False) as client:
            r=client.get('https://api.typesafe.ai/v1/models',headers={'Authorization':'Bearer '+token})
        print('HTTP status:',r.status_code)
        if r.status_code==200:
            data=r.json()
            valid=isinstance(data,dict) and isinstance(data.get('models'),list)
            if not valid:print('Unexpected response shape; authentication is not confirmed.');return 1
            available=any(isinstance(m,dict) and m.get('name')=='jev-latest' for m in data['models'])
            print('Authenticated model listing received. jev-latest available:',available)
            print('If dashboard inference still fails, check the JEV service environment and model access.')
            return 0
        if r.status_code==401:print('Authentication rejected independently of the dashboard and login JSON. Check issuer, account, endpoint or gateway with provider support.')
        elif r.status_code==403:print('Access denied; check account permissions with the provider.')
        elif 300<=r.status_code<400:print('Redirect received. Not followed; no credential forwarded.')
        else:print('Provider did not return a successful model listing.')
        return 1
    except (httpx.RequestError,ValueError):
        print('Connection or response decoding failed. No credential or response body is displayed.');return 1
if __name__=='__main__':raise SystemExit(main())
