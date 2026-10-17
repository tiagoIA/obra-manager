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
  needle='    match /{document=**} { allow read, write: if false; }';assert original.count(needle)==1
  block='''    // Estimates are private to the signed-in owner; existing collections unchanged.
    match /users/{uid}/estimates/{estimateId} {
      function estimateOwner() { return isAuth() && request.auth.uid == uid && isAdmin(); }
      allow read: if estimateOwner();
      allow create: if estimateOwner() && request.resource.data.createdBy == uid && request.resource.data.revision == 1;
      allow update: if estimateOwner() && resource.data.createdBy == uid && request.resource.data.createdBy == uid && request.resource.data.revision == resource.data.revision + 1;
    }
'''
  assert 'match /users/{uid}/estimates/' not in original
  candidate=original.replace(needle,block+needle)
 else:
  # Preserve the existing authenticated policy for every other top-level folder.
  needle='''    match /{allPaths=**} {
      allow read, write: if request.auth != null;
    }''';assert original.count(needle)==1,'Storage policy changed; review manually'
  block='''    match /{folder}/{allPaths=**} {
      allow read, write: if request.auth != null && folder != 'estimateFiles';
    }
    match /estimateFiles/{uid}/{estimateId}/{fileId} {
      allow read, delete: if request.auth != null && request.auth.uid == uid;
      allow create, update: if request.auth != null && request.auth.uid == uid
        && request.resource.size <= 50 * 1024 * 1024
        && request.resource.contentType.matches('(image|video|audio)/.*|application/pdf');
    }'''
  candidate=original.replace(needle,block)
 (root/(kind+'.before.rules')).write_text(original)
 (root/(kind+'.rules')).write_text(candidate)
 manifest[kind]={'release':release,'rulesetName':live['rulesetName'],'name':files[0]['name'],'before_sha256':hashlib.sha256(original.encode()).hexdigest(),'after_sha256':hashlib.sha256(candidate.encode()).hexdigest()}
 print('RULE_CANDIDATE',kind,manifest[kind]['after_sha256'])
(root/'estimate-rules-manifest.json').write_text(json.dumps(manifest,indent=2))
Path('firebase-estimates-test.json').write_text(json.dumps({'firestore':{'rules':'hosting-test/firestore.rules'},'storage':{'rules':'hosting-test/storage.rules'},'emulators':{'firestore':{'port':8080},'storage':{'port':9199},'ui':{'enabled':False},'singleProjectMode':True}}))
