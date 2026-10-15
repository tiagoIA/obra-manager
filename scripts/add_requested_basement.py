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
names = ['Rework basement lighting circuit', 'Rework basement receptacle circuit', 'Rework boiler circuit']
rooms_query = db.collection('rooms').where(filter=firestore.FieldFilter('projectId', '==', project_id))
tasks_query = db.collection('tasks').where(filter=firestore.FieldFilter('projectId', '==', project_id))
norm = lambda value: str(value or '').strip().casefold()

@firestore.transactional
def add_basement(transaction):
    current = project_ref.get(transaction=transaction)
    if not current.exists or any(current.to_dict().get(k) != project.get(k) for k in ['name', 'address', 'scope']):
        raise RuntimeError('Project changed; no writes')
    rooms = list(rooms_query.stream(transaction=transaction))
    matching = [s for s in rooms if norm(s.to_dict().get('name')) == 'basement']
    if len(matching) > 1:
        raise RuntimeError('Duplicate basement units require review')
    room_ref = matching[0].reference if matching else db.collection('rooms').document(project_id + '-basement')
    reserved = room_ref.get(transaction=transaction)
    if not matching and reserved.exists:
        raise RuntimeError('Reserved unit identifier conflict')
    tasks = list(tasks_query.stream(transaction=transaction))
    existing = {}
    for name in names:
        found = [s for s in tasks if s.to_dict().get('roomId') == room_ref.id and norm(s.to_dict().get('name')) == norm(name)]
        if len(found) > 1:
            raise RuntimeError('Duplicate requested tasks require review')
        existing[name] = found[0] if found else None
    refs = [db.collection('tasks').document(project_id + '-basement-task-' + str(i + 1).zfill(2)) for i in range(3)]
    reserved_tasks = [ref.get(transaction=transaction) for ref in refs]
    for name, ref, snap in zip(names, refs, reserved_tasks):
        if existing[name] is None and snap.exists:
            raise RuntimeError('Reserved task identifier conflict')
    company_fields = {k: project[k] for k in ['companyId', 'tenantId', 'workspaceId'] if project.get(k)}
    if matching:
        for k, v in company_fields.items():
            if matching[0].to_dict().get(k) not in [None, v]:
                raise RuntimeError('Unit company mismatch')
    if not matching:
        transaction.create(room_ref, {**company_fields, 'projectId': project_id, 'name': 'Basement', 'floor': 'Basement', 'createdAt': firestore.SERVER_TIMESTAMP})
    added = 0
    for i, (name, ref) in enumerate(zip(names, refs)):
        if existing[name] is None:
            transaction.create(ref, {**company_fields, 'projectId': project_id, 'roomId': room_ref.id, 'name': name, 'cat': 'eletrica', 'qty': 0, 'hasQty': False, 'note': '', 'materialId': None, 'materialName': None, 'subtasks': [], 'done': False, 'doneAt': None, 'photos': [], 'sortOrder': i + 1, 'createdAt': firestore.SERVER_TIMESTAMP})
            added += 1
    return room_ref.id, not bool(matching), added

room_id, unit_created, tasks_added = add_basement(db.transaction())
room = db.collection('rooms').document(room_id).get().to_dict()
if room.get('name') != 'Basement' or room.get('projectId') != project_id:
    raise SystemExit('Unit verification failed')
saved_tasks = [s.to_dict() for s in tasks_query.stream() if s.to_dict().get('roomId') == room_id]
for name in names:
    if sum(norm(t.get('name')) == norm(name) for t in saved_tasks) != 1:
        raise SystemExit('Task verification failed')
print('BASEMENT_VERIFIED ' + json.dumps({'unitCreated': unit_created, 'tasksAdded': tasks_added, 'requestedTasksVerified': 3, 'existingProjectPreserved': True}))
