"""Publish only the catalog validator and cache version; never write Firestore."""
import os,json,gzip,hashlib,pathlib,requests,time
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
s=AuthorizedSession(creds);root='https://firebasehosting.googleapis.com/v1beta1/';site='sites/obra-manager-4ecc7'
def call(method,path,**kw):
 r=s.request(method,root+path,timeout=60,**kw);r.raise_for_status();return r.json() if r.content else {}
old=call('GET',site+'/releases',params={'pageSize':1})['releases'][0]['version']['name']
config=call('GET',old).get('config',{});files={};token=None
while True:
 params={'pageSize':1000}
 if token:params['pageToken']=token
 data=call('GET',old+'/files',params=params)
 for f in data.get('files',[]):files[f['path']]=f['hash']
 token=data.get('nextPageToken')
 if not token:break
assert len(files)>=74 and '/index.html' in files
live=requests.get('https://obra-manager-4ecc7.web.app/index.html',timeout=40);live.raise_for_status()
assert live.content.rstrip()==pathlib.Path('public/index.html').read_bytes().rstrip(),'Live index changed; review before publishing'
bucket=storage.Client(project=key['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app');folder='backups/catalog-guards/'+os.environ['GITHUB_RUN_ID']+'/'
bucket.blob(folder+'hosting.json').upload_from_string(json.dumps({'version':old,'config':config,'files':files}),content_type='application/json',if_generation_match=0)
uploaded={};expected={}
for path in ['/central-catalog-v1.js','/sw.js']:
 r=requests.get('https://obra-manager-4ecc7.web.app'+path,timeout=40);r.raise_for_status();bucket.blob(folder+path[1:]).upload_from_string(r.content,content_type='application/javascript',if_generation_match=0)
 raw=pathlib.Path('public'+path).read_bytes();expected[path]=raw;data=gzip.compress(raw,mtime=0);h=hashlib.sha256(data).hexdigest();files[path]=h;uploaded[h]=data
new=call('POST',site+'/versions',json={'config':config})['name'];pop=call('POST',new+':populateFiles',json={'files':files})
for h in pop.get('uploadRequiredHashes',[]):
 assert h in uploaded,'An unrelated asset would change'
 r=s.post(pop['uploadUrl']+'/'+h,data=uploaded[h],headers={'Content-Type':'application/octet-stream'},timeout=60);r.raise_for_status()
call('PATCH',new,params={'update_mask':'status'},json={'status':'FINALIZED'})
assert call('GET',site+'/releases',params={'pageSize':1})['releases'][0]['version']['name']==old,'Another release happened; abort'
call('POST',site+'/releases',params={'versionName':new})
assert call('GET',site+'/releases',params={'pageSize':1})['releases'][0]['version']['name']==new
for path,raw in expected.items():
 for attempt in range(6):
  r=requests.get('https://obra-manager-4ecc7.web.app'+path,params={'catalogRevision':os.environ['GITHUB_RUN_ID']},headers={'Cache-Control':'no-cache'},timeout=40);r.raise_for_status()
  if r.content==raw:break
  if attempt==5:raise AssertionError('Public asset differs after release propagation')
  time.sleep(3)
print('CATALOG_GUARDS_PUBLISHED',json.dumps({'version':new,'preservedFiles':len(files),'backup':folder,'firestoreWrites':0}))
