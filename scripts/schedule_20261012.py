import os,json
from google.cloud import firestore
from google.oauth2 import service_account
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
users=[{'id':d.id,**{k:d.to_dict().get(k) for k in ['name','displayName','active','status','role']}} for d in db.collection('users').stream()]
print('SCHEDULE_USERS',json.dumps(users),flush=True)
pid='o3igcYUWRFxNTXRb9kbx'
p=db.collection('projects').document(pid).get();assert p.exists
print('SCHEDULE_PROJECT',json.dumps({'id':pid,**{k:p.to_dict().get(k) for k in ['name','address','employeeSchedule']}}),flush=True)
tasks=[{'id':d.id,**{k:d.to_dict().get(k) for k in ['name','roomId','done','assignedTo','assignedDate','plannedTime']}} for d in db.collection('tasks').where('projectId','==',pid).stream()]
print('SCHEDULE_TASKS',json.dumps(tasks),flush=True)
