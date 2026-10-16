"""Provision only an isolated, unbilled staging project; never touch production."""
import json
import os
import time
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

PROJECT = 'obra-company-staging-4ecc7'
result = {'project_id': PROJECT, 'status': 'blocked', 'billing_linked': False, 'production_changed': False}
out = Path('company-pilot-results')
out.mkdir(exist_ok=True)

def save():
    (out / 'staging-provision.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)

raw = os.environ.get('FIREBASE_SA', '')
if not raw:
    result['blocker'] = 'Firebase service-account connection is unavailable.'
    save()
    raise SystemExit(0)
session = AuthorizedSession(service_account.Credentials.from_service_account_info(
    json.loads(raw), scopes=['https://www.googleapis.com/auth/cloud-platform']))
base = 'https://cloudresourcemanager.googleapis.com/v1/'
response = session.get(base + 'projects/' + PROJECT, timeout=30)
if response.status_code in (403, 404):
    response = session.post(base + 'projects', json={'projectId':PROJECT, 'name':'Obra company staging'}, timeout=30)
    result['project_create_http'] = response.status_code
    if response.ok:
        operation = response.json()
        for _ in range(30):
            if operation.get('done'):
                break
            time.sleep(2)
            poll = session.get(base + operation['name'], timeout=30)
            if not poll.ok:
                result['blocker'] = 'Cannot verify project creation operation.'
                save()
                raise SystemExit(0)
            operation = poll.json()
        if operation.get('error') or not operation.get('done'):
            result['blocker'] = 'Project creation failed or remains pending.'
            result['operation_error_code'] = operation.get('error', {}).get('code')
            save()
            raise SystemExit(0)
    else:
        result['blocker'] = 'Connected service account cannot create or access the isolated staging project.'
        result['api_status'] = response.json().get('error', {}).get('status', 'unknown')
        save()
        raise SystemExit(0)
elif not response.ok:
    result['blocker'] = 'Cannot inspect the isolated staging project.'
    result['project_get_http'] = response.status_code
    save()
    raise SystemExit(0)

response = session.get('https://firebase.googleapis.com/v1beta1/projects/' + PROJECT, timeout=30)
if response.status_code == 404:
    response = session.post('https://firebase.googleapis.com/v1beta1/projects/' + PROJECT + ':addFirebase', json={}, timeout=30)
    result['firebase_add_http'] = response.status_code
if response.ok:
    result['status'] = 'project-available-configure-services-next'
else:
    result['blocker'] = 'Cannot enable or inspect Firebase in the isolated staging project.'
    result['firebase_http'] = response.status_code
# No billing account is selected or attached by this script.
save()
