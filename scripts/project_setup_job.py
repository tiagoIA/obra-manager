"""One bounded project setup. Customer data travels only through private Firebase Storage."""
import base64
import hashlib
import json
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from google.cloud import firestore, storage
from google.oauth2 import service_account

PROJECT = 'obra-manager-4ecc7'
BUCKET = PROJECT + '.firebasestorage.app'
config = json.loads(Path('scripts/project-setup-job.json').read_text())
key = json.loads(os.environ['FIREBASE_SA'])
if key.get('project_id') != PROJECT:
    raise SystemExit('Unexpected Firebase project')
if not config['object'].startswith('automation/project-setup/') or '..' in config['object']:
    raise SystemExit('Invalid staging path')
credentials = service_account.Credentials.from_service_account_info(key)
client = storage.Client(project=PROJECT, credentials=credentials)
bucket = client.bucket(BUCKET)
staging = bucket.blob(config['object'])

if config['mode'] == 'prepare':
    url = staging.generate_signed_url(version='v4', expiration=timedelta(minutes=30), method='PUT', content_type='application/json', credentials=credentials)
    public = serialization.load_pem_public_key(Path('scripts/upload-public-key.pem').read_bytes())
    aes_key, nonce = os.urandom(32), os.urandom(12)
    encrypted = AESGCM(aes_key).encrypt(nonce, url.encode(), b'obra-project-setup-v1')
    wrapped = public.encrypt(aes_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    envelope = {name: base64.b64encode(value).decode() for name, value in [('key', wrapped), ('nonce', nonce), ('ciphertext', encrypted)]}
    print('SECURE_UPLOAD_ENVELOPE ' + base64.b64encode(json.dumps(envelope).encode()).decode())
    raise SystemExit(0)
if config['mode'] != 'finish':
    raise SystemExit('Invalid setup phase')

raw = staging.download_as_bytes()
if len(raw) > 3 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != config['payload_sha256']:
    raise SystemExit('Staged payload verification failed')
payload = json.loads(raw)
if set(payload) != {'name', 'address', 'type', 'scope', 'workTypes', 'photo'}:
    raise SystemExit('Unexpected project payload fields')
if payload['type'] != 'residential' or payload['scope'] != 'electrical' or payload['workTypes'] != ['ev-charger']:
    raise SystemExit('Unexpected requested project classification')
if payload['name'] != payload['address'] or not payload['name'].strip():
    raise SystemExit('Project name must match its address')
photo = base64.b64decode(payload['photo']['data'], validate=True)
photo_hash = hashlib.sha256(photo).hexdigest()
if payload['photo']['contentType'] != 'image/jpeg' or photo_hash != payload['photo']['sha256'] or not photo.startswith(b'\xff\xd8'):
    raise SystemExit('Facade verification failed')

db = firestore.Client(project=PROJECT, credentials=credentials)
matches = {}
for field in ['name', 'address']:
    for doc in db.collection('projects').where(filter=firestore.FieldFilter(field, '==', payload[field])).stream():
        matches[doc.id] = doc
if len(matches) > 1:
    raise SystemExit('Multiple matching projects; no project was modified')
existing = next(iter(matches.values()), None)
if existing and any(existing.to_dict().get(field) != payload[field] for field in ['name', 'address']):
    raise SystemExit('Matching project needs review; no project was modified')
project_id = existing.id if existing else 'project-' + hashlib.sha256(payload['address'].casefold().strip().encode()).hexdigest()[:24]
target = db.collection('projects').document(project_id)
storage_path = 'projects/facades/imports/' + project_id + '/' + photo_hash + '.jpg'
blob = bucket.blob(storage_path)
if blob.exists():
    blob.reload()
    if hashlib.sha256(blob.download_as_bytes()).hexdigest() != photo_hash:
        raise SystemExit('Existing facade file mismatch; no overwrite attempted')
    token = (blob.metadata or {}).get('firebaseStorageDownloadTokens')
    if not token:
        token = str(uuid4()); blob.metadata = {**(blob.metadata or {}), 'firebaseStorageDownloadTokens': token}; blob.patch()
else:
    token = str(uuid4())
    blob.metadata = {'firebaseStorageDownloadTokens': token, 'sourceSha256': photo_hash}
    blob.upload_from_string(photo, content_type='image/jpeg', if_generation_match=0)
if hashlib.sha256(blob.download_as_bytes()).hexdigest() != photo_hash:
    raise SystemExit('Facade upload verification failed')
facade = {'url': 'https://firebasestorage.googleapis.com/v0/b/' + BUCKET + '/o/' + quote(storage_path, safe='') + '?alt=media&token=' + token,
          'storagePath': storage_path, 'uploadedBy': key['client_email'], 'sha256': photo_hash}

@firestore.transactional
def save_project(transaction):
    snap = target.get(transaction=transaction)
    if snap.exists:
        current = snap.to_dict()
        if any(current.get(field) != payload[field] for field in ['name', 'address']):
            raise RuntimeError('Project changed concurrently; no overwrite attempted')
        if current.get('type') != payload['type'] or current.get('scope') != payload['scope']:
            raise RuntimeError('Existing classification requires review')
        transaction.update(target, {'facadePhoto': facade, 'workTypes': firestore.ArrayUnion(['ev-charger']), 'updatedAt': firestore.SERVER_TIMESTAMP})
        return False
    transaction.create(target, {
        'name': payload['name'], 'address': payload['address'], 'type': payload['type'], 'scope': payload['scope'],
        'workTypes': payload['workTypes'], 'customWorkType': '', 'facadePhoto': facade,
        'scopeBrief': {'before': '', 'workScope': '', 'observations': '', 'photos': [], 'captureStatus': 'before-photos-needed'},
        'createdAt': firestore.SERVER_TIMESTAMP
    })
    return True

created = save_project(db.transaction())
saved = target.get().to_dict()
if saved['name'] != payload['name'] or saved['facadePhoto']['sha256'] != photo_hash or 'ev-charger' not in saved.get('workTypes', []):
    raise SystemExit('Saved project verification failed')
tasks = sum(1 for _ in db.collection('tasks').where(filter=firestore.FieldFilter('projectId', '==', project_id)).stream())
print('PROJECT_SETUP_VERIFIED ' + json.dumps({'projectId': project_id, 'created': created, 'facadeVerified': True, 'taskCount': tasks}))


# Add the concise installation tasks requested by the project owner.
task_specs = [
    ('Assess cable route', ''),
    ('Drill exterior-to-basement cable penetration', ''),
    ('Run circuit cable to electrical panel', ''),
    ('Install mounting bracket and secure EV charger', ''),
    ('Terminate wiring at EV charger', ''),
    ('Install circuit breaker and terminate panel wiring', ''),
    ('Label EV Charger Circuit - Photo Required', 'Attach a clear, legible photo of the EV charger circuit identification on the panel.'),
    ('Test EV charger and complete installation', ''),
    ('Secure Cables with Clamps', 'Install cable clamps and verify all cables are securely supported.'),
    ('Overall Installation - Final Photos', 'Attach overview photos of the completed installation after jobsite cleanup.'),
]
room_ref = db.collection('rooms').document(project_id + '-ev-installation')
task_refs = [db.collection('tasks').document(project_id + '-ev-task-' + str(i + 1).zfill(2)) for i in range(len(task_specs))]

@firestore.transactional
def add_requested_tasks(transaction):
    project_snap = target.get(transaction=transaction)
    room_snap = room_ref.get(transaction=transaction)
    task_snaps = [ref.get(transaction=transaction) for ref in task_refs]
    if not project_snap.exists or project_snap.to_dict().get('scope') != 'electrical':
        raise RuntimeError('Expected electrical project is unavailable')
    if room_snap.exists and room_snap.to_dict().get('projectId') != project_id:
        raise RuntimeError('Installation area conflict')
    for snap, (name, note) in zip(task_snaps, task_specs):
        if snap.exists and any(snap.to_dict().get(k) != v for k, v in {'projectId': project_id, 'roomId': room_ref.id, 'name': name}.items()):
            raise RuntimeError('Existing task differs; no changes applied')
    if not room_snap.exists:
        transaction.create(room_ref, {'projectId': project_id, 'name': 'EV Charger Installation', 'floor': 'Other', 'createdAt': firestore.SERVER_TIMESTAMP})
    count = 0
    for i, (ref, snap, (name, note)) in enumerate(zip(task_refs, task_snaps, task_specs)):
        if not snap.exists:
            transaction.create(ref, {'projectId': project_id, 'roomId': room_ref.id,
                'name': name, 'cat': 'eletrica', 'qty': 0, 'hasQty': False, 'note': note,
                'materialId': None, 'materialName': None, 'subtasks': [], 'done': False,
                'doneAt': None, 'photos': [], 'sortOrder': i + 1, 'createdAt': firestore.SERVER_TIMESTAMP})
            count += 1
    return count

added = add_requested_tasks(db.transaction())
for ref, (name, note) in zip(task_refs, task_specs):
    result = ref.get().to_dict()
    if result.get('name') != name or result.get('note') != note or result.get('roomId') != room_ref.id:
        raise SystemExit('Saved task verification failed')
print('REQUESTED_TASKS_VERIFIED ' + json.dumps({'added': added, 'verified': len(task_specs), 'panelLabelPhotoInstruction': True}))
