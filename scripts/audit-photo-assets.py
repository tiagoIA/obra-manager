"""Read-only photo coverage and asset audit. Never print download URLs or tokens."""
import os,json,io,base64,requests,concurrent.futures
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from importlib.machinery import SourceFileLoader
catalog=SourceFileLoader('catalog','scripts/import-central.py').load_module()
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
s=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
url='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents/materials'
docs=[];token=None
while True:
 p={'pageSize':1000}
 if token:p['pageToken']=token
 r=s.get(url,params=p,timeout=60);r.raise_for_status();d=r.json();docs+=d.get('documents',[]);token=d.get('nextPageToken')
 if not token:break
rows=[{'id':d['name'].split('/')[-1],**{k:catalog.decode(v) for k,v in d.get('fields',{}).items()}} for d in docs]
active=[r for r in rows if r.get('active') is not False and r.get('status')!='inactive' and not r.get('isTask')]
for r in active:
 if not r.get('photoUrl'):print('PHOTO_PENDING',json.dumps({k:r.get(k) for k in ['id','sku','name','brand','manufacturerPart','model']},ensure_ascii=False))
def check(p):
 result={k:p.get(k) for k in ['id','sku','name']}
 try:
  u=p['photoUrl']
  if u.startswith('data:image/'):raw=base64.b64decode(u.split(',',1)[1])
  else:
   assert u.startswith('https://')
   q=requests.get(u,timeout=30);q.raise_for_status();raw=q.content
  assert len(raw)<20000000
  im=Image.open(io.BytesIO(raw));im.load();assert min(im.size)>=40
  result['ok']=True
 except Exception as e:result.update(ok=False,error=type(e).__name__)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(check,[r for r in active if r.get('photoUrl')]))
for r in results:
 if not r['ok']:print('PHOTO_ASSET_FAILURE',json.dumps(r,ensure_ascii=False))
print('PHOTO_AUDIT_SUMMARY',json.dumps({'catalogCount':len(rows),'activeMaterials':len(active),'missing':sum(not r.get('photoUrl') for r in active),'validPhotos':sum(r['ok'] for r in results),'failedPhotos':sum(not r['ok'] for r in results)}))
