import base64, hashlib, json, os, uuid, glob
from urllib.parse import quote
from google.cloud import firestore, storage
from google.oauth2 import service_account
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PID='project-7316b60c7f14f0210e55cbd5'
RID=PID+'-basement'
TID=RID+'-task-01'
OP='melrose-light-photos-20261016-v1'
k=json.loads(os.environ['FIREBASE_SA'])
assert k['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(k)
db=firestore.Client(project=k['project_id'],credentials=creds)
bucket=storage.Client(project=k['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
private=serialization.load_pem_private_key(k['private_key'].encode(),None)
target=db.collection('tasks').document(TID)
d=target.get().to_dict()
assert d and d['projectId']==PID and d['roomId']==RID
assert 'light' in d['name'].lower()
payload=[json.load(open(p)) for p in sorted(glob.glob('ops/light-photo-*.enc.json'))]
assert len(payload)==6 and len({p['sha256'] for p in payload})==6
urls=[]
for p in payload:
    aes=private.decrypt(base64.b64decode(p['key']),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    photo=AESGCM(aes).decrypt(base64.b64decode(p['nonce']),base64.b64decode(p['ciphertext']),p['aad'].encode())
    assert hashlib.sha256(photo).hexdigest()==p['sha256'] and photo[:2]==b'\xff\xd8'
    path='tasks/'+TID+'/light-'+p['sha256']+'.jpg'
    blob=bucket.blob(path)
    if blob.exists():
        blob.reload()
        assert hashlib.sha256(blob.download_as_bytes()).hexdigest()==p['sha256']
        token=blob.metadata['firebaseStorageDownloadTokens']
    else:
        token=str(uuid.uuid4())
        blob.metadata={'firebaseStorageDownloadTokens':token,'sourceSha256':p['sha256']}
        blob.upload_from_string(photo,content_type='image/jpeg',if_generation_match=0)
        assert hashlib.sha256(blob.download_as_bytes()).hexdigest()==p['sha256']
    urls.append('https://firebasestorage.googleapis.com/v0/b/'+bucket.name+'/o/'+quote(path,safe='')+'?alt=media&token='+token.split(',')[0])
marker=db.collection('maintenanceOperations').document(OP)
@firestore.transactional
def save(tx):
    snap=target.get(transaction=tx)
    previous=snap.to_dict()
    existing=marker.get(transaction=tx)
    assert previous['projectId']==PID and previous['roomId']==RID
    if existing.exists:
        assert all(u in previous.get('photos',[]) for u in urls)
        return
    merged=list(previous.get('photos',[]))
    for u in urls:
        if u not in merged: merged.append(u)
    tx.update(target,{'photos':merged})
    tx.create(marker,{'projectId':PID,'roomId':RID,'taskId':TID,'beforePhotos':previous.get('photos',[]),'photoSha256':[p['sha256'] for p in payload],'createdAt':firestore.SERVER_TIMESTAMP})
save(db.transaction())
actual=target.get().to_dict()
assert all(u in actual.get('photos',[]) for u in urls)
assert marker.get().exists
print('MELROSE_LIGHT_PHOTOS_SAVED_VERIFIED',json.dumps({'attachedPhotos':6,'taskName':actual['name'],'totalTaskPhotos':len(actual['photos']),'projectId':PID,'roomId':RID}))
