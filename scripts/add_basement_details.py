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

specs = [
    ('Rework basement lighting circuit', 'lighting', [
        'Identify and mark basement lighting outlet locations',
        'Run 14/2 cable for the basement lighting circuit',
        'Replace existing lighting outlet boxes',
        'Secure lighting circuit cables with staples during cable installation',
        'Install light fixtures and complete final wiring connections'
    ]),
    ('Rework basement receptacle circuit', 'receptacles', [
        'Identify and mark basement receptacle locations',
        'Run 12/2 cable for the basement receptacle circuit',
        'Install receptacle outlet boxes',
        'Secure receptacle circuit cables with staples during cable installation',
        'Install receptacles and cover plates and complete final wiring connections'
    ])
]
rooms_query = db.collection('rooms').where(filter=firestore.FieldFilter('projectId', '==', project_id))
tasks_query = db.collection('tasks').where(filter=firestore.FieldFilter('projectId', '==', project_id))
norm = lambda value: str(value or '').strip().casefold()

@firestore.transactional
def add_details(transaction):
    current = project_ref.get(transaction=transaction)
    if not current.exists or any(current.to_dict().get(k) != project.get(k) for k in ['name', 'address', 'scope']):
        raise RuntimeError('Project changed; no writes')
    rooms = [s for s in rooms_query.stream(transaction=transaction) if norm(s.to_dict().get('name')) == 'basement']
    if len(rooms) != 1:
        raise RuntimeError('Expected one basement unit')
    room_id = rooms[0].id
    tasks = list(tasks_query.stream(transaction=transaction))
    plans = []
    for task_name, tag, names in specs:
        found = [s for s in tasks if s.to_dict().get('roomId') == room_id and s.to_dict().get('name') == task_name]
        if len(found) != 1:
            raise RuntimeError('Expected exactly one target task')
        snap = found[0]
        data = snap.to_dict()
        subs = data.get('subtasks') or []
        if not isinstance(subs, list):
            raise RuntimeError('Unexpected subtask schema')
        updated = list(subs)
        for i, name in enumerate(names):
            sid = 'basement-detail-20261015-' + tag + '-' + str(i+1)
            same_name = [s for s in subs if norm(s.get('name')) == norm(name)]
            same_id = [s for s in subs if s.get('id') == sid]
            if len(same_name) > 1 or (same_id and same_id[0].get('name') != name):
                raise RuntimeError('Subtask conflict; no changes applied')
            if not same_name:
                updated.append({'id': sid, 'name': name, 'done': False})
        if updated != subs and data.get('done'):
            raise RuntimeError('Task already completed; review before adding steps')
        plans.append((snap.reference, updated, names))
    for ref, subs, names in plans:
        transaction.update(ref, {'subtasks': subs, 'updatedAt': firestore.SERVER_TIMESTAMP})
    return room_id, [ref.id for ref, _, _ in plans]

room_id, task_ids = add_details(db.transaction())
verified = 0
for task_id, (_, _, names) in zip(task_ids, specs):
    data = db.collection('tasks').document(task_id).get().to_dict()
    if data.get('roomId') != room_id or data.get('projectId') != project_id:
        raise SystemExit('Task ownership verification failed')
    for name in names:
        matches = [s for s in data.get('subtasks', []) if norm(s.get('name')) == norm(name)]
        if len(matches) != 1:
            raise SystemExit('Subtask verification failed')
        verified += 1
print('BASEMENT_DETAILS_VERIFIED ' + json.dumps({'parentTasks': 2, 'subtasksVerified': verified, 'boilerUnchanged': True}))
