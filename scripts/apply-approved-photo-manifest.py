"""Apply visually reviewed photo references only; preserve all material and history fields."""
import os,json,io,base64,hashlib,uuid,requests,fitz
from urllib.parse import quote,urlparse
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
from importlib.machinery import SourceFileLoader
catalog=SourceFileLoader('catalog','scripts/import-central.py').load_module()
def enc(v):
 if isinstance(v,str):return {'stringValue':v}
 if isinstance(v,dict):return {'mapValue':{'fields':{k:enc(x) for k,x in v.items()}}}
 raise TypeError('Photo patch accepts only strings/maps')
def main():
 key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
 creds=service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform'])
 s=AuthorizedSession(creds);fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
 bucket=storage.Client(project=key['project_id'],credentials=creds).bucket('obra-manager-4ecc7.firebasestorage.app')
 folder='backups/photo-coverage/'+os.environ['GITHUB_RUN_ID']+'/'
 def read(col):
  docs=[];token=None
  while True:
   params={'pageSize':1000}
   if token:params['pageToken']=token
   r=s.get(fire+'/'+col,params=params,timeout=60);r.raise_for_status();d=r.json();docs+=d.get('documents',[]);token=d.get('nextPageToken')
   if not token:return docs
 def save(name,data):bucket.blob(folder+name).upload_from_string(json.dumps(data,ensure_ascii=False),content_type='application/json',if_generation_match=0)
 docs=read('materials');assert len(docs)==524,'Catalog count changed; audit again'
 originals={d['name']:d for d in docs};by_id={d['name'].split('/')[-1]:d for d in docs};records={i:{k:catalog.decode(v) for k,v in d.get('fields',{}).items()} for i,d in by_id.items()}
 save('materials.json',docs)
 for col in ['shoppingLists','shoppingItems','tasks','productDB','invoices','invoiceItems']:save(col+'.json',read(col))
 plans=json.load(open(os.environ['PHOTO_MANIFEST']));assert len(plans)==int(os.environ['PHOTO_EXPECTED_COUNT'])
 writes=[];cache={};updated=[]
 for p in plans:
  old=records[p['id']]
  assert old['name']==p['expectedName'] and old.get('sku')==p['expectedSku'],'Target identity changed'
  assert old.get('active') is not False and old.get('status')!='inactive' and not old.get('isTask')
  assert not old.get('photoUrl'),'A user already added a photo; audit again'
  assert urlparse(p['photoSourceUrl']).scheme=='https'
  assert urlparse(p['photoSourceUrl']).hostname in {"www.power-sonic.com","digitalassets.resideo.com","static.tp-link.com","prod-edam.honeywell.com","uselectrical.vteximg.com.br","d1unzhqf5a606m.cloudfront.net","www.hesinnovations.com","gw-assets.assaabloy.com","firetekprotection.com","assets.nsiindustries.com","us.store.tapo.com","honeywell.scene7.com","cdn.prod.website-files.com","www.securitron.com","d1unzhqf5a606m.cloudfront.net","firealarmdepot.com","s7d1.scene7.com","www.identisource.net","buy.dmp.com","static.tp-link.com","material.dahuasecurity.com","zktecoma.com"}
  r=requests.get(p['photoSourceUrl'],timeout=45);r.raise_for_status();assert len(r.content)<40000000
  raw=r.content
  if p.get('photoDocumentSha256'):
   assert hashlib.sha256(raw).hexdigest()==p['photoDocumentSha256'],'Manufacturer PDF changed'
   with fitz.open(stream=raw,filetype='pdf') as doc:raw=doc.extract_image(p['photoImageXref'])['image']
  im=Image.open(io.BytesIO(raw));im.load();assert min(im.size)>=80;im=im.convert('RGB');im.thumbnail((1000,1000));b=io.BytesIO();im.save(b,'JPEG',quality=86);payload=b.getvalue()
  assert hashlib.sha256(payload).hexdigest()==p['photoSha256'],'Source image changed after visual review'
  digest=hashlib.sha256(payload).hexdigest();asset='materials/'+p['id']+'/reference-'+digest[:12]+'.jpg';blob=bucket.blob(asset)
  if blob.exists():blob.reload();token=(blob.metadata or {}).get('firebaseStorageDownloadTokens');assert token
  else:
   token=str(uuid.uuid4());blob.metadata={'firebaseStorageDownloadTokens':token,'sourceUrl':p['sourceUrl'],'referenceType':'family'};blob.upload_from_string(payload,content_type='image/jpeg',if_generation_match=0)
  url='https://firebasestorage.googleapis.com/v0/b/'+bucket.name+'/o/'+quote(asset,safe='')+'?alt=media&token='+token
  r=requests.get(url,timeout=40);r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==digest,'Uploaded photo differs'
  provenance=dict(old.get('photoProvenance') or {})
  provenance[os.environ['GITHUB_RUN_ID']]={'sourceUrl':p['sourceUrl'],'photoSourceUrl':p['photoSourceUrl'],'photoSha256':digest,'basis':p['basis'],'reviewedAt':'2026-10-09','type':'family'}
  patch={'photoUrl':url,'photoReferenceType':'family','photoReferenceNote':p['photoReferenceNote'],'photoVerifiedAt':'2026-10-09','photoProvenance':provenance}
  doc=by_id[p['id']];writes.append({'update':{'name':doc['name'],'fields':{k:enc(v) for k,v in patch.items()}},'updateMask':{'fieldPaths':sorted(patch)},'currentDocument':{'updateTime':doc['updateTime']},'updateTransforms':[{'fieldPath':'updatedAt','setToServerValue':'REQUEST_TIME'}]})
  updated.append({'id':p['id'],'sku':p['expectedSku'],'name':p['expectedName'],'type':'family'})
 save('prepared-writes.json',writes);result=None
 try:
  r=s.post(fire+':commit',json={'writes':writes},timeout=90);r.raise_for_status();result=r.json();save('commit-result.json',result)
  after=read('materials');assert {d['name'] for d in after}==set(originals),'Material IDs changed'
  written={w['update']['name']:w for w in writes}
  for d in after:
   before=originals[d['name']].get('fields',{});actual=d.get('fields',{});w=written.get(d['name'])
   mask=set(w['update']['fields'])|{'updatedAt'} if w else set()
   assert {k:v for k,v in before.items() if k not in mask}=={k:v for k,v in actual.items() if k not in mask},'Stock/status/history or another protected field changed'
   if w:assert all(k in actual and catalog.decode(actual[k])==catalog.decode(v) for k,v in w['update']['fields'].items()),'Photo patch differs'
  active=[{k:catalog.decode(v) for k,v in d.get('fields',{}).items()} for d in after if catalog.decode(d.get('fields',{}).get('active',{})) is not False and catalog.decode(d.get('fields',{}).get('status',{}))!='inactive']
  missing=[p for p in active if not p.get('isTask') and not p.get('photoUrl')]
  receipt={'catalogCount':len(after),'newPhotos':len(writes),'activeWithoutPhotos':len(missing),'activeWithPhotos':sum(bool(p.get('photoUrl')) for p in active),'referencePhotos':len(writes),'backup':folder,'updated':updated}
  save('receipt.json',receipt);print('PHOTO_COVERAGE_VERIFIED',json.dumps(receipt,ensure_ascii=False))
 except Exception:
  if result:catalog.rollback(s,fire,writes,result,originals)
  raise
if __name__=='__main__':main()
