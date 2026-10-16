"""Apply the owner's reported progress once; keep original records in a private backup."""
import base64, copy, hashlib, json, os, uuid
from urllib.parse import quote
from google.cloud import firestore, storage
from google.oauth2 import service_account
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PID = 'project-7316b60c7f14f0210e55cbd5'
RID = PID + '-basement'
OP = 'melrose-progress-20261016-v1'
LABEL = RID + '-panel-labeling'
DATE = '10/16/2026'
key = json.loads(os.environ['FIREBASE_SA'])
assert key['project_id'] == 'obra-manager-4ecc7'
creds = service_account.Credentials.from_service_account_info(key)
db = firestore.Client(project=key['project_id'], credentials=creds)
operation = db.collection('maintenanceOperations').document(OP)
if operation.get().exists:
    marker = operation.get().to_dict()
    label = db.collection('tasks').document(marker['labelTaskId']).get().to_dict()
    assert label['done'] and label['photos']
    print('ALREADY_SAVED_AND_VERIFIED')
    raise SystemExit(0)

payload = json.load(open('ops/panel-photo.enc.json'))
private = serialization.load_pem_private_key(key['private_key'].encode(), password=None)
aeskey = private.decrypt(base64.b64decode(payload['key']), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
photo = AESGCM(aeskey).decrypt(base64.b64decode(payload['nonce']), base64.b64decode(payload['ciphertext']), payload['aad'].encode())
assert hashlib.sha256(photo).hexdigest() == payload['sha256']
assert photo[:2] == b'\xff\xd8'
bucket = storage.Client(project=key['project_id'], credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
path = 'tasks/' + LABEL + '/final-label-20261016.jpg'
blob = bucket.blob(path)
if blob.exists():
    blob.reload()
    assert hashlib.sha256(blob.download_as_bytes()).hexdigest() == payload['sha256']
    token = blob.metadata.get('firebaseStorageDownloadTokens')
    assert token
else:
    token = str(uuid.uuid4())
    blob.metadata = {'firebaseStorageDownloadTokens': token, 'sourceSha256': payload['sha256']}
    blob.upload_from_string(photo, content_type='image/jpeg', if_generation_match=0)
    assert hashlib.sha256(blob.download_as_bytes()).hexdigest() == payload['sha256']
url = 'https://firebasestorage.googleapis.com/v0/b/' + bucket.name + '/o/' + quote(path, safe='') + '?alt=media&token=' + token.split(',')[0]

def append_note(d, text):
    old = d.get('note') or ''
    line = 'Work update — October 16, 2026: ' + text
    return old if line in old else (old + '\n\n' + line).strip()

def new_task(name, note, done=True, qty=0):
    return {'projectId':PID,'roomId':RID,'name':name,'cat':'eletrica','hasQty':bool(qty),'qty':qty,'done':done,'doneAt':DATE if done else None,'photos':[],'subtasks':[],'note':note,'createdAt':firestore.SERVER_TIMESTAMP,'reportedBy':'Tiago','sourceOperation':OP}

@firestore.transactional
def apply(tx):
    project = db.collection('projects').document(PID).get(transaction=tx)
    room = db.collection('rooms').document(RID).get(transaction=tx)
    marker = operation.get(transaction=tx)
    snaps = list(tx.get(db.collection('tasks').where('roomId','==',RID)))
    assert project.exists and room.exists and room.to_dict()['projectId'] == PID
    assert 'basement' in room.to_dict()['name'].lower()
    assert not marker.exists
    original = {s.id:s.to_dict() for s in snaps}
    for d in original.values(): assert d['projectId'] == PID
    changes = {}
    for suffix, phrase in [('task-01','Install light fixtures and complete final wiring connections'),('task-02','Install receptacles and cover plates and complete final wiring connections')]:
        tid = RID + '-' + suffix
        d = original[tid]
        subs = copy.deepcopy(d.get('subtasks',[]))
        matches = [s for s in subs if s['name'] == phrase]
        assert len(matches) == 1
        matches[0].update(done=True,doneAt=DATE)
        changes[tid] = {'subtasks':subs,'note':append_note(d,'Lighting trim-out completed.' if suffix=='task-01' else 'Basement receptacle trim-out completed. Three additional second-floor receptacles and the junction-box interconnection are recorded separately.')}
    boilerid = RID + '-task-03'
    boiler = original[boilerid]
    subs = copy.deepcopy(boiler.get('subtasks',[]))
    if not subs:
        subs = [{'id':'boiler-prepared-20261016','name':'Prepare the boiler circuit and leave ready for future connection, as requested by the client','done':True,'doneAt':DATE},{'id':'boiler-connect-20261016','name':'Connect the boiler and complete final checks','done':False,'doneAt':None}]
    changes[boilerid] = {'done':False,'doneAt':None,'subtasks':subs,'note':append_note(boiler,'Boiler circuit added and left ready for future connection at the client’s request. Final boiler connection remains pending.')}
    panelid = RID + '-scope-2'
    panel = original[panelid]
    changes[panelid] = {'note':append_note(panel,'Circuit breakers installed, as reported by Tiago. Final panel identification is recorded with its supplied photo under Panel labeling; other panel-work requirements retain their existing status.'),'labelTaskId':LABEL}
    additions = {
      LABEL:new_task('Panel labeling','Final panel labeling completed. Supplied final photo IMG_1907.jpeg documents the circuit identification.'),
      RID+'-second-floor-receptacles':new_task('Install three additional second-floor receptacles','Installed three additional second-floor receptacles using the wiring already left ready. Circuit interconnection is recorded in the junction-box task.',qty=3),
      RID+'-junction-box-interconnection':new_task('Install junction box and interconnect receptacle circuits','Junction box installed to interconnect the additional second-floor receptacles with the basement receptacle circuit.')
    }
    additions[LABEL]['photos'] = [url]
    # Refuse conflicting IDs or equivalent task names rather than duplicate/overwrite.
    for tid,d in additions.items():
        assert tid not in original, 'Target task exists; review before retrying'
        assert not any((x.get('name') or '').strip().lower()==d['name'].lower() for x in original.values()), 'Matching task exists; review before retrying'
    for tid,patch in changes.items(): tx.update(db.collection('tasks').document(tid),patch)
    for tid,d in additions.items(): tx.create(db.collection('tasks').document(tid),d)
    tx.create(operation,{'projectId':PID,'roomId':RID,'labelTaskId':LABEL,'reportedBy':'Tiago','workDate':'2026-10-16','createdAt':firestore.SERVER_TIMESTAMP,'beforeTasks':original,'updatedTaskIds':list(changes),'createdTaskIds':list(additions),'photoSha256':payload['sha256'],'photoStoragePath':path})
    return changes,additions

changes, additions = apply(db.transaction())
for tid,patch in changes.items():
    actual=db.collection('tasks').document(tid).get().to_dict()
    for k,v in patch.items(): assert actual[k] == v
for tid,d in additions.items():
    actual=db.collection('tasks').document(tid).get().to_dict()
    for k,v in d.items():
        if k != 'createdAt': assert actual[k] == v
assert operation.get().exists
print('MELROSE_SAVED_VERIFIED',json.dumps({'updatedTasks':len(changes),'newTasks':len(additions),'panelLabelingDone':True,'panelPhotoAttached':True,'boilerFinalConnectionPending':True,'originalTaskBackupSaved':True}))
