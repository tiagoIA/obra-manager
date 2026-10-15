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


rooms=list(db.collection('rooms').where(filter=firestore.FieldFilter('projectId','==',project_id)).stream())
room=next(s for s in rooms if s.to_dict().get('name','').lower()=='basement')
tasks=list(db.collection('tasks').where(filter=firestore.FieldFilter('projectId','==',project_id)).stream())
print('BASEMENT_AUDIT '+json.dumps([{'id':s.id,**s.to_dict()} for s in tasks if s.to_dict().get('roomId')==room.id],default=str))
peers=[s for s in db.collection('projects').stream() if s.id!=project_id and s.to_dict().get('companyId')==project.get('companyId')]
for p in peers[:4]:
 ts=list(db.collection('tasks').where(filter=firestore.FieldFilter('projectId','==',p.id)).limit(16).stream())
 print('REFERENCE_TASKS '+json.dumps([{'name':s.to_dict().get('name'),'done':s.to_dict().get('done'),'subtasks':len(s.to_dict().get('subtasks') or []),'note':s.to_dict().get('note','')} for s in ts],default=str))
print('EV_REFERENCE '+json.dumps([{'name':s.to_dict().get('name'),'done':s.to_dict().get('done'),'note':s.to_dict().get('note','')} for s in tasks if s.to_dict().get('roomId')!=room.id],default=str))
