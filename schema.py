from pydantic import BaseModel, ConfigDict, Field

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_max_length=2048)
    failure_ind: bool
    device_bounded: bool
    device_linked: bool
    credential_remed_manda: bool
    remember_my_device: bool
    session_key: str = ''
    trans_normalized_date: str = ''
    Channel: str = 'MOBL'
    system_cd: str = 'NATIVE_APP'
    source: str = 'LOGIN'
    trans_key: str = ''
    origination_system_cd: str = 'NATIVE_APP'
    trans_type: str = 'MOBL_LOGIN'
    source_app_id: str = 'XXX'
    password_status_cdoe: str = 'ENHANCED'
    pre_auth_permissive_failure_adv: str = ''
    originator_name: str = 'iphone'
    flow_initiating_app: str = 'loginapp'
    device_create_time: str = ''
    accept_encoding: str = 'gzip'
    via: str = 'akamai'
    online_device_id: str = ''
    first_seen: str = ''
    last_event: str = ''
    header_user_agent: str = ''
    ip_address: str = ''
    start_date_time: str = ''
    app_version: str = '1.0'
    device_type: str = 'MOBILE'
    browser_accet_lang: str = 'en-US'
    gps: str = ''
