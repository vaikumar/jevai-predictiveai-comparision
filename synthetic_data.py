import numpy as np
from schema import LoginRequest
from policy import label

def generate(n, seed):
    rng=np.random.default_rng(seed); records=[]
    for i in range(n):
        r=LoginRequest(failure_ind=bool(rng.random()<.3),device_bounded=bool(rng.random()<.8),device_linked=bool(rng.random()<.8),credential_remed_manda=bool(rng.random()<.25),remember_my_device=bool(rng.random()<.7)).model_dump()
        r.update(session_key=f'synthetic_{seed}_{i}',trans_key=f'ses_synthetic_{seed}_{i}',online_device_id=f'demo_device_{seed}_{i}',ip_address=f'192.0.2.{1+i%254}',gps='',originator_name=str(rng.choice(['iphone','android'])),app_version=str(rng.choice(['1.0','1.1','2.0'])))
        records.append(r)
    return records,np.array([label(r) for r in records])

