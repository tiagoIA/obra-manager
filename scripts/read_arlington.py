import json,os,datetime
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account
PROJECT='obra-manager-4ecc7'
key=json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id')!=PROJECT:raise SystemExit('Unexpected project')
db=firestore.Client(project=PROJECT,credentials=service_account.Credentials.from_service_account_info(key))
projects=[s for s in db.collection('projects').stream() if s.to_dict().get('name')=='455 Massachusetts Ave, Arlington, MA']
if len(projects)!=1:raise SystemExit('Expected one Arlington project')
p=projects[0];pid=p.id
rows=lambda c:[{'id':s.id,**s.to_dict()} for s in db.collection(c).where(filter=firestore.FieldFilter('projectId','==',pid)).stream()]
rooms=rows('rooms');ids={r['id'] for r in rooms}
notes=[{'id':s.id,**s.to_dict()} for s in db.collection('roomNotes').stream() if s.to_dict().get('projectId')==pid or s.to_dict().get('roomId') in ids]
def serialize(v):
 if isinstance(v,datetime.datetime):return v.isoformat()
 raise TypeError(type(v).__name__)
Path('report-audit').mkdir(exist_ok=True)
Path('report-audit/arlington.json').write_text(json.dumps({'project':{'id':pid,**p.to_dict()},'rooms':rooms,'tasks':rows('tasks'),'notes':notes,'filters':{},'floorOrder':['1st Floor','Common Area','Exterior']},default=serialize))
print('READ_ONLY_ARLINGTON',len(rooms),'units',len(notes),'field records')
