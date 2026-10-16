"""Collect exact product-page references. Stage candidates; never apply prices/photos.
Use --request JSON --output JSON locally, or --firestore in the project workflow.
No AI key or model guesses. Retailer access failures remain unavailable.
"""
import argparse, concurrent.futures, datetime, json, os, re, urllib.request
from html.parser import HTMLParser
from urllib.parse import urlsplit
ALLOWED=('homedepot.com','lowes.com','grainger.com','supplyhouse.com','platt.com','gce.com','granitecityelectric.com','southwire.com','leviton.com','hubbell.com','atkore.com','eaton.com','legrand.com','kidde.com','rexelusa.com','graybar.com')
def safe_url(url):
 try:
  u=urlsplit(url)
  return u.scheme=='https' and not u.username and not u.password and u.port in (None,443) and any(u.hostname==h or u.hostname.endswith('.'+h) for h in ALLOWED)
 except (ValueError,AttributeError): return False
class Redirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if not safe_url(newurl): raise ValueError('Redirect outside approved supplier domains')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
class LDParser(HTMLParser):
 def __init__(self): super().__init__(); self.active=False; self.text=[]; self.objects=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('type','').split(';')[0]=='application/ld+json':self.active=True;self.text=[]
 def handle_data(self,data):
  if self.active:self.text.append(data)
 def handle_endtag(self,tag):
  if tag=='script' and self.active:
   try:self.objects.append(json.loads(''.join(self.text)))
   except ValueError:pass
   self.active=False

def products(value):
 if isinstance(value,list):
  for x in value:yield from products(x)
 elif isinstance(value,dict):
  types=value.get('@type',[]);types=types if isinstance(types,list) else [types]
  if any(str(t).rsplit('/',1)[-1]=='Product' for t in types):yield value
  for key in ('@graph','mainEntity','hasVariant','itemListElement','item'):
   if key in value:yield from products(value[key])
def norm(v):return re.sub('[^a-z0-9]','',str(v or '').lower())
def same_product(m,ref,p):
 brand=p.get('brand','');brand=brand.get('name','') if isinstance(brand,dict) else brand
 mpn=p.get('mpn','');part=m.get('manufacturerPart') or m.get('model')
 model=bool(part and m.get('brand') and norm(mpn)==norm(part) and norm(brand)==norm(m['brand']))
 codes={norm(x) for x in (ref.get('code'),ref.get('internetId'),*(ref.get('aliasCodes') or [])) if x}
 code=norm(p.get('sku')) in codes if p.get('sku') else False
 # If both sources provide a model or brand, disagreement blocks the candidate.
 if part and mpn and norm(part)!=norm(mpn):return False
 if m.get('brand') and brand and norm(m['brand'])!=norm(brand):return False
 return model or code

def collect_page(m,ref,html=None):
 url=ref.get('url','')
 if not safe_url(url):return {'materialId':m['id'],'status':'unavailable','reason':'No approved HTTPS product URL','candidates':[]}
 if html is None:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; ObraManagerProductReferences/1.0)','Accept':'text/html'})
  with urllib.request.build_opener(Redirects).open(req,timeout=18) as r:
   if not safe_url(r.url):raise ValueError('Unapproved source')
   raw=r.read(3_000_001)
   if len(raw)>3_000_000:raise ValueError('Product page too large')
   html=raw.decode('utf-8',errors='replace')
 parser=LDParser();parser.feed(html);result=[]
 for product in products(parser.objects):
  if not same_product(m,ref,product):continue
  offers=product.get('offers',[]);offers=offers if isinstance(offers,list) else [offers]
  # Aggregate/range prices are not exact purchase prices.
  exact=[o for o in offers if isinstance(o,dict) and o.get('price') is not None and o.get('priceCurrency')=='USD']
  prices={str(o['price']) for o in exact}
  price=None
  if len(prices)==1:
   try:
    value=float(next(iter(prices)))
    if value>=0 and value<float('inf'):price=value
   except ValueError:pass
  brand=product.get('brand','');brand=brand.get('name','') if isinstance(brand,dict) else brand
  image=product.get('image','');image=image[0] if isinstance(image,list) and image else image;image=image.get('url','') if isinstance(image,dict) else image
  if image and not safe_url(image):image=''
  result.append({'materialId':m['id'],'supplier':ref.get('name',''),'storeCode':ref.get('code') or ref.get('internetId') or product.get('sku',''),'brand':brand,'manufacturerPart':product.get('mpn',''),'url':url,'photoUrl':image,'price':price,'currency':'USD','unit':'','location':ref.get('location',''),'date':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),'status':'needs-review','source':'Product page JSON-LD','matchEvidence':'Exact registered model or store code; packaging requires review'})
 return {'materialId':m['id'],'status':'needs-review' if result else 'unavailable','reason':'' if result else 'No exact product identity and offer found','candidates':result}

def main():
 p=argparse.ArgumentParser();p.add_argument('--request');p.add_argument('--output',default='product-reference-candidates.json');p.add_argument('--firestore',action='store_true');p.add_argument('--limit',type=int,default=0);args=p.parse_args();db=None
 if args.firestore:
  import firebase_admin
  from firebase_admin import credentials,firestore
  key=json.loads(os.environ['FIREBASE_SA'])
  if key.get('project_id')!='obra-manager-4ecc7':raise ValueError('Unexpected project')
  firebase_admin.initialize_app(credentials.Certificate(key));db=firestore.client()
  rows=[dict(d.to_dict(),id=d.id) for d in db.collection('materials').stream()]
 else:
  raw=json.load(open(args.request));rows=raw['materials'] if isinstance(raw,dict) else raw
 rows=[m for m in rows if not m.get('isTask') and m.get('active') is not False and m.get('status')!='inactive' and m.get('recordType')!='family']
 jobs=[(m,r) for m in rows for r in m.get('suppliers',[]) if r.get('url') and r.get('matchVerified') is not False]
 if args.limit:jobs=jobs[:args.limit]
 def run(job):
  try:return collect_page(*job)
  except Exception as e:return {'materialId':job[0]['id'],'status':'unavailable','reason':type(e).__name__,'candidates':[]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(run,jobs))
 candidates=[c for r in results for c in r['candidates']]
 if db:
  by_id={}
  for r in results:by_id.setdefault(r['materialId'],[]).append(r)
  for mid,values in by_id.items():db.collection('materials').document(mid).update({'enrichmentCandidates':[c for r in values for c in r['candidates']],'enrichmentCheckedAt':datetime.datetime.now(datetime.timezone.utc),'enrichmentStatus':'needs-review' if any(r['candidates'] for r in values) else 'unavailable'})
 with open(args.output,'w') as f:json.dump({'candidates':candidates,'results':results},f,indent=2)
 print(json.dumps({'pagesChecked':len(results),'candidatesForReview':len(candidates),'unavailable':sum(r['status']=='unavailable' for r in results)}))
if __name__=='__main__':main()
