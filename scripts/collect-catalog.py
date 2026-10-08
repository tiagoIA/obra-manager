"""Read public distributor/manufacturer product feeds; never import prices or account data."""
import requests,json,re,io,base64,concurrent.futures,pathlib,collections,hashlib,time
from PIL import Image,ImageDraw
out=pathlib.Path('catalog-stage');out.mkdir(exist_ok=True)
QUERIES=[('NM-B','wiring',['circuit']),('MC','wiring',['circuit','recessed']),('THHN','wiring',['service','subpanel','circuit','hvac','ev']),('THWN','wiring',['circuit','hvac','ev']),('EMT','conduit',['circuit','hvac','ev']),('connector','fittings',['circuit','hvac','ev']),('PVC','conduit',['service','circuit']),('RACO','boxes',['devices','circuit','recessed']),('Carlon','boxes',['devices','recessed']),('receptacle','devices',['devices','circuit']),('GFCI','devices',['devices','circuit']),('switch','devices',['devices']),('wallplate','devices',['devices']),('loadcenter','breakers',['panel','subpanel']),('Eaton','breakers',['panel','circuit','hvac','ev']),('Siemens','breakers',['panel','circuit','hvac','ev']),('grounding','grounding',['service','panel']),('wireconnector','fittings',['devices','circuit','recessed']),('strut','accessories',['service','circuit']),('recessed','lighting',['recessed','led']),('LED','lighting',['led']),('emergency','lighting',['led']),('disconnect','devices',['hvac','circuit']),('charger','devices',['ev']),('CAT6','datacom',['data']),('smoke','detectors',['fire']),('FPLP','wiring',['fire']),('solar','solar',['solar'])]
http=requests.Session();http.headers['User-Agent']='ObraManager-Catalog/1.0 product reference research'
def get(url,**kw):
 r=http.get(url,timeout=35,**kw);r.raise_for_status();return r
rows=[];errors=[];seen=set()
for query,sub,uses in QUERIES:
 try:
  data=get('https://www.ew-ne.com/api/catalog_system/pub/products/search',params={'ft':query,'_from':0,'_to':9}).json();assert isinstance(data,list)
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
   if added>=6:break
  print('FEED_QUERY',query,'selected',added)
 except Exception as e:errors.append({'query':query,'error':type(e).__name__});print('FEED_ERROR',query,type(e).__name__,str(e)[:250])
# A bounded manufacturer supplement: specific wiring devices and controls, with SKU and variant photo.
try:
 data=get('https://store.leviton.com/products.json?limit=250').json()
 selected=0
 for p in sorted(data.get('products',[]),key=lambda p:(not bool(re.search(r'white|residential|gfci',p['title'],re.I)),p['title'])):
  if not re.search(r'receptacle|outlet|switch|wallplate|dimmer|charger|jack',p['title'],re.I):continue
  if re.search(r'kit|pack|bundle|box of|discontinued',p['title'],re.I):continue
  vs=p.get('variants') or []
  # Single-variant product avoids assigning one color's photo to another color.
  if len(vs)!=1 or not vs[0].get('sku') or not p.get('images'):continue
  v=vs[0];image=(v.get('featured_image') or p['images'][0]).get('src');link='https://store.leviton.com/products/'+p['handle']
  uses=['ev'] if re.search('charger',p['title'],re.I) else ['devices'];family='datacom' if re.search('jack',p['title'],re.I) else 'devices'
  rows.append({'name':p['title'],'brand':p['vendor'],'manufacturerPart':v['sku'],'upc':str(v.get('barcode') or ''),'cat':'eletrica','subcategory':'devices','family':family,'unit':'un','specs':'','guidedUses':uses,'recordType':'product','source':'Leviton Store','sourceUrl':link,'sourceVerifiedAt':'2026-10-08','photoSourceUrl':image,'suppliers':[{'name':'Leviton Store','code':v['sku'],'url':link,'unit':'un','verifiedAt':'2026-10-08'}]});selected+=1
  if selected>=24:break
 print('MANUFACTURER_SELECTED',selected)
except Exception as e:errors.append({'source':'Leviton','error':type(e).__name__})
# Validate that every photo is an actual raster; keep stable bytes for later upload.
def photo(pair):
 n,p=pair
 try:
  r=get(p['photoSourceUrl']);assert len(r.content)<12_000_000
  im=Image.open(io.BytesIO(r.content));im.load();assert min(im.size)>=80
  im=im.convert('RGB');im.thumbnail((1000,1000));buf=io.BytesIO();im.save(buf,'JPEG',quality=86)
  payload=buf.getvalue();path=out/(str(n)+'.jpg');path.write_bytes(payload);p['photoSha256']=hashlib.sha256(payload).hexdigest();p['_image']=str(path)
  return p
 except Exception as e:print('PHOTO_REJECT',p['name'][:70],type(e).__name__);return None
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:valid=[p for p in pool.map(photo,enumerate(rows)) if p]
for start in range(0,len(valid),40):
 batch=valid[start:start+40];canvas=Image.new('RGB',(1000,((len(batch)+7)//8)*160),'white');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(batch):
  im=Image.open(p['_image']);im.thumbnail((110,110));x=(j%8)*125;y=(j//8)*160;canvas.paste(im,(x+(125-im.width)//2,y));draw.text((x+3,y+112),str(start+j)+' '+p['manufacturerPart'][:17],fill='black');draw.text((x+3,y+130),p['family'][:18],fill='black')
 buf=io.BytesIO();canvas.save(buf,'PNG');print('CATALOG_CONTACT_SHEET',start,base64.b64encode(buf.getvalue()).decode())
for p in valid:print('STAGED_PRODUCT',json.dumps({k:v for k,v in p.items() if k!='_image'},ensure_ascii=False))
(out/'products.json').write_text(json.dumps(valid,ensure_ascii=False,indent=2));print('STAGED_SUMMARY',json.dumps({'count':len(valid),'families':dict(collections.Counter(p['family'] for p in valid)),'sources':dict(collections.Counter(p['source'] for p in valid)),'errors':errors}))
