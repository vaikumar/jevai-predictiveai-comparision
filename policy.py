from pathlib import Path
ROOT = Path(__file__).parent
LABELS = ['allow', 'Challenge', 'Block']
FEATURES = ['failure_ind', 'device_bounded', 'device_linked', 'credential_remed_manda']
CRITERIA = {'allow':'Permit under the demonstration policy only; not an authentication success.', 'Challenge':'Require additional verification.', 'Block':'Deny under the demonstration policy.'}
POLICY = ('DEMONSTRATION ONLY, not a validated fraud policy. Apply in this order: '
          'Block if failure_ind AND credential_remed_manda are true. '
          'Otherwise Challenge if failure_ind OR credential_remed_manda is true, OR device_bounded OR device_linked is false. '
          'Otherwise allow. Ignore all other fields. remember_my_device is a user preference, not proof of trust. '
          'allow never overrides failed authentication. Output exactly allow, Challenge, or Block.')

def features(record):
    if hasattr(record,'model_dump'): record=record.model_dump()
    return [int(record[k]) for k in FEATURES]

def label(record):
    if record['failure_ind'] and record['credential_remed_manda']: return 2
    if record['failure_ind'] or record['credential_remed_manda'] or not record['device_bounded'] or not record['device_linked']: return 1
    return 0

