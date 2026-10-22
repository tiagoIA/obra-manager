"""Append only the reviewed guide collection rule to the audited current rules."""
import json,os
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
project='obra-manager-4ecc7';key=json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id')!=project:raise SystemExit('Unexpected project')
s=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
base='https://firebaserules.googleapis.com/v1/'
def call(method,path,**kwargs):
 r=s.request(method,base+path,timeout=60,**kwargs)
 if not r.ok:raise SystemExit('Rules operation HTTP '+str(r.status_code))
 return r.json()
release=call('GET','projects/'+project+'/releases/cloud.firestore')
source=call('GET',release['rulesetName'])['source']
files=source['files'];old=Path('reference-audit/firestore.rules').read_text();new=Path('hosting-test/reference-firestore.rules').read_text()
if len(files)!=1 or files[0]['content']!=old:raise SystemExit('Rules changed since audit; stop')
if old==new: print('Reference rules already installed');raise SystemExit(0)
# The only diff is insertion of the reviewed fragment; existing permissions untouched.
fragment=Path('scripts/installation-reference.rules').read_text()
if new.replace(fragment,'',1)!=old:raise SystemExit('Unexpected rules changes')
created=call('POST','projects/'+project+'/rulesets',json={'source':{'files':[{'name':files[0]['name'],'content':new}]}})
current=call('GET',release['name'])
if current['rulesetName']!=release['rulesetName']:raise SystemExit('Concurrent rules change; stop')
updated=call('PATCH',release['name'],json={'release':{'name':release['name'],'rulesetName':created['name']},'updateMask':'rulesetName'})
verified=call('GET',release['name'])
if verified['rulesetName']!=created['name']:raise SystemExit('Rules read-back mismatch')
Path('hosting-test/reference-rules-result.json').write_text(json.dumps({'previous':release['rulesetName'],'current':verified['rulesetName']},indent=2))
print('REFERENCE_RULES_VERIFIED',verified['rulesetName'])
