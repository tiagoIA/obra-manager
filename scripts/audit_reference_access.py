"""Read-only access check: no task, material, rule or Hosting writes."""
import hashlib,json,os,urllib.request
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
project='obra-manager-4ecc7'
key=json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id') != project: raise SystemExit('Unexpected Firebase project')
session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
out=Path('reference-audit');out.mkdir(exist_ok=True)
def read(url):
 r=session.get(url,timeout=45)
 if not r.ok: raise SystemExit('Read-only Firebase audit returned HTTP '+str(r.status_code))
 return r.json()
hosting=read('https://firebasehosting.googleapis.com/v1beta1/sites/'+project+'/channels/live')
base='https://firebaserules.googleapis.com/v1/'
release=read(base+'projects/'+project+'/releases/cloud.firestore')
rules=read(base+release['rulesetName'])
for f in rules['source']['files']:
 if f['name'].endswith('.rules'): (out/'firestore.rules').write_text(f['content'])
# Verify service access with a one-document query; never export customer content.
firestore=read('https://firestore.googleapis.com/v1/projects/'+project+'/databases/(default)/documents/materials?pageSize=1')
data=urllib.request.urlopen('https://'+project+'.web.app/app.html',timeout=30).read()
result={'hostingReadable':True,'rulesReadable':True,'firestoreReadable':True,'liveVersion':hosting['release']['version']['name'],'appSha256':hashlib.sha256(data).hexdigest(),'rulesetName':release['rulesetName']}
(out/'access.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
