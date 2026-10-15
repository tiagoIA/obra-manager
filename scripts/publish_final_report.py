import gzip, hashlib, json, os, time
from pathlib import Path
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
PROJECT = 'obra-manager-4ecc7'
SITE = 'sites/' + PROJECT
API = 'https://firebasehosting.googleapis.com/v1beta1/'
config = json.loads(Path('scripts/final-report-publication.json').read_text())
key = json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id') != PROJECT:
    raise SystemExit('Unexpected Firebase project')
session = AuthorizedSession(service_account.Credentials.from_service_account_info(key, scopes=['https://www.googleapis.com/auth/cloud-platform']))
def call(method, path, **kwargs):
    response = session.request(method, API+path, timeout=60, **kwargs)
    if not response.ok:
        raise SystemExit(f'{method} {path}: HTTP {response.status_code}')
    return response.json() if response.content else {}
def verify(url):
    for filename in config['files']:
        r = requests.get(url.rstrip('/')+'/'+filename, params={'version':os.environ.get('GITHUB_SHA','verify'),'verification':str(time.time_ns())}, timeout=30)
        if not r.ok or r.content != Path('public',filename).read_bytes():
            return False
    return True
for filename,digest in config['files'].items():
    if hashlib.sha256(Path('public',filename).read_bytes()).hexdigest()!=digest:
        raise SystemExit('Reviewed source file mismatch')
live = call('GET', SITE+'/channels/live')
source = live['release']['version']['name']
response = requests.get('https://'+PROJECT+'.web.app/app.html', timeout=30)
if not response.ok or hashlib.sha256(response.content).hexdigest() != config['baseline_sha256']:
    if response.ok and response.content == Path('public/app.html').read_bytes() and verify('https://'+PROJECT+'.web.app/'):
        Path('hosting-test').mkdir(exist_ok=True)
        result={'live_url':'https://'+PROJECT+'.web.app/','workspace_url':'https://'+PROJECT+'.web.app/app.html','version':source,'verified_files':config['files'],'already_published':True}
        Path('hosting-test/final-report-result.json').write_text(json.dumps(result,indent=2))
        print('PUBLICATION_VERIFIED',json.dumps(result))
        raise SystemExit(0)
    raise SystemExit('Live HTML changed; stop to preserve newer work')
for filename,digest in config.get('baseline_files',{}).items():
    previous=requests.get('https://'+PROJECT+'.web.app/'+filename,params={'verification':str(time.time_ns())},timeout=30)
    if not previous.ok or hashlib.sha256(previous.content).hexdigest()!=digest:
        raise SystemExit('Live report module changed; stop to preserve newer work')
Path('hosting-test').mkdir(exist_ok=True)
Path('hosting-test/live-before.json').write_text(json.dumps(live,indent=2))
op=call('POST',SITE+'/versions:clone',json={'sourceVersion':source,'finalize':False})
for _ in range(60):
    if op.get('done'): break
    time.sleep(2)
    op=call('GET',op['name'])
else: raise SystemExit('Clone timed out')
if op.get('error'): raise SystemExit('Clone failed')
version=op['response']['name']
if not version.startswith(SITE+'/versions/'): raise SystemExit('Unexpected version')
blobs={}
for filename in config['files']:
    data=gzip.compress(Path('public',filename).read_bytes(),mtime=0)
    blobs[filename]=(hashlib.sha256(data).hexdigest(),data)
files=call('POST',version+':populateFiles',json={'files':{'/'+f:v[0] for f,v in blobs.items()}})
for digest,data in blobs.values():
    if digest not in files.get('uploadRequiredHashes',[]): continue
    r=session.post(files['uploadUrl']+'/'+digest,data=data,headers={'Content-Type':'application/octet-stream'},timeout=60)
    if not r.ok: raise SystemExit('Upload failed')
call('PATCH',version,params={'updateMask':'status'},json={'status':'FINALIZED'})
channel_id='final-report-20261015'
r=session.get(API+SITE+'/channels/'+channel_id,timeout=30)
if r.status_code==404: channel=call('POST',SITE+'/channels',params={'channelId':channel_id},json={'ttl':'604800s'})
elif r.ok: channel=r.json()
else: raise SystemExit('Preview channel unavailable')
call('POST',SITE+'/channels/'+channel_id+'/releases',params={'versionName':version},json={'message':'Verify photo report cover and project facade'})
preview=channel['url']
print('PREVIEW_READY',preview,flush=True)
for _ in range(24):
    if verify(preview): break
    time.sleep(5)
else: raise SystemExit('Preview content verification failed')
if config.get('review_only'):
    result={'preview_url':preview,'previous_live_version':source,'preview_version':version,'verified_files':config['files'],'review_only':True}
    Path('hosting-test/final-report-result.json').write_text(json.dumps(result,indent=2))
    print('REVIEW_READY',json.dumps(result))
    raise SystemExit(0)
after=call('GET',SITE+'/channels/live')
if after['release']['name']!=live['release']['name']: raise SystemExit('Live release changed during verification')
release=call('POST',SITE+'/releases',params={'versionName':version},json={'message':'Improve Photos 2.0 unit order, compact index and adaptive photo layout'})
url='https://'+PROJECT+'.web.app/'
for _ in range(24):
    if verify(url): break
    time.sleep(5)
else:
    call('POST',SITE+'/releases',params={'versionName':source},json={'message':'Restore previous release after shopping verification failure'})
    raise SystemExit('Live verification failed; previous release restored')
result={'live_url':url,'workspace_url':url+'app.html','preview_url':preview,'previous_live_version':source,'version':version,'release':release['name'],'verified_files':config['files']}
Path('hosting-test/final-report-result.json').write_text(json.dumps(result,indent=2))
print('PUBLICATION_VERIFIED',json.dumps(result))




