"""Preserve all existing hosting files/config and seed only absent template IDs."""
import os,json,gzip,hashlib,pathlib,time,requests,runpy,concurrent.futures
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
s=AuthorizedSession(creds);root='https://firebasehosting.googleapis.com/v1beta1/';site='sites/obra-manager-4ecc7'
def call(method,path,**kw):
 r=s.request(method,root+path,timeout=60,**kw)
 if not r.ok:raise RuntimeError('Hosting API '+str(r.status_code)+': '+r.text[:1200])
 return r.json() if r.content else {}
previous=call('GET',site+'/releases',params={'pageSize':1})['releases'][0]['version']
oldname=previous['name'];oldversion=call('GET',oldname)
live=requests.get('https://obra-manager-4ecc7.web.app/index.html',timeout=30);live.raise_for_status()
assert hashlib.sha256(live.content.rstrip()).hexdigest()==pathlib.Path('live-index.sha256').read_text().strip(),'Live app changed; aborting instead of overwriting'
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
folder='backups/central-catalog/'+os.environ['GITHUB_RUN_ID']+'/'
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
material_docs=[];token=None
while True:
 params={'pageSize':1000}
 if token:params['pageToken']=token
 r=s.get(fire+'/materials',params=params,timeout=60);r.raise_for_status();data=r.json();material_docs+=data.get('documents',[])
 token=data.get('nextPageToken')
 if not token:break
bucket.blob(folder+'materials.json').upload_from_string(json.dumps(material_docs),content_type='application/json',if_generation_match=0)
for collection in ['shoppingItems','tasks','productDB','invoices']:
 saved=[];token=None
 while True:
  params={'pageSize':1000}
  if token:params['pageToken']=token
  r=s.get(fire+'/'+collection,params=params,timeout=60);r.raise_for_status();data=r.json();saved+=data.get('documents',[]);token=data.get('nextPageToken')
  if not token:break
 bucket.blob(folder+collection+'.json').upload_from_string(json.dumps(saved),content_type='application/json',if_generation_match=0)
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
catalog=runpy.run_path('scripts/import-central.py')
catalog_writes,originals=catalog['prepare'](s,fire,bucket,folder,material_docs,encode)
writes=catalog_writes+writes
uploaded={}
asset_paths=['/index.html','/guided-shopping-v1.js','/central-catalog-v1.js','/sw.js']
for path in asset_paths:
 raw=pathlib.Path('public'+path).read_bytes();blob=gzip.compress(raw,mtime=0);h=hashlib.sha256(blob).hexdigest();files[path]=h;uploaded[h]=blob
new=call('POST',site+'/versions',json={'config':oldversion.get('config',{})})['name']
pop=call('POST',new+':populateFiles',json={'files':files})
for h in pop.get('uploadRequiredHashes',[]):
 assert h in uploaded,'Unexpected old asset requires upload; preserving current site'
 r=s.post(pop['uploadUrl']+'/'+h,data=uploaded[h],headers={'Content-Type':'application/octet-stream'},timeout=60);r.raise_for_status()
call('PATCH',new,params={'update_mask':'status'},json={'status':'FINALIZED'})
# All files staged before creating the built-ins or publishing.
committed=None;published=False
try:
 if writes:
  r=s.post(fire+':commit',json={'writes':writes},timeout=60);r.raise_for_status();committed=r.json()
 print('PRESETS_CREATED',len(writes)-len(catalog_writes))
 # Existing stock, IDs, purchase links and unrelated fields must be unchanged.
 current={};token=None
 while True:
  params={'pageSize':1000}
  if token:params['pageToken']=token
  r=s.get(fire+'/materials',params=params,timeout=60);r.raise_for_status();data=r.json();current.update({d['name']:d for d in data.get('documents',[])});token=data.get('nextPageToken')
  if not token:break
 masks={w['update']['name']:set(w.get('updateMask',{}).get('fieldPaths',[]))|{'updatedAt'} for w in catalog_writes}
 for name,original in originals.items():
  assert name in current,'Existing material removed'
  for key,value in original.get('fields',{}).items():
   if key not in masks.get(name,set()):assert current[name]['fields'].get(key)==value,'Unrelated field changed: '+key
 for collection in ['shoppingItems','tasks','productDB','invoices']:
  saved=json.loads(bucket.blob(folder+collection+'.json').download_as_text());now=[];token=None
  while True:
   params={'pageSize':1000}
   if token:params['pageToken']=token
   r=s.get(fire+'/'+collection,params=params,timeout=60);r.raise_for_status();data=r.json();now+=data.get('documents',[]);token=data.get('nextPageToken')
   if not token:break
  # No changes to these collections are performed by this migration.
  assert {d['name']:d.get('fields',{}) for d in saved}=={d['name']:d.get('fields',{}) for d in now},'Concurrent activity detected in '+collection
 # Recovery check against the original pre-import backup, not just this run's snapshot.
 baseline=json.loads(bucket.blob('backups/central-catalog/37848656302/materials.json').download_as_text())
 for d in baseline:
  assert d['name'] in current
  for key,value in d.get('fields',{}).items():
   if key not in {'suppliers','updatedAt'}:assert current[d['name']]['fields'].get(key)==value,'Pre-import field changed: '+key
 for collection in ['shoppingItems','tasks','productDB','invoices']:
  baseline_items=json.loads(bucket.blob('backups/central-catalog/37848656302/'+collection+'.json').download_as_text())
  this_run=json.loads(bucket.blob(folder+collection+'.json').download_as_text())
  assert {d['name']:d.get('fields',{}) for d in baseline_items}=={d['name']:d.get('fields',{}) for d in this_run},'Pre-import '+collection+' changed'
 print('PRE_IMPORT_RECORDS_PRESERVED',len(baseline),'CURRENT_CATALOG',len(current))
 print('EXISTING_RECORDS_PRESERVED',len(originals))
 receipt=json.loads(pathlib.Path('catalog-receipt.json').read_text())
 def verify_public_photo(row):
  name=fire.replace('https://firestore.googleapis.com/v1/','')+'/materials/'+row['id'];photo=current[name]['fields']['photoUrl']['stringValue']
  r=requests.get(photo,timeout=35);r.raise_for_status()
  from PIL import Image
  import io
  im=Image.open(io.BytesIO(r.content));im.load();assert min(im.size)>=80
  return True
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:assert all(pool.map(verify_public_photo,receipt['imported']))
 print('PUBLIC_CATALOG_PHOTOS_VERIFIED',len(receipt['imported']))
 release=call('POST',site+'/releases',params={'versionName':new},json={'message':'Central materials v4: verified catalog, supplier codes and purchasing PDF'});published=True
 for path in asset_paths:
  for attempt in range(6):
   r=requests.get('https://obra-manager-4ecc7.web.app'+path,params={'verify':os.environ['GITHUB_RUN_ID']},timeout=30)
   if r.ok and r.content.rstrip()==pathlib.Path('public'+path).read_bytes().rstrip():break
   time.sleep(3)
  else:raise RuntimeError('Published file verification failed: '+path)
 print('DEPLOY_VERIFIED',new,'files preserved',len(files),'backup',folder)
except Exception:
 try:
  if published:call('POST',site+'/releases',params={'versionName':oldname},json={'message':'Automatic rollback after verification failure'})
 finally:
  if committed:catalog['rollback'](s,fire,writes,committed,originals)
 print('ROLLED_BACK',oldname);raise
