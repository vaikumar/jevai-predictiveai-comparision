"""Non-secret service configuration; shared by launcher, gateway and UI."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
CONFIG=json.loads((ROOT/'service_urls.json').read_text())
PREDICTIVE_URL=CONFIG['predictive'].rstrip('/')
JEV_URL=CONFIG['jev'].rstrip('/')
DASHBOARD_URL=CONFIG['dashboard'].rstrip('/')
JEV_ENDPOINT='https://api.typesafe.ai/v1/systemone'
JEV_MODEL='jev-latest'
