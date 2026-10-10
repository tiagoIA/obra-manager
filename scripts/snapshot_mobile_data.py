"""Read-only preservation check for collections affected by the mobile UI."""
import hashlib,json,os
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account

key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
collections=['projects','rooms','tasks','materials','shoppingLists','shoppingItems','roomNotes','invoices','invoiceItems','productDB','jobs','reminders','clockEntries']
def canonical(value):
    if isinstance(value,dict):return {k:canonical(v) for k,v in sorted(value.items())}
    if isinstance(value,list):return [canonical(v) for v in value]
    if isinstance(value,bytes):return {'bytesHash':hashlib.sha256(value).hexdigest()}
    if hasattr(value,'isoformat'):return value.isoformat()
    if hasattr(value,'path'):return value.path
    return value
snapshot={}
for collection in collections:
    docs={d.id:canonical(d.to_dict()) for d in db.collection(collection).stream()}
    encoded=json.dumps(docs,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str).encode()
    snapshot[collection]={'count':len(docs),'sha256':hashlib.sha256(encoded).hexdigest()}
path=Path('hosting-test/mobile-data-before.json');path.parent.mkdir(exist_ok=True)
if '--after' in __import__('sys').argv:
    before=json.loads(path.read_text())
    changes=[name for name in collections if snapshot[name]!=before[name]]
    Path('hosting-test/mobile-data-after.json').write_text(json.dumps(snapshot,indent=2))
    if changes:raise RuntimeError('Data changed during the publication window; review concurrent activity: '+', '.join(changes))
    print('MOBILE_DATA_PRESERVED: all 13 collection fingerprints and counts unchanged')
else:
    path.write_text(json.dumps(snapshot,indent=2))
    print('MOBILE_DATA_BASELINE: read-only fingerprints for 13 collections')
