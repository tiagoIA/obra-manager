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

fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
targets={'6Slgo0bUln1R3rBe8RY5','AvymoHXdWiMfhrcGMqMm','HAvsU3Xkf359Tkbs5kwO','ih7gJ4TXKQSd5MN3h8KH','rwX7nGbTG9yI2RDM1YkO','vkIv9XEz6Az7A7x3mM7m'}
terms=['b300','febwfbew','uninstructed','point of attachment','pipe lines for smoke','pipe lines for smoke’s','unistrut clamp']
safe={'name','title','productName','materialName','description','specs','sku','model','manufacturerPart','partNumber','catalogCode','gceCode','brand','unit','qty','quantity','materialId','productId','itemId','recordType','isTask','status','active','importBatch','createdAt','updatedAt'}
def read(col):
 docs=[];token=None
 while True:
  params={'pageSize':1000}
  if token:params['pageToken']=token
  r=s.get(fire+'/'+col,params=params,timeout=60);r.raise_for_status();d=r.json();docs+=d.get('documents',[]);token=d.get('nextPageToken')
  if not token:return docs
def strings(v):
 if isinstance(v,str):yield v
 elif isinstance(v,dict):
  for x in v.values():yield from strings(x)
 elif isinstance(v,list):
  for x in v:yield from strings(x)
def scrub(v):
 if isinstance(v,dict):
  out={}
  for k,x in v.items():
   if k in safe and isinstance(x,(str,int,float,bool,type(None))):
    if isinstance(x,str) and ('http' in x or '@' in x):continue
    out[k]=x[:1400] if isinstance(x,str) else x
   elif isinstance(x,(dict,list)):
    y=scrub(x)
    if y:out[k]=y
  return out
 if isinstance(v,list):return [y for x in v if (y:=scrub(x))]
 return None
for col in ['materials','productDB','shoppingLists','shoppingItems','tasks','invoices','invoiceItems']:
 docs=read(col);matches=0
 for d in docs:
  row={k:catalog.decode(v) for k,v in d.get('fields',{}).items()};values=list(strings(row))
  exact=d['name'].split('/')[-1] in targets or any(x in targets for x in values)
  matched=[t for t in terms if any(t in x.lower() for x in values)]
  if exact or matched:
   matches+=1
   print('IDENTITY_EVIDENCE',json.dumps({'collection':col,'id':d['name'].split('/')[-1],'exactLink':exact,'matchedTerms':matched,'fieldNames':sorted(row),'data':scrub(row)},ensure_ascii=False))
 print('IDENTITY_COLLECTION',json.dumps({'collection':col,'count':len(docs),'matches':matches}))
