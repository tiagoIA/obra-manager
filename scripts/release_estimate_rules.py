"""Deploy only the exact emulator-tested rule sources; retain rollback refs."""
import json,os,hashlib
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

def release_rules():
 key=json.loads(os.environ['FIREBASE_SA']);assert key.get('project_id')=='obra-manager-4ecc7'
 session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
 base='https://firebaserules.googleapis.com/v1/';project='projects/obra-manager-4ecc7';manifest=json.loads(Path('hosting-test/estimate-rules-manifest.json').read_text());out={}
 def call(method,path,**kwargs):
  r=session.request(method,base+path,timeout=45,**kwargs)
  if not r.ok:raise RuntimeError('Rules API HTTP '+str(r.status_code))
  return r.json()
 # Check both baselines before changing either service.
 for kind,cfg in manifest.items():
  path=project+'/releases/'+cfg['release'];live=call('GET',path)
  if live['rulesetName']!=cfg['rulesetName']:raise RuntimeError('Live rules changed during tests; stop.')
  content=Path('hosting-test/'+kind+'.rules').read_text();assert hashlib.sha256(content.encode()).hexdigest()==cfg['after_sha256']
  new=call('POST',project+'/rulesets',json={'source':{'files':[{'name':cfg['name'],'content':content}]}})
  out[kind]={'release':path,'before':cfg['rulesetName'],'after':new['name']}
 Path('hosting-test/estimate-rules-release.json').write_text(json.dumps(out,indent=2))
 changed=[]
 try:
  for kind,r in out.items():
   current=call('GET',r['release'])
   if current['rulesetName']!=r['before']:raise RuntimeError('Rules release baseline changed.')
   call('PATCH',r['release'],json={'release':{'name':r['release'],'rulesetName':r['after']},'updateMask':'rulesetName'});changed.append(r)
   assert call('GET',r['release'])['rulesetName']==r['after']
   print('RULE_RELEASE_VERIFIED',kind)
 except Exception:
  for r in reversed(changed):
   if call('GET',r['release'])['rulesetName']==r['after']:
    call('PATCH',r['release'],json={'release':{'name':r['release'],'rulesetName':r['before']},'updateMask':'rulesetName'})
  raise
 return out
