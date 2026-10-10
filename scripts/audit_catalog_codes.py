"""Read-only audit of store catalog identifiers; never writes business data."""
import json,os,re,hashlib
from pathlib import Path
from collections import Counter
from google.cloud import firestore
from google.oauth2 import service_account
key=json.loads(os.environ['FIREBASE_SA'])
assert key['project_id']=='obra-manager-4ecc7'
db=firestore.Client(project=key['project_id'],credentials=service_account.Credentials.from_service_account_info(key))
safe_fields={'name','sku','gceCode','brand','manufacturerPart','model','upc','unit','cat','isTask','recordType','active','status','catalogReviewStatus','sourceUrl','company','description','materialId','code'}
ref_fields={'name','code','internetId','aliasCodes','matchVerified','url','unit'}
out={'collections':{},'storeCounts':{},'storeVerifiedCounts':{},'codedMaterialCount':0,'roof':{}}
for collection in ['materials','productDB']:
    records=[];keys=Counter()
    for doc in db.collection(collection).stream():
        raw=doc.to_dict();keys.update(raw.keys())
        row={'id':doc.id,**{k:raw[k] for k in safe_fields if k in raw}}
        row['suppliers']=[{k:s[k] for k in ref_fields if k in s} for s in raw.get('suppliers',[]) if isinstance(s,dict)]
        row['otherIdentifierFields']={k:v for k,v in raw.items() if re.search(r'(code|sku|catalog|supplier|store|internet)',k,re.I) and k not in safe_fields and k!='suppliers' and isinstance(v,(str,int,float,bool,type(None)))}
        records.append(row)
    out['collections'][collection]={'count':len(records),'fieldNames':dict(keys),'records':records}
counts=Counter();verified=Counter()
for m in out['collections']['materials']['records']:
    if m.get('isTask'):continue
    refs=m['suppliers'][:]
    if m.get('gceCode') and not any(s.get('name')=='Granite City Electric' for s in refs):refs.append({'name':'Granite City Electric','code':m['gceCode']})
    names={s.get('name','Unnamed') for s in refs if s.get('code') or s.get('internetId')}
    ok={s.get('name','Unnamed') for s in refs if (s.get('code') or s.get('internetId')) and s.get('matchVerified') is not False}
    counts.update(names);verified.update(ok)
    if names:out['codedMaterialCount']+=1
out['storeCounts']=dict(counts);out['storeVerifiedCounts']=dict(verified)
lid='3MR0tydWGIHwMrLmYUq6'
list_doc=db.collection('shoppingLists').document(lid).get()
if list_doc.exists:
    raw=list_doc.to_dict();out['roof']['list']={k:raw.get(k) for k in ['name','purchasingSupplier']}
out['roof']['items']=[]
for doc in db.collection('shoppingItems').where('listId','==',lid).stream():
    raw=doc.to_dict();out['roof']['items'].append({'id':doc.id,**{k:raw.get(k) for k in ['name','matId','referenceMaterialId','unit','qty']}})
p=Path('hosting-test/catalog-codes-audit.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(out,indent=2,default=str))
print('READ_ONLY_CATALOG_AUDIT',json.dumps({'materials':out['collections']['materials']['count'],'codedMaterials':out['codedMaterialCount'],'stores':out['storeCounts'],'verifiedStores':out['storeVerifiedCounts'],'productDB':out['collections']['productDB']['count']}))
