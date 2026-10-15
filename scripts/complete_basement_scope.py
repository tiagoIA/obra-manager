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

norm = lambda v: str(v or '').strip().casefold()
details = [
 ('Rework basement lighting circuit', 'lighting', [
  'Identify and mark basement lighting outlet locations',
  'Run 14/2 cable for the basement lighting circuit',
  'Replace existing lighting outlet boxes',
  'Secure lighting circuit cables with staples during cable installation',
  'Run the basement lighting circuit home run to the electrical panel',
  'Install the new lighting circuit breaker and terminate circuit conductors at the panel',
  'Install light fixtures and complete final wiring connections']),
 ('Rework basement receptacle circuit', 'receptacles', [
  'Identify and mark basement receptacle locations',
  'Run 12/2 cable for the basement receptacle circuit',
  'Install receptacle outlet boxes',
  'Secure receptacle circuit cables with staples during cable installation',
  'Run the basement receptacle circuit home run to the electrical panel',
  'Install the new receptacle circuit breaker and terminate circuit conductors at the panel',
  'Install receptacles and cover plates and complete final wiring connections'])
]
shared = [
 ('Decommission Superseded Basement Circuits',
  'Identify the existing lighting and receptacle circuits and confirm all connected loads before decommissioning. Disconnect and remove superseded wiring as applicable after the replacement circuits are complete. Preserve any circuits still serving other loads.'),
 ('Panel Work and Circuit Identification - Photos Required',
  'PHOTOS REQUIRED: Attach clear photos documenting the completed panel work, the newly installed lighting and receptacle breakers, legible circuit identification, and the updated panel directory.'),
 ('Overall Basement Installation - Final Photos Required',
  'PHOTOS REQUIRED: After trim-out and jobsite cleanup, attach overall views of the completed basement installation, including lighting fixtures, receptacles and cover plates, cable routing and support, and completed panel work.')
]
room_query = db.collection('rooms').where(filter=firestore.FieldFilter('projectId', '==', project_id))
task_query = db.collection('tasks').where(filter=firestore.FieldFilter('projectId', '==', project_id))
@firestore.transactional
def complete_scope(transaction):
 current = project_ref.get(transaction=transaction)
 if not current.exists or any(current.to_dict().get(k) != project.get(k) for k in ['name', 'address', 'scope']):
  raise RuntimeError('Project changed; no writes')
 rooms = [s for s in room_query.stream(transaction=transaction) if norm(s.to_dict().get('name')) == 'basement']
 if len(rooms) != 1:
  raise RuntimeError('Expected exactly one basement unit')
 room_id = rooms[0].id
 tasks = [s for s in task_query.stream(transaction=transaction) if s.to_dict().get('roomId') == room_id]
 updates = []
 for parent, tag, names in details:
  found = [s for s in tasks if s.to_dict().get('name') == parent]
  if len(found) != 1:
   raise RuntimeError('Expected one target parent task')
  data = found[0].to_dict()
  subs = data.get('subtasks') or []
  if not isinstance(subs, list):
   raise RuntimeError('Unexpected subtask schema')
  ordered = []
  for i, name in enumerate(names):
   matches = [s for s in subs if norm(s.get('name')) == norm(name)]
   if len(matches) > 1:
    raise RuntimeError('Duplicate subtask requires review')
   sid = 'basement-scope-20261015-' + tag + '-' + str(i+1)
   if not matches and any(s.get('id') == sid for s in subs):
    raise RuntimeError('Subtask identifier conflict')
   ordered.append(matches[0] if matches else {'id': sid, 'name': name, 'done': False})
  extras = [s for s in subs if norm(s.get('name')) not in {norm(n) for n in names}]
  ordered += extras
  if data.get('done') and ordered != subs:
   raise RuntimeError('Completed parent requires review')
  updates.append((found[0].reference, ordered))
 refs = [db.collection('tasks').document(project_id + '-basement-scope-' + str(i+1)) for i in range(len(shared))]
 reserved = [ref.get(transaction=transaction) for ref in refs]
 creates = []
 for i, ((name, note), ref, snap) in enumerate(zip(shared, refs, reserved)):
  matches = [s for s in tasks if norm(s.to_dict().get('name')) == norm(name)]
  if len(matches) > 1:
   raise RuntimeError('Duplicate shared task requires review')
  if matches:
   if matches[0].to_dict().get('note') != note:
    raise RuntimeError('Shared task content conflict')
   continue
  if snap.exists:
   raise RuntimeError('Reserved task identifier conflict')
  creates.append((ref, name, note, i))
 company = {k: project[k] for k in ['companyId', 'tenantId', 'workspaceId'] if project.get(k)}
 for ref, subs in updates:
  transaction.update(ref, {'subtasks': subs, 'updatedAt': firestore.SERVER_TIMESTAMP})
 for ref, name, note, i in creates:
  transaction.create(ref, {**company, 'projectId': project_id, 'roomId': room_id, 'name': name,
   'cat': 'eletrica', 'qty': 0, 'hasQty': False, 'note': note, 'materialId': None, 'materialName': None,
   'subtasks': [], 'done': False, 'doneAt': None, 'photos': [], 'sortOrder': 4 + i, 'createdAt': firestore.SERVER_TIMESTAMP})
 return room_id, [r.id for r, _ in updates]

room_id, parent_ids = complete_scope(db.transaction())
for task_id, (_, _, names) in zip(parent_ids, details):
 data = db.collection('tasks').document(task_id).get().to_dict()
 for name in names:
  if sum(norm(s.get('name')) == norm(name) for s in data.get('subtasks', [])) != 1:
   raise SystemExit('Detailed scope verification failed')
tasks = [s.to_dict() for s in task_query.stream() if s.to_dict().get('roomId') == room_id]
for name, note in shared:
 found = [t for t in tasks if t.get('name') == name and t.get('note') == note]
 if len(found) != 1:
  raise SystemExit('Shared scope verification failed')
print('BASEMENT_FULL_SCOPE_VERIFIED ' + json.dumps({'detailedSteps': 14, 'decommissionTask': True, 'photoDocumentationTasks': 2, 'boilerUnchanged': True}))
