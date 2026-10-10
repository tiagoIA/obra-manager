"""Read-only fixture and before/after fingerprint for the restored Roof store PDF."""
import hashlib,json,os,sys
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
PID='o3igcYUWRFxNTXRb9kbx'
LID='3MR0tydWGIHwMrLmYUq6'
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
listing=db.collection('shoppingLists').document(LID).get().to_dict()
assert listing and listing['projectId']==PID
items={d.id:d.to_dict() for d in db.collection('shoppingItems').where('listId','==',LID).stream()}
project=db.collection('projects').document(PID).get().to_dict()
assert project and project['name']=='COAX Main · Arlington'
fingerprint=hashlib.sha256(json.dumps({'list':listing,'items':items},sort_keys=True,default=str).encode()).hexdigest()
out=Path('hosting-test');out.mkdir(exist_ok=True)
proof=out/'roof-shopping-fingerprint.txt'
if '--after' in sys.argv:
 assert proof.read_text()==fingerprint,'Roof shopping records changed during publication; inspect concurrent edits'
 print('ROOF_SHOPPING_UNCHANGED',fingerprint,flush=True)
else:
 mids={i.get(k) for i in items.values() for k in ['matId','referenceMaterialId'] if i.get(k)}
 mats=[]
 for mid in sorted(mids):
  data=db.collection('materials').document(mid).get().to_dict()
  if data:mats.append({'id':mid,**data})
 fixture={'projectName':project['name'],'list':{'id':LID,**listing},'items':[{'id':iid,**i} for iid,i in items.items()],'materials':mats}
 (out/'roof-shopping-live.json').write_text(json.dumps(fixture,default=str,ensure_ascii=False))
 proof.write_text(fingerprint)
 print('ROOF_SHOPPING_READ_ONLY_SNAPSHOT',json.dumps({'items':len(items),'pending':sum(not i.get('bought') for i in items.values())}),flush=True)
