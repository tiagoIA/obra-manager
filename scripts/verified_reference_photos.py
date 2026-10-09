import os,json,urllib.request
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
rows=[('verified-purchase-crf300-20261009','CRF-300','https://honeywell.scene7.com/is/image/Honeywell65/HBT-Fire-CRF-300-STRAIGHT-HiRes'),('verified-purchase-srled-20261009','SRLED','https://honeywell.scene7.com/is/image/Honeywell65/HBT-Fire-SRLED-1')]
updated=0
for mid,model,url in rows:
 response=urllib.request.urlopen(url,timeout=30);assert response.headers.get('Content-Type','').startswith('image/')
 @firestore.transactional
 def add(tx):
  ref=db.collection('materials').document(mid);snap=ref.get(transaction=tx);assert snap.exists and snap.to_dict()['manufacturerPart']==model
  if snap.to_dict().get('photoUrl'):return False
  tx.update(ref,{'photoUrl':url,'photoReferenceNote':None,'photoSource':'verified-manufacturer','updatedAt':firestore.SERVER_TIMESTAMP});return True
 updated+=int(add(db.transaction()))
print('REFERENCE_PHOTOS_VERIFIED',json.dumps({'verifiedManufacturerPhotos':len(rows),'updated':updated,'existingPhotosPreserved':True}))
