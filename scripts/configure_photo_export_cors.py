import json, os
from pathlib import Path
from urllib.parse import urlparse
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
project='obra-manager-4ecc7'
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']==project
session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
data=json.loads(Path('tmp/photo-report/arlington-input.json').read_text())
buckets=set()
def collect(value):
 if isinstance(value,dict):
  for v in value.values(): collect(v)
 elif isinstance(value,list):
  for v in value: collect(v)
 elif isinstance(value,str) and value.startswith('https://firebasestorage.googleapis.com/'):
  parts=urlparse(value).path.split('/')
  if len(parts)>3 and parts[1:3]==['v0','b']: buckets.add(parts[3])
collect(data)
assert buckets and buckets<= {project+'.appspot.com',project+'.firebasestorage.app'}
origins=['https://'+project+'.web.app','https://'+project+'.firebaseapp.com']
for bucket in sorted(buckets):
 url='https://storage.googleapis.com/storage/v1/b/'+bucket
 response=session.get(url,timeout=30)
 if not response.ok: raise SystemExit('Unable to read bucket configuration: HTTP '+str(response.status_code))
 current=response.json().get('cors',[])
 missing=[origin for origin in origins if not any(origin in rule.get('origin',[]) and 'GET' in rule.get('method',[]) for rule in current)]
 if missing:
  response=session.patch(url,json={'cors':current+[{'origin':missing,'method':['GET'],'responseHeader':['Content-Type','Cache-Control','Content-Length'],'maxAgeSeconds':3600}]},timeout=30)
  if not response.ok: raise SystemExit('Unable to update image CORS: HTTP '+str(response.status_code))
 print('IMAGE_CORS_READY',json.dumps({'applicationOrigins':origins,'existingRulesPreserved':True}))
