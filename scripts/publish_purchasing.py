import gzip,hashlib,json,os,time
from pathlib import Path
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

PROJECT='obra-manager-4ecc7'
SITE='sites/'+PROJECT
API='https://firebasehosting.googleapis.com/v1beta1/'
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']==PROJECT
session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
manifest=json.loads(Path('scripts/publication_manifest.json').read_text())
files={name:Path('public/'+name).read_bytes() for name in manifest['files']}
url='https://'+PROJECT+'.web.app/'
def call(method,path,**kwargs):
 r=session.request(method,API+path,timeout=60,**kwargs)
 if not r.ok:raise RuntimeError(str(r.status_code)+' '+r.json().get('error',{}).get('message',''))
 return r.json() if r.content else {}
def verify(base):
 for name,data in files.items():
  r=requests.get(base.rstrip('/')+'/'+name,params={'verify':os.environ.get('GITHUB_RUN_ID','')+'-'+str(time.time_ns())},headers={'Cache-Control':'no-cache'},timeout=30)
  if not r.ok or r.content!=data:
   print('VERIFY_PENDING',json.dumps({'file':name,'status':r.status_code,'expectedHash':hashlib.sha256(data).hexdigest(),'servedHash':hashlib.sha256(r.content).hexdigest()}),flush=True)
   return False
 return True
live=call('GET',SITE+'/channels/live')
source=live['release']['version']['name']
for name,expected in manifest['baseline'].items():
 r=requests.get(url+name,params={'baseline':str(time.time_ns())},headers={'Cache-Control':'no-cache'},timeout=30)
 if not r.ok or hashlib.sha256(r.content).hexdigest()!=expected:raise RuntimeError('Live '+name+' changed; stopped to preserve newer edits')
op=call('POST',SITE+'/versions:clone',json={'sourceVersion':source,'finalize':False})
for _ in range(60):
 if op.get('done'):break
 time.sleep(2);op=call('GET',op['name'])
if op.get('error') or not op.get('done'):raise RuntimeError('Hosting clone failed')
version=op['response']['name']
compressed={name:gzip.compress(data,mtime=0) for name,data in files.items()}
hashes={name:hashlib.sha256(data).hexdigest() for name,data in compressed.items()}
result=call('POST',version+':populateFiles',json={'files':{'/'+name:sha for name,sha in hashes.items()}})
for name,sha in hashes.items():
 if sha in result.get('uploadRequiredHashes',[]):
  r=session.post(result['uploadUrl']+'/'+sha,data=compressed[name],headers={'Content-Type':'application/octet-stream'},timeout=60)
  if not r.ok:raise RuntimeError('Hosting upload failed: '+name)
call('PATCH',version,params={'updateMask':'status'},json={'status':'FINALIZED'})
channel='purchasing-20261009'
r=session.get(API+SITE+'/channels/'+channel,timeout=30)
if r.status_code==404:preview=call('POST',SITE+'/channels',params={'channelId':channel},json={'ttl':'604800s'})
elif r.ok:preview=r.json()
else:raise RuntimeError('Preview channel unavailable')
call('POST',SITE+'/channels/'+channel+'/releases',params={'versionName':version},json={'message':manifest['message']})
for _ in range(24):
 if verify(preview['url']):break
 time.sleep(5)
else:raise RuntimeError('Preview did not serve the verified files')
if call('GET',SITE+'/channels/live')['release']['name']!=live['release']['name']:raise RuntimeError('Live release changed during verification')
call('POST',SITE+'/releases',params={'versionName':version},json={'message':manifest['message']})
for _ in range(24):
 if verify(url):break
 time.sleep(5)
else:
 call('POST',SITE+'/releases',params={'versionName':source},json={'message':'Restore previous version after verification failure'})
 raise RuntimeError('Live verification failed; previous version restored')
report={'live':url,'version':version,'previousVersion':source,'files':list(files),'verified':True}
Path('hosting-test').mkdir(exist_ok=True)
Path('hosting-test/publication.json').write_text(json.dumps(report,indent=2))
print('PUBLICATION_VERIFIED',json.dumps(report),flush=True)
