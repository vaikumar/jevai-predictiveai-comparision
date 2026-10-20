"""Run all three services, or one named service; stop children on exit."""
import os,sys,time,socket,subprocess,signal
from urllib.parse import urlparse
from urllib.request import urlopen
from settings import CONFIG,ROOT
MODULES={'dashboard':'dashboard_api','predictive':'predictive_api','jev':'jev_api'}
def main():
    selected=sys.argv[1:] or list(MODULES)
    if any(s not in MODULES for s in selected):raise SystemExit('Usage: ./run.sh [dashboard|predictive|jev]')
    parsed={name:urlparse(CONFIG[name]) for name in selected}
    if any(u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or not u.port or u.path not in ('','/') for u in parsed.values()):
        raise SystemExit('Configure local http://127.0.0.1:PORT service URLs in service_urls.json')
    if len({u.port for u in parsed.values()})!=len(parsed):raise SystemExit('Each service needs a different port')
    for u in parsed.values():
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            try:s.bind(('127.0.0.1',u.port))
            except OSError:raise SystemExit(f'Port {u.port} is already in use. Stop the existing service first.')
    children=[]
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        for name,u in parsed.items():
            env=os.environ.copy()
            if name!='jev':env.pop('TYPESAFE_API_KEY',None)
            children.append(subprocess.Popen([sys.executable,'-m','uvicorn',MODULES[name]+':app','--host','127.0.0.1','--port',str(u.port)],cwd=ROOT,env=env))
        pending=set(selected);deadline=time.monotonic()+30
        while pending:
            if any(p.poll() is not None for p in children):raise RuntimeError('A service exited during startup')
            for name in list(pending):
                try:
                    with urlopen(CONFIG[name]+'/health',timeout=.5) as response:
                        if response.status==200:pending.remove(name);print(name+' ready: '+CONFIG[name],flush=True)
                except OSError:pass
            if time.monotonic()>deadline:raise RuntimeError('Service startup timed out')
            time.sleep(.1)
        while True:
            if any(p.poll() is not None for p in children):raise RuntimeError('A service exited; stopping the remaining services')
            time.sleep(.5)
    except KeyboardInterrupt:pass
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.wait()
if __name__=='__main__':main()
