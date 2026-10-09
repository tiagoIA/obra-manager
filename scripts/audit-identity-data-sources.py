"""Read-only photo coverage and asset audit. Never print download URLs or tokens."""
import os,json,io,base64,requests,concurrent.futures
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from importlib.machinery import SourceFileLoader
catalog=SourceFileLoader('catalog','scripts/import-central.py').load_module()
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
s=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))

from google.cloud import storage
fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
r=s.post(fire+':listCollectionIds',json={'pageSize':1000},timeout=60);r.raise_for_status()
print('ROOT_COLLECTIONS',json.dumps(r.json().get('collectionIds',[])))
bucket=storage.Client(project=key['project_id'],credentials=s.credentials).bucket('obra-manager-4ecc7.firebasestorage.app')
ids=['6Slgo0bUln1R3rBe8RY5','AvymoHXdWiMfhrcGMqMm','HAvsU3Xkf359Tkbs5kwO','ih7gJ4TXKQSd5MN3h8KH','rwX7nGbTG9yI2RDM1YkO','vkIv9XEz6Az7A7x3mM7m']
count=0;matches=0
for blob in bucket.list_blobs(prefix='materials/',max_results=20000):
 count+=1
 terms=[t for t in ids+['b300','unistrut','febwfbew','uninstructed'] if t.lower() in blob.name.lower()]
 if terms:
  matches+=1;print('STORED_IDENTITY_ASSET',json.dumps({'path':blob.name,'bytes':blob.size,'contentType':blob.content_type,'matched':terms}))
print('STORED_IDENTITY_ASSET_SUMMARY',json.dumps({'scanned':count,'matches':matches}))
