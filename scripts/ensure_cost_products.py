import os,json,re,requests
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import firestore
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
refs=json.loads(Path('scripts/cost_product_refs.json').read_text())
def norm(v):return re.sub('[^a-z0-9]','',str(v or '').lower())
# Verify that each official product image remains available before updating the catalog.
for p in refs:
 r=requests.get(p['photoUrl'],timeout=20);assert r.ok and r.headers.get('Content-Type','').startswith('image/') and len(r.content)>1000,'Product image unavailable'
docs={s.id:s.to_dict() for s in db.collection('materials').stream()};changes=[]
for p in refs:
 code=p['suppliers'][0]['code']
 matches=[mid for mid,m in docs.items() if not m.get('isTask') and (any(norm(s.get('name')) in ['homedepot','thehomedepot'] and s.get('matchVerified') is not False and str(s.get('code'))==code for s in m.get('suppliers',[])) or (norm(m.get('brand'))==norm(p['brand']) and norm(m.get('manufacturerPart'))==norm(p['manufacturerPart'])))]
 assert len(matches)<=1,'Ambiguous catalog product: '+code
 mid=matches[0] if matches else 'verified-hd-'+code;old=docs.get(mid)
 if old:
  assert old.get('recordType')!='family' and old.get('catalogReviewStatus')!='needs-identification','Existing product requires review: '+code
  # Never replace a known different model, color or brand solely from a store code.
  if old.get('brand'):assert norm(old['brand'])==norm(p['brand']),'Brand conflict: '+code
  if old.get('manufacturerPart'):assert norm(old['manufacturerPart']) in [norm(p['manufacturerPart']),norm('R92-GFWT1-0KW') if code=='1001370824' else norm(p['manufacturerPart'])],'Model conflict: '+code
  patch={k:v for k,v in p.items() if not old.get(k) and k not in ['suppliers']}
  suppliers=[dict(s) for s in old.get('suppliers',[])];incoming=p['suppliers'][0]
  found=next((s for s in suppliers if norm(s.get('name')) in ['homedepot','thehomedepot'] and (not s.get('code') or str(s.get('code'))==code)),None)
  if found is None:suppliers.append(incoming)
  else:found.update({k:v for k,v in incoming.items() if k not in ['price','priceDate','priceSource']})
  patch['suppliers']=suppliers
 else:patch={**p,'sku':'MAT-HD-'+code,'qty':0,'isTask':False,'active':True,'status':'active','createdAt':firestore.SERVER_TIMESTAMP}
 patch['updatedAt']=firestore.SERVER_TIMESTAMP;changes.append((mid,old,patch))
@firestore.transactional
def apply(tx):
 snaps=[db.collection('materials').document(mid).get(transaction=tx) for mid,old,p in changes]
 for snap,(mid,old,p) in zip(snaps,changes):assert snap.to_dict()==old,'Concurrent catalog change: '+mid
 for mid,old,p in changes:
  ref=db.collection('materials').document(mid)
  if old is None:tx.create(ref,p)
  else:tx.update(ref,p)
apply(db.transaction())
for mid,old,p in changes:
 m=db.collection('materials').document(mid).get().to_dict();assert m.get('photoUrl')
 if old is not None:assert m.get('qty')==old.get('qty'),'Existing stock changed'
print('COST_PRODUCTS_VERIFIED '+json.dumps({'products':len(changes),'new':sum(old is None for mid,old,p in changes),'imagesVerified':len(refs),'stockPreserved':True}))
