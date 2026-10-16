"""Add exact box models and fill missing attributes without overwriting user data."""
import collections,hashlib,json,os,pathlib,re
from urllib.parse import urlsplit
from import_catalog_expansion import identity,active,validate
ALLOWED={'boxWidth','boxHeight','boxDepth','boxVolume','gangs','boxMaterial','boxShape','workType','knockouts','useLocation','boxApplication','mountingType','dimensions'}
def main():
 import firebase_admin
 from firebase_admin import credentials,firestore
 path=pathlib.Path('catalog-expansion/box-products.json')
 manifest=json.loads(pathlib.Path('catalog-expansion/box-manifest.json').read_text())
 if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('Source digest mismatch')
 data=json.loads(path.read_text())
 for row in data['materials']:validate(row)
 for update in data['updates']:
  if set(update['attributes'])-ALLOWED:raise ValueError('Unexpected attribute')
  if urlsplit(update['sourceUrl']).hostname!='www.homedepot.com' or not urlsplit(update['sourceUrl']).path.startswith('/p/'):raise ValueError('Unexpected source')
  for k in ['boxWidth','boxHeight','boxDepth','boxVolume']:
   if k in update['attributes'] and (not isinstance(update['attributes'][k],(int,float)) or update['attributes'][k]<=0):raise ValueError('Invalid dimension')
 key=json.loads(os.environ['FIREBASE_SA'])
 if key.get('project_id')!='obra-manager-4ecc7':raise ValueError('Wrong project')
 firebase_admin.initialize_app(credentials.Certificate(key));db=firestore.client()
 before={doc.id:doc for doc in db.collection('materials').stream()}
 known={identity(doc.to_dict()) for doc in before.values() if identity(doc.to_dict())}
 known_skus={doc.to_dict().get('sku') for doc in before.values()}
 new=[];updates=[];skipped=0
 for row in data['materials']:
  if row['identity'] in known or row['id'] in before or row['sku'] in known_skus:skipped+=1;continue
  new.append(row);known.add(row['identity']);known_skus.add(row['sku'])
 for row in data['updates']:
  snap=before.get(row['id'])
  if not snap:continue
  saved=snap.to_dict()
  if identity(saved)!=row['identity']:raise ValueError('Existing product identity changed')
  if not active(saved):continue
  patch={k:v for k,v in row['attributes'].items() if k not in saved or saved[k] is None or saved[k]==''}
  if not patch:continue
  # Metadata is also missing-only; existing provenance stays intact.
  if not saved.get('boxSpecificationSource'):patch['boxSpecificationSource']=row['sourceUrl']
  evidence=dict(saved.get('boxAttributeEvidence') or {})
  for k in patch:
   if k in row['evidence'] and k not in evidence:evidence[k]=row['evidence'][k]
  patch['boxAttributeEvidence']=evidence
  updates.append((snap,patch))
 backup={snap.id:{k:snap.to_dict().get(k) for k in patch} for snap,patch in updates}
 pathlib.Path('box-update-before.json').write_text(json.dumps(backup,default=str))
 created=[];changed=[]
 for offset in range(0,len(new),50):
  batch=db.batch()
  for row in new[offset:offset+50]:
   body={k:v for k,v in row.items() if k not in ('id','identity')};body.update(createdAt=firestore.SERVER_TIMESTAMP,updatedAt=firestore.SERVER_TIMESTAMP)
   batch.create(db.collection('materials').document(row['id']),body)
  batch.commit();created.extend(r['id'] for r in new[offset:offset+50])
 for offset in range(0,len(updates),50):
  batch=db.batch()
  for snap,patch in updates[offset:offset+50]:
   batch.update(snap.reference,patch,option=db.write_option(last_update_time=snap.update_time))
  batch.commit();changed.extend(snap.id for snap,_ in updates[offset:offset+50])
 after={doc.id:doc.to_dict() for doc in db.collection('materials').stream()}
 for row in new:
  if identity(after.get(row['id'],{}))!=row['identity']:raise ValueError('Created product verification failed')
 for snap,patch in updates:
  for k,v in patch.items():
   if after[snap.id].get(k)!=v:raise ValueError('Attribute verification failed')
  old=snap.to_dict()
  for k,v in old.items():
   if k not in patch and after[snap.id].get(k)!=v:raise ValueError('Existing field changed')
 report={'newProducts':len(created),'existingProductsEnriched':len(changed),'duplicatesSkipped':skipped,'activeRecords':sum(active(x) for x in after.values()),'boxesAndAccessories':sum(active(x) and (x.get('catalogFamily')=='boxes' or x.get('family')=='boxes') for x in after.values()),'withDeclaredVolume':sum(active(x) and bool(x.get('boxVolume')) for x in after.values()),'withDepth':sum(active(x) and bool(x.get('boxDepth')) for x in after.values()),'createdIds':created,'updatedIds':changed,'existingFieldsOverwritten':0,'recordsDeleted':0,'readBackVerified':True}
 pathlib.Path('box-catalog-result.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if not k.endswith('Ids')}))
if __name__=='__main__':main()
