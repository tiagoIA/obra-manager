"""Read public distributor/manufacturer product feeds; never import prices or account data."""
import requests,json,re,io,base64,concurrent.futures,pathlib,collections,hashlib,time
from PIL import Image,ImageDraw
out=pathlib.Path('photo-coverage-stage');out.mkdir(exist_ok=True)
QUERIES=[["EMT connector","emt-connector",["reference"]],["EMT coupling","emt-coupling",["reference"]],["rigid conduit","rmc",["reference"]],["flexible metal conduit","fmc",["reference"]],["PVC conduit","pvc-pipe",["reference"]],["liquidtight connector","liquidtight-connector",["reference"]],["handy cover","handy-cover",["reference"]],["concrete screw","anchor",["reference"]],["threaded rod","rod",["reference"]],["HNF361","disconnect30",["reference"]],["HF362N","disconnect60",["reference"]],["R977L","pvc-strap",["reference"]],["R977LC","pvc-strap",["reference"]],["KOS","seal",["reference"]],["PVC 3/4","pvc",["reference"]],["THHN 12 black","thhn",["reference"]],["THHN 8","thhn",["reference"]],["NM-B 6/3","nmb",["reference"]],["NM-B 10/2","nmb",["reference"]],["SPEAKER","speaker",["reference"]],["632","screw",["reference"]],["COUPLING","coupling",["reference"]],["CONNECTOR","connector",["reference"]]]
http=requests.Session();http.headers['User-Agent']='ObraManager-Catalog/1.0 product reference research'
def get(url,**kw):
 r=http.get(url,timeout=35,**kw);r.raise_for_status();return r
rows=[];errors=[];seen=set()
for query,sub,uses in QUERIES:
 try:
  data=get('https://www.ew-ne.com/api/catalog_system/pub/products/search',params={'ft':query,'_from':0,'_to':29}).json();assert isinstance(data,list)
  added=0
  for p in data:
   if p.get('productId') in seen or str((p.get('Global_Disable') or ['false'])[0]).lower()=='true' or str((p.get('PFA Discontinued Flag') or ['false'])[0]).lower()=='true':continue
   if any('tools' in c.lower() for c in p.get('categories',[])):continue
   items=p.get('items') or [];it=items[0] if items else {};images=it.get('images') or []
   image=next((i.get('imageUrl') for i in images if i.get('imageUrl')),None)
   if not image:continue
   def v(k,default=''):return (p.get(k) or [default])[0]
   name=v('Short Description',p.get('productName',''));brand=next((str(x) for x in [p.get('brand'),v('Brand Name'),v('Manufacturer Name')] if x and not str(x).isdigit()),'');part=v('Manufacturer Part Number')
   unit=v('UOM','un').lower();unit={'ea':'un','each':'un','pc':'un','pcs':'un'}.get(unit,unit)
   cat='fire' if uses==['fire'] else 'eletrica';family=sub if cat!='fire' else ('detectors' if sub=='detectors' else 'wiring')
   facts={k:v(k) for k in ['Amperage Rating','Voltage Rating','Color','Material','Trade Size','Conductor Size','Number Of Poles','Wire Size','Size','Length'] if p.get(k)}
   link=p.get('link') or 'https://www.ew-ne.com/'+p['linkText']+'/p';code=str(v('Eclipse ID',p['productId']))
   row={'name':name,'brand':brand,'manufacturerPart':part,'upc':(str(it.get('ean') or '') if re.fullmatch(r'\d{12,14}',str(it.get('ean') or '')) else ''),'cat':cat,'subcategory':family,'family':sub,'unit':unit,'specs':'; '.join(k+': '+str(val) for k,val in facts.items()),'technicalAttributes':facts,'guidedUses':uses,'recordType':'product','source':'Electrical Wholesalers NE','sourceUrl':link,'sourceVerifiedAt':'2026-10-08','photoSourceUrl':image,'suppliers':[{'name':'Electrical Wholesalers NE','code':code,'url':link,'unit':unit,'verifiedAt':'2026-10-08'}]}
   rows.append(row);seen.add(p['productId']);added+=1
   if added>=3:break
  print('FEED_QUERY',query,'selected',added)
 except Exception as e:errors.append({'query':query,'error':type(e).__name__});print('FEED_ERROR',query,type(e).__name__,str(e)[:250])
# Validate that every photo is an actual raster; keep stable bytes for later upload.
def photo(pair):
 n,p=pair
 try:
  r=get(p['photoSourceUrl']);assert len(r.content)<12_000_000
  im=Image.open(io.BytesIO(r.content));im.load();assert min(im.size)>=80
  im=im.convert('RGB');im.thumbnail((1000,1000));buf=io.BytesIO();im.save(buf,'JPEG',quality=86)
  payload=buf.getvalue();path=out/(str(n)+'.jpg');path.write_bytes(payload);p['photoSha256']=hashlib.sha256(payload).hexdigest();assert p['photoSha256'] not in {'1809524679fdd7d0b46d13d0aa2edb5ef818e9d3a619961e4e5f64ccaae00c77','d7ec0494f7d7c73468a7d4b5ec117b351741ea2a300bed9dcd99e5abfb71e42d'};p['_image']=str(path)
  return p
 except Exception as e:print('PHOTO_REJECT',p['name'][:70],type(e).__name__);return None
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:valid=[p for p in pool.map(photo,enumerate(rows)) if p]
for start in range(0,len(valid),40):
 batch=valid[start:start+40];canvas=Image.new('RGB',(1000,((len(batch)+7)//8)*160),'white');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(batch):
  im=Image.open(p['_image']);im.thumbnail((110,110));x=(j%8)*125;y=(j//8)*160;canvas.paste(im,(x+(125-im.width)//2,y));draw.text((x+3,y+112),str(start+j)+' '+p['manufacturerPart'][:17],fill='black');draw.text((x+3,y+130),p['family'][:18],fill='black')
 buf=io.BytesIO();canvas.save(buf,'PNG');print('COVERAGE_CONTACT_SHEET',start,base64.b64encode(buf.getvalue()).decode())
for p in valid:print('COVERAGE_CANDIDATE',json.dumps({k:v for k,v in p.items() if k!='_image'},ensure_ascii=False))
(out/'products.json').write_text(json.dumps(valid,ensure_ascii=False,indent=2));print('COVERAGE_COLLECTION_SUMMARY',json.dumps({'count':len(valid),'families':dict(collections.Counter(p['family'] for p in valid)),'sources':dict(collections.Counter(p['source'] for p in valid)),'errors':errors}))
