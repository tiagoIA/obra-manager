"""Preserve all existing hosting files/config and seed only absent template IDs."""
import os,json,gzip,hashlib,pathlib,time,requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
s=AuthorizedSession(creds);root='https://firebasehosting.googleapis.com/v1beta1/';site='sites/obra-manager-4ecc7'
def call(method,path,**kw):
 r=s.request(method,root+path,timeout=60,**kw);r.raise_for_status();return r.json() if r.content else {}
previous=call('GET',site+'/releases',params={'pageSize':1})['releases'][0]['version']
oldname=previous['name'];oldversion=call('GET',oldname)
live=requests.get('https://obra-manager-4ecc7.web.app/index.html',timeout=30);live.raise_for_status()
assert hashlib.sha256(live.content).hexdigest()=='82e4c25d4cab868766165006ac8e11655822a1d9064d47c0eed6e90555eb12a6','Live app changed; aborting instead of overwriting'
files={};token=None
while True:
 params={'pageSize':1000}
 if token:params['pageToken']=token
 data=call('GET',oldname+'/files',params=params)
 for f in data.get('files',[]):files[f['path']]=f['hash']
 token=data.get('nextPageToken')
 if not token:break
assert '/index.html' in files and '/manifest.json' in files
bucket=storage.Client(project=key['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
folder='backups/guided-lists/'+os.environ['GITHUB_RUN_ID']+'/'
bucket.blob(folder+'hosting.json').upload_from_string(json.dumps({'version':oldversion,'files':files}),content_type='application/json',if_generation_match=0)
bucket.blob(folder+'index.html').upload_from_string(live.content,content_type='text/html',if_generation_match=0)
fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
docs=[];token=None
while True:
 params={'pageSize':1000}
 if token:params['pageToken']=token
 r=s.get(fire+'/shoppingLists',params=params,timeout=60);r.raise_for_status();data=r.json();docs+=data.get('documents',[])
 token=data.get('nextPageToken')
 if not token:break
bucket.blob(folder+'shoppingLists.json').upload_from_string(json.dumps(docs),content_type='application/json',if_generation_match=0)
def encode(v):
 if v is None:return {'nullValue':None}
 if isinstance(v,bool):return {'booleanValue':v}
 if isinstance(v,int):return {'integerValue':str(v)}
 if isinstance(v,float):return {'doubleValue':v}
 if isinstance(v,str):return {'stringValue':v}
 if isinstance(v,list):return {'arrayValue':{'values':[encode(x) for x in v]}}
 return {'mapValue':{'fields':{k:encode(x) for k,x in v.items()}}}
existing={d['name'].split('/')[-1] for d in docs};writes=[]
for p in json.loads(pathlib.Path('guided-presets-v1.json').read_text()):
 if p['id'] in existing:continue
 ident=p['id'];p={**p,'listType':'template','ownerUid':None,'projectId':None,'done':False,'isBuiltIn':True}
 fields={k:encode(v) for k,v in p.items() if k!='id'}
 writes.append({'update':{'name':'projects/obra-manager-4ecc7/databases/(default)/documents/shoppingLists/'+ident,'fields':fields},'currentDocument':{'exists':False},'updateTransforms':[{'fieldPath':'createdAt','setToServerValue':'REQUEST_TIME'}]})
uploaded={}
for path in ['/index.html','/guided-shopping-v1.js','/sw.js']:
 raw=pathlib.Path('public'+path).read_bytes();blob=gzip.compress(raw,mtime=0);h=hashlib.sha256(blob).hexdigest();files[path]=h;uploaded[h]=blob
new=call('POST',site+'/versions',json={'config':oldversion.get('config',{})})['name']
pop=call('POST',new+':populateFiles',json={'files':files})
for h in pop.get('uploadRequiredHashes',[]):
 assert h in uploaded,'Unexpected old asset requires upload; preserving current site'
 r=s.post(pop['uploadUrl']+'/'+h,data=uploaded[h],headers={'Content-Type':'application/octet-stream'},timeout=60);r.raise_for_status()
call('PATCH',new,params={'update_mask':'status'},json={'status':'FINALIZED'})
# All files staged before creating the built-ins or publishing.
if writes:
 r=s.post(fire+':commit',json={'writes':writes},timeout=60);r.raise_for_status()
print('PRESETS_CREATED',len(writes))
release=call('POST',site+'/releases',params={'versionName':new},json={'message':'Guided and custom shopping v1'})
try:
 for path in ['/index.html','/guided-shopping-v1.js','/sw.js']:
  for attempt in range(6):
   r=requests.get('https://obra-manager-4ecc7.web.app'+path,params={'verify':os.environ['GITHUB_RUN_ID']},timeout=30)
   if r.ok and r.content.rstrip()==pathlib.Path('public'+path).read_bytes().rstrip():break
   time.sleep(3)
  else:raise RuntimeError('Published file verification failed: '+path)
 print('DEPLOY_VERIFIED',new,'files preserved',len(files),'backup',folder)
except Exception:
 call('POST',site+'/releases',params={'versionName':oldname},json={'message':'Automatic rollback after verification failure'})
 print('ROLLED_BACK',oldname);raise
