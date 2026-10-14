"""Allow the existing app to process its evidence images; preserve access controls."""
import json, os
from pathlib import Path
from urllib.parse import urlparse, unquote, quote
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

key = json.loads(os.environ['FIREBASE_SA'])
assert key['project_id'] == 'obra-manager-4ecc7'
origin = 'https://obra-manager-4ecc7.web.app'
data = json.loads(Path('tmp/photo-report/arlington-input.json').read_text())
buckets = set()
def visit(value):
    if isinstance(value, dict):
        for child in value.values(): visit(child)
    elif isinstance(value, list):
        for child in value: visit(child)
    elif isinstance(value, str):
        parsed = urlparse(value)
        if parsed.hostname == 'firebasestorage.googleapis.com' and parsed.path.startswith('/v0/b/'):
            buckets.add(unquote(parsed.path.split('/')[3]))
visit(data)
assert buckets and buckets <= {'obra-manager-4ecc7.appspot.com', 'obra-manager-4ecc7.firebasestorage.app'}
session = AuthorizedSession(service_account.Credentials.from_service_account_info(key, scopes=['https://www.googleapis.com/auth/devstorage.full_control']))
for bucket in sorted(buckets):
    endpoint = 'https://storage.googleapis.com/storage/v1/b/' + quote(bucket, safe='')
    response = session.get(endpoint, timeout=30)
    response.raise_for_status()
    metadata = response.json()
    cors = metadata.get('cors', [])
    if any(origin in row.get('origin', []) and 'GET' in row.get('method', []) for row in cors):
        print('REPORT_IMAGE_CORS_ALREADY_CONFIGURED', bucket)
        continue
    Path('hosting-test').mkdir(exist_ok=True)
    Path('hosting-test/report-cors-before.json').write_text(json.dumps({'bucket': bucket, 'cors': cors}, indent=2))
    cors.append({'origin': [origin], 'method': ['GET'], 'responseHeader': ['Content-Type'], 'maxAgeSeconds': 3600})
    result = session.patch(endpoint, params={'ifMetagenerationMatch': metadata['metageneration']}, json={'cors': cors}, timeout=30)
    result.raise_for_status()
    updated = result.json()
    assert updated.get('iamConfiguration') == metadata.get('iamConfiguration')
    print('REPORT_IMAGE_CORS_CONFIGURED', json.dumps({'bucket': bucket, 'origin': origin, 'method': 'GET'}))
