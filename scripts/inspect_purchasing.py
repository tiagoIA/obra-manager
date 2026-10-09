import os,json
from google.oauth2 import service_account
from google.cloud import firestore
from google.auth.transport.requests import AuthorizedSession
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
db=firestore.Client(project=key['project_id'],credentials=creds)
fields=['name','sku','cat','unit','brand','model','manufacturerPart','upc','photoUrl','sourceUrl','suppliers','active','status','recordType','catalogReviewStatus','gceCode','description','specs','family']
for col in ['materials','suppliers','shoppingLists']:
 rows=[]
 for d in db.collection(col).stream():
  x=d.to_dict()
  if col=='materials' and x.get('isTask'):continue
  if col=='shoppingLists':
   if d.id not in ['guided-reference-fa-scope-20261009','guided-reference-fa-quote-20261009']:continue
   rows.append({'id':d.id,**x})
  elif col=='suppliers':rows.append({'id':d.id,**{k:x.get(k) for k in ['name','website','url','active']}})
  else:rows.append({'id':d.id,**{k:x.get(k) for k in fields if k in x}})
 print('AUDIT_'+col.upper(),json.dumps(rows,default=str),flush=True)
s=AuthorizedSession(creds)
r=s.get('https://firebaserules.googleapis.com/v1/projects/'+key['project_id']+'/releases/cloud.firestore',timeout=30)
if r.ok:
 name=r.json().get('rulesetName')
 r=s.get('https://firebaserules.googleapis.com/v1/'+name,timeout=30)
 if r.ok:print('RULES',json.dumps(r.json().get('source',{})),flush=True)
