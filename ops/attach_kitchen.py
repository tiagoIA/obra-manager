import base64, hashlib, json, os, uuid, glob
from urllib.parse import quote
from google.cloud import firestore, storage
from google.oauth2 import service_account
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PID='project-7316b60c7f14f0210e55cbd5'
RID=PID+'-basement'
TID=RID+'-kitchen-refeed'
OP='melrose-kitchen-refeed-20261016-v1'
k=json.loads(os.environ['FIREBASE_SA'])
assert k['project_id']=='obra-manager-4ecc7'
creds=service_account.Credentials.from_service_account_info(k)
db=firestore.Client(project=k['project_id'],credentials=creds)
bucket=storage.Client(project=k['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
private=serialization.load_pem_private_key(k['private_key'].encode(),None)
target=db.collection('tasks').document(TID)
assert db.collection('rooms').document(RID).get().to_dict()['projectId']==PID
payload=[json.load(open(p)) for p in sorted(glob.glob('ops/kitchen-photo-*.enc.json'))]
assert len(payload)==1 and len({p['sha256'] for p in payload})==1
urls=[]
for p in payload:
    aes=private.decrypt(base64.b64decode(p['key']),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    photo=AESGCM(aes).decrypt(base64.b64decode(p['nonce']),base64.b64decode(p['ciphertext']),p['aad'].encode())
    assert hashlib.sha256(photo).hexdigest()==p['sha256'] and photo[:2]==b'\xff\xd8'
    path='tasks/'+TID+'/kitchen-'+p['sha256']+'.jpg'
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
NAME='Restore power to disconnected kitchen receptacle'
@firestore.transactional
def save(tx):
    snap=target.get(transaction=tx)
    existing=marker.get(transaction=tx)
    tasks=list(tx.get(db.collection('tasks').where('projectId','==',PID)))
    if existing.exists:
        assert snap.exists and all(u in snap.to_dict().get('photos',[]) for u in urls)
        return
    assert not snap.exists
    assert not any('kitchen' in (x.to_dict().get('name') or '').lower() for x in tasks), 'Kitchen task exists; review before creating'
    task={'projectId':PID,'roomId':RID,'name':NAME,'cat':'eletrica','hasQty':False,'qty':0,'done':True,'doneAt':'10/16/2026','photos':urls,'subtasks':[],'note':'Work completed — October 16, 2026: Restored power to the existing kitchen receptacle, which had been disconnected, as reported by Tiago. Photo documents the kitchen receptacle. Recorded under the Melrose basement work package.','createdAt':firestore.SERVER_TIMESTAMP,'reportedBy':'Tiago','sourceOperation':OP}
    tx.create(target,task)
    tx.create(marker,{'projectId':PID,'roomId':RID,'taskId':TID,'createdTask':True,'photoSha256':[p['sha256'] for p in payload],'createdAt':firestore.SERVER_TIMESTAMP})
save(db.transaction())
actual=target.get().to_dict()
assert all(u in actual.get('photos',[]) for u in urls)
assert marker.get().exists
assert actual['done'] and actual['name']==NAME
print('MELROSE_KITCHEN_REFEED_SAVED_VERIFIED',json.dumps({'attachedPhotos':1,'taskName':actual['name'],'totalTaskPhotos':len(actual['photos']),'projectId':PID,'roomId':RID}))
