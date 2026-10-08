"""Enrich existing material documents only, with backup and optimistic preconditions."""
import os,json,io,hashlib,pathlib,uuid,re
from urllib.parse import quote, urlparse
import requests
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage

ALLOWED={'brand','manufacturerPart','model','upc','sourceUrl','recordType','specs','description'}
def dec(v):
 if 'integerValue' in v:return int(v['integerValue'])
 for k in ['stringValue','doubleValue','booleanValue','timestampValue','nullValue']:
  if k in v:return v[k]
 if 'arrayValue' in v:return [dec(x) for x in v['arrayValue'].get('values',[])]
 if 'mapValue' in v:return {k:dec(x) for k,x in v['mapValue'].get('fields',{}).items()}
 return None
def enc(v):
 if v is None:return {'nullValue':None}
 if isinstance(v,bool):return {'booleanValue':v}
 if isinstance(v,str):return {'stringValue':v}
 if isinstance(v,int):return {'integerValue':str(v)}
 if isinstance(v,float):return {'doubleValue':v}
 if isinstance(v,list):return {'arrayValue':{'values':[enc(x) for x in v]}}
 return {'mapValue':{'fields':{k:enc(x) for k,x in v.items()}}}
def fill(old,p):
 assert old.get('name')==p['expectedName'] and old.get('sku')==p['expectedSku'],'Identity changed; review again'
 assert not old.get('isTask')
 assert set(p['fields'])<=ALLOWED
 patch={}
 for k,v in p['fields'].items():
  if old.get(k):
   assert old[k]==v or k in {'description','specs','sourceUrl'},'Conflicting existing '+k
   continue
  patch[k]=v
 if p.get('supplier'):
  ref=p['supplier'];assert ref['name'] and ref['code'] and ref['url'].startswith('https://')
  refs=[dict(x) for x in old.get('suppliers') or []]
  same=next((x for x in refs if x.get('name')==ref['name'] and x.get('code')==ref['code']),None)
  if same is None:refs.append(dict(ref))
  else:
   for k,v in ref.items():
    if not same.get(k):same[k]=v
  if refs!=(old.get('suppliers') or []):patch['suppliers']=refs
 return patch
