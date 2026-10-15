"""Add only the requested basement unit and three electrical tasks.
Customer address is read from the existing private setup object, never logged.
"""
import hashlib
import json
import os
from google.cloud import firestore, storage
from google.oauth2 import service_account

PROJECT = 'obra-manager-4ecc7'
key = json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id') != PROJECT:
    raise SystemExit('Unexpected Firebase project')
credentials = service_account.Credentials.from_service_account_info(key)
bucket = storage.Client(project=PROJECT, credentials=credentials).bucket(PROJECT + '.firebasestorage.app')
raw = bucket.blob('automation/project-setup/384c6038-e262-4b21-a341-d666f35068f2.json').download_as_bytes()
if hashlib.sha256(raw).hexdigest() != 'e5ba3ac9dd6f11d97e51e69185aa0a97fd83c0eef755bb7c3b988da9ac7ca090':
    raise SystemExit('Private setup reference mismatch')
payload = json.loads(raw)
if payload.get('name') != payload.get('address') or payload.get('type') != 'residential' or payload.get('scope') != 'electrical' or payload.get('workTypes') != ['ev-charger']:
    raise SystemExit('Unexpected project reference')
db = firestore.Client(project=PROJECT, credentials=credentials)
matches = list(db.collection('projects').where(filter=firestore.FieldFilter('address', '==', payload['address'])).stream())
if len(matches) != 1:
    raise SystemExit('Expected exactly one existing project')
project_ref = matches[0].reference
project_id = project_ref.id
project = matches[0].to_dict()
if project.get('name') != payload['name'] or project.get('scope') != 'electrical':
    raise SystemExit('Project classification mismatch')


norm=lambda v:str(v or '').strip().casefold()
room_query=db.collection('rooms').where(filter=firestore.FieldFilter('projectId','==',project_id))
task_query=db.collection('tasks').where(filter=firestore.FieldFilter('projectId','==',project_id))
shared_ref=db.collection('tasks').document(project_id+'-basement-cable-support')
backup_ref=db.collection('automationBackups').document(project_id+'-basement-cable-support-20261015')
@firestore.transactional
def consolidate(transaction):
 current=project_ref.get(transaction=transaction)
 if not current.exists or any(current.to_dict().get(k)!=project.get(k) for k in ['name','address','scope']):
  raise RuntimeError('Project changed')
 rooms=[s for s in room_query.stream(transaction=transaction) if norm(s.to_dict().get('name'))=='basement']
 if len(rooms)!=1:raise RuntimeError('Expected exactly one Basement')
 room_id=rooms[0].id
 snapshots=list(task_query.stream(transaction=transaction))
 tasks=[s for s in snapshots if s.to_dict().get('roomId')==room_id]
 shared=shared_ref.get(transaction=transaction)
 backup=backup_ref.get(transaction=transaction)
 if shared.exists:
  if not backup.exists or shared.to_dict().get('migration')!='basement-cable-support-20261015':raise RuntimeError('Shared task conflict')
  return room_id,False
 if backup.exists:raise RuntimeError('Existing backup without migration result')
 if any(norm(s.to_dict().get('name'))=='secure and support all basement cables' for s in tasks):raise RuntimeError('Duplicate support task')
 sources=[]
 for parent,sub in [
  ('Rework basement lighting circuit','Secure lighting circuit cables with staples during cable installation'),
  ('Rework basement receptacle circuit','Secure receptacle circuit cables with staples during cable installation')]:
  found=[s for s in tasks if s.to_dict().get('name')==parent]
  if len(found)!=1:raise RuntimeError('Target parent conflict')
  data=found[0].to_dict()
  subs=data.get('subtasks') or []
  support=[s for s in subs if s.get('name')==sub]
  if len(support)!=1:raise RuntimeError('Support subtask conflict')
  sources.append((found[0],data,support[0],[s for s in subs if s.get('id')!=support[0].get('id')]))
 done=all(bool(s[2].get('done')) for s in sources)
 photos=[]
 for _,_,s,_ in sources:
  for photo in s.get('photos') or []:
   if photo not in photos:photos.append(photo)
 notes=['Secure and support all new basement lighting and receptacle cables with staples or approved supports during cable installation.']
 notes += [s[2]['note'] for s in sources if s[2].get('note')]
 company={k:project[k] for k in ['companyId','tenantId','workspaceId'] if project.get(k)}
 transaction.create(backup_ref,{'projectId':project_id,'roomId':room_id,'createdAt':firestore.SERVER_TIMESTAMP,
  'operation':'Consolidate duplicate cable support subtasks','originalTasks':{s[0].id:s[1] for s in sources}})
 transaction.create(shared_ref,{**company,'projectId':project_id,'roomId':room_id,'name':'Secure and support all basement cables',
  'cat':'eletrica','qty':0,'hasQty':False,'note':'\n'.join(notes),'materialId':None,'materialName':None,
  'subtasks':[],'done':done,'doneAt':(next((s[2].get('doneAt') for s in sources if s[2].get('doneAt')),None) if done else None),
  'photos':photos,'sortOrder':3.5,'createdAt':firestore.SERVER_TIMESTAMP,'migration':'basement-cable-support-20261015'})
 for snap,data,sub,remaining in sources:
  update={'subtasks':remaining,'updatedAt':firestore.SERVER_TIMESTAMP}
  if data.get('done') and not all(s.get('done') for s in remaining):update.update(done=False,doneAt=None)
  transaction.update(snap.reference,update)
 return room_id,True
room_id,changed=consolidate(db.transaction())
saved=[s.to_dict() for s in task_query.stream() if s.to_dict().get('roomId')==room_id]
support=[t for t in saved if t.get('migration')=='basement-cable-support-20261015']
if len(support)!=1:raise SystemExit('Support verification failed')
parents=[t for t in saved if t.get('name') in ['Rework basement lighting circuit','Rework basement receptacle circuit']]
if len(parents)!=2 or any(any('staples during' in s.get('name','') for s in t.get('subtasks') or []) for t in parents):raise SystemExit('Parent verification failed')
def fraction(t):
 if t.get('done'):return 1
 ss=t.get('subtasks') or []
 return sum(bool(s.get('done')) for s in ss)/len(ss) if ss else 0
print('BASEMENT_CONSOLIDATION_VERIFIED '+json.dumps({'changed':changed,'tasks':len(saved),'completedTasks':sum(bool(t.get('done')) for t in saved),
 'progressPercent':round(sum(fraction(t) for t in saved)/len(saved)*100),'sharedSupportDone':support[0].get('done'),'remainingSteps':[len(t.get('subtasks') or []) for t in parents],
 'photoNoticesPreserved':sum('PHOTOS REQUIRED:' in (t.get('note') or '') for t in saved)==2,'backupSaved':True}))
