"""Prepare narrowly scoped rule additions while retaining the live originals."""
import json,os,hashlib
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
key=json.loads(os.environ['FIREBASE_SA'])
assert key.get('project_id')=='obra-manager-4ecc7'
session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
root=Path('hosting-test');root.mkdir(exist_ok=True)
manifest={}
for kind,release in [('firestore','cloud.firestore'),('storage','firebase.storage/obra-manager-4ecc7.firebasestorage.app')]:
 base='https://firebaserules.googleapis.com/v1/projects/obra-manager-4ecc7/'
 r=session.get(base+'releases/'+release,timeout=30);r.raise_for_status();live=r.json()
 r=session.get('https://firebaserules.googleapis.com/v1/'+live['rulesetName'],timeout=30);r.raise_for_status()
 files=r.json()['source']['files'];assert len(files)==1,'Review multiple-source rules before publishing'
 original=files[0]['content'];candidate=original
 if kind=='firestore':
  assert hashlib.sha256(original.encode()).hexdigest()=='a0867d768522f036fa8170232e25dcad2f00caca3ec9add68ff1c1f74a86fe10','Live Firestore rules changed; review before publishing'
  old='function estimateOwner() { return isAuth() && request.auth.uid == uid && isAdmin(); }'
  new="function estimateOwner() { return isAuth() && request.auth.uid == uid && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'owner'; }"
  assert original.count(old)==1;candidate=original.replace(old,new)
  extra="""    function fieldEstimateUser() {
      return isAuth() && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['supervisor','foreman','owner','master','admin'];
    }
    function financialEstimateOwner() {
      return isAuth() && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'owner';
    }
    match /users/{uid}/estimateCaptures/{captureId} {
      allow read: if fieldEstimateUser() && (request.auth.uid == uid || (financialEstimateOwner() && resource.data.approverUid == request.auth.uid && resource.data.status == 'Submitted'));
      allow create, update: if fieldEstimateUser() && request.auth.uid == uid
        && request.resource.data.createdBy == uid
        && request.resource.data.status in ['Draft','Submitted']
        && request.resource.data.keys().hasOnly(['id','revision','title','client','address','projectId','approverUid','status','notes','exclusions','rooms','visits','files','items','history','createdBy','createdAt','updatedAt']);
    }
    match /users/{owner}/estimateIntake/{requestId} {
      allow read: if financialEstimateOwner() && request.auth.uid == owner;
      allow create, update: if fieldEstimateUser()
        && request.resource.data.sourceUid == request.auth.uid
        && requestId == request.auth.uid + '~' + request.resource.data.captureId
        && request.resource.data.keys().hasOnly(['sourceUid','captureId','title','revision','status'])
        && request.resource.data.status == 'Pending review'
        && get(/databases/$(database)/documents/users/$(owner)).data.role == 'owner'
        && getAfter(/databases/$(database)/documents/users/$(request.auth.uid)/estimateCaptures/$(request.resource.data.captureId)).data.approverUid == owner
        && getAfter(/databases/$(database)/documents/users/$(request.auth.uid)/estimateCaptures/$(request.resource.data.captureId)).data.status == 'Submitted';
      allow update: if financialEstimateOwner() && request.auth.uid == owner
        && request.resource.data.diff(resource.data).affectedKeys().hasOnly(['status','importedEstimateId'])
        && request.resource.data.status == 'Imported';
    }
"""
  needle='    match /{document=**} { allow read, write: if false; }';assert candidate.count(needle)==1
  candidate=candidate.replace(needle,extra+needle)
 else:
  assert hashlib.sha256(original.encode()).hexdigest()=='ab2bafffc96235e5f6f6db52da6c0c0cea3becdf1e9414f08f5cacaf80abee63','Live Storage rules changed; review before publishing'
  old='allow read, delete: if request.auth != null && request.auth.uid == uid;'
  new="""allow read: if request.auth != null && (request.auth.uid == uid || resource.metadata.reviewOwner == request.auth.uid);
      allow delete: if request.auth != null && request.auth.uid == uid;"""
  assert original.count(old)==1;candidate=original.replace(old,new)
 (root/(kind+'.before.rules')).write_text(original)
 (root/(kind+'.rules')).write_text(candidate)
 manifest[kind]={'release':release,'rulesetName':live['rulesetName'],'name':files[0]['name'],'before_sha256':hashlib.sha256(original.encode()).hexdigest(),'after_sha256':hashlib.sha256(candidate.encode()).hexdigest()}
 print('RULE_CANDIDATE',kind,manifest[kind]['after_sha256'])
(root/'estimate-rules-manifest.json').write_text(json.dumps(manifest,indent=2))
Path('firebase-estimates-test.json').write_text(json.dumps({'firestore':{'rules':'hosting-test/firestore.rules'},'storage':{'rules':'hosting-test/storage.rules'},'emulators':{'firestore':{'port':8080},'storage':{'port':9199},'ui':{'enabled':False},'singleProjectMode':True}}))