def main():
 key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
 creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
 s=AuthorizedSession(creds);fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
 bucket=storage.Client(project=key['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
 folder='backups/material-enrichment/'+os.environ['GITHUB_RUN_ID']+'/'
 def read(col):
  docs=[];token=None
  while True:
   params={'pageSize':1000}
   if token:params['pageToken']=token
   r=s.get(fire+'/'+col,params=params,timeout=60);r.raise_for_status();d=r.json();docs+=d.get('documents',[]);token=d.get('nextPageToken')
   if not token:return docs
 def save(name,data):bucket.blob(folder+name).upload_from_string(json.dumps(data,ensure_ascii=False),content_type='application/json',if_generation_match=0)
 docs=read('materials');assert len(docs)==495,'Catalog count changed; audit again'
 originals={d['name']:d for d in docs};records={d['name'].split('/')[-1]:{k:dec(v) for k,v in d.get('fields',{}).items()} for d in docs}
 save('materials.json',docs)
 for col in ['shoppingLists','shoppingItems','tasks','productDB','invoices']:save(col+'.json',read(col))
 manifest=json.loads(pathlib.Path(os.environ.get('ENRICHMENT_MANIFEST','material-enrichment-v1.json')).read_text());assert len(manifest)==int(os.environ.get('ENRICHMENT_EXPECTED_COUNT','9'))
 patches={};photos=[]
 for p in manifest:
  ident=p['id'];assert ident in records
  old=records[ident];patch=fill(old,p)
  if p.get('photoSourceUrl') and not old.get('photoUrl'):
   assert urlparse(p['photoSourceUrl']).scheme=='https' and urlparse(p['photoSourceUrl']).hostname in {'static.grainger.com','media.cityelectricsupply.com'}
   r=requests.get(p['photoSourceUrl'],timeout=40);r.raise_for_status();assert len(r.content)<12_000_000
   image_bytes=r.content
   if p.get('photoDocumentSha256'):
    import fitz
    assert hashlib.sha256(r.content).hexdigest()==p['photoDocumentSha256'],'Source PDF changed after review'
    with fitz.open(stream=r.content,filetype='pdf') as pdf:image_bytes=pdf.extract_image(p['photoImageXref'])['image']
   im=Image.open(io.BytesIO(image_bytes));im.load();assert min(im.size)>=80;im=im.convert('RGB');im.thumbnail((1000,1000));b=io.BytesIO();im.save(b,'JPEG',quality=86);raw=b.getvalue()
   assert hashlib.sha256(raw).hexdigest()==p['photoSha256'],'Image changed after visual review'
   asset='materials/'+ident+'/verified-'+p['photoSha256'][:12]+'.jpg';blob=bucket.blob(asset)
   if blob.exists():blob.reload();token=(blob.metadata or {}).get('firebaseStorageDownloadTokens');assert token
   else:
    token=str(uuid.uuid4());blob.metadata={'firebaseStorageDownloadTokens':token,'sourceUrl':p['photoSourceUrl']};blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
   url='https://firebasestorage.googleapis.com/v0/b/'+bucket.name+'/o/'+quote(asset,safe='')+'?alt=media&token='+token
   check=requests.get(url,timeout=40);check.raise_for_status();assert hashlib.sha256(check.content).hexdigest()==p['photoSha256']
   patch.update(photoUrl=url,photoSourceUrl=p['photoSourceUrl'],photoVerifiedAt='2026-10-08');photos.append(ident)
  if patch:
   provenance=dict(old.get('catalogProvenance') or {});provenance['enrichment'+os.environ['GITHUB_RUN_ID']]={'sourceUrl':p.get('manufacturerSourceUrl') or p['fields']['sourceUrl'],'basis':p['basis'],'fields':list(patch),'verifiedAt':'2026-10-08'};patch['catalogProvenance']=provenance;patches[ident]=patch
 # The previous feed supplied some short retailer IDs in its ean field. Preserve retailer codes; remove only these proven non-GTIN copies.
 corrected=[]
 for ident,old in records.items():
  upc=str(old.get('upc') or '')
  if ident.startswith('catalog-') and old.get('importBatch') and upc and not re.fullmatch(r'\d{12,14}',upc):
   assert any(str(x.get('code'))==upc for x in old.get('suppliers') or []),'Unknown short code; requires review'
   patches.setdefault(ident,{})['upc']='';corrected.append(ident)
   provenance=dict(old.get('catalogProvenance') or {});provenance['upcCorrection20261008']={'previousValue':upc,'reason':'ID do distribuidor, sem formato GTIN; preservado em suppliers.code.'};patches[ident]['catalogProvenance']=provenance
 assert len(patches)<=30
 writes=[]
 for ident,patch in patches.items():
  doc=next(d for d in docs if d['name'].endswith('/'+ident))
  writes.append({'update':{'name':doc['name'],'fields':{k:enc(v) for k,v in patch.items()}},'updateMask':{'fieldPaths':sorted(patch)},'currentDocument':{'updateTime':doc['updateTime']},'updateTransforms':[{'fieldPath':'updatedAt','setToServerValue':'REQUEST_TIME'}]})
 save('prepared-writes.json',writes)
 committed=None
 try:
  if writes:
   r=s.post(fire+':commit',json={'writes':writes},timeout=60);r.raise_for_status();committed=r.json();save('commit-result.json',committed)
  after=read('materials');assert {d['name'] for d in after}==set(originals),'Document IDs changed'
  for d in after:
   ident=d['name'].split('/')[-1]
   if ident not in patches:continue
   before=originals[d['name']]['fields'];actual=d.get('fields',{});mask=set(patches[ident])|{'updatedAt'}
   assert {k:v for k,v in before.items() if k not in mask}=={k:v for k,v in actual.items() if k not in mask},'Protected fields changed'
   assert all(actual.get(k)==enc(v) for k,v in patches[ident].items()),'Patch verification failed'
  missing=[]
  for d in after:
   f={k:dec(v) for k,v in d.get('fields',{}).items()}
   if not f.get('photoUrl'):missing.append({'id':d['name'].split('/')[-1],'sku':f.get('sku'),'name':f.get('name'),'reason':'Modelo/variante ou imagem exata ainda não confirmados.'})
  save('pending-identification.json',missing)
  receipt={'catalogCount':len(after),'updatedRecords':len(patches),'newPhotos':len(photos),'correctedNonGtinCodes':len(corrected),'remainingMissingPhotos':len(missing),'updated':[{'sku':records[i].get('sku'),'name':records[i].get('name'),'fields':list(p)} for i,p in patches.items()],'backup':folder}
  save('receipt.json',receipt);print('ENRICH_VERIFIED',json.dumps(receipt,ensure_ascii=False))
 except Exception:
  if committed:
   undo=[{'update':{'name':w['update']['name'],'fields':originals[w['update']['name']]['fields']},'currentDocument':{'updateTime':res['updateTime']}} for w,res in zip(writes,committed['writeResults'])]
   r=s.post(fire+':commit',json={'writes':undo},timeout=60);r.raise_for_status();print('ENRICH_ROLLBACK_VERIFIED',len(undo))
  raise
if __name__=='__main__':main()
