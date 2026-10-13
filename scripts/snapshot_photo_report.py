"""Read-only export of the selected project's report inputs; never writes Firestore."""
import json,os,datetime,hashlib
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
pid='o3igcYUWRFxNTXRb9kbx'
def canonical(value):
 if isinstance(value,dict):return {k:canonical(v) for k,v in value.items()}
 if isinstance(value,list):return [canonical(v) for v in value]
 if hasattr(value,'isoformat'):return value.isoformat()
 if isinstance(value,bytes):return None
 if hasattr(value,'path'):return value.path
 return value

def row(doc):return {'id':doc.id,**canonical(doc.to_dict())}
project=db.collection('projects').document(pid).get();assert project.exists
project=row(project);assert 'arlington' in (project.get('name','')+' '+project.get('address','')).lower()
rooms=[row(d) for d in db.collection('rooms').where('projectId','==',pid).stream()]
tasks=[row(d) for d in db.collection('tasks').where('projectId','==',pid).stream()]
notes=[]
for room in rooms:notes.extend(row(d) for d in db.collection('roomNotes').where('roomId','==',room['id']).stream())
assert any(r.get('name')=='Condensers' for r in rooms)
data={'project':project,'rooms':rooms,'tasks':tasks,'notes':notes,'filters':{'floor':'all','system':'all','status':'all'},'floorOrder':['Basement','Ground Floor','1st Floor','2nd Floor','Common Area','Exterior','Roof']}
path=Path('tmp/photo-report/arlington-input.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False))
print('READ_ONLY_ARLINGTON_SNAPSHOT',json.dumps({'units':len(rooms),'tasks':len(tasks),'fieldRecords':len(notes),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
