import pathlib
src=pathlib.Path('scripts/collect-catalog.py').read_text()
src=src.replace("QUERIES=[", "ORIGINAL_QUERIES=[",1)
src=src.replace('http=requests.Session()', "QUERIES=[(q,f,u) for q,f,u in [('BR120','breakers',['panel','circuit']),('BR230','breakers',['panel','hvac']),('Q120','breakers',['panel','circuit']),('QO120','breakers',['panel','circuit']),('HOM120','breakers',['panel','circuit']),('GFTR2','devices',['devices']),('222-412','fittings',['devices','recessed']),('NM-B-12','wiring',['circuit']),('CAT6','datacom',['data'])]]\nhttp=requests.Session()")
src=src[:src.index('# A bounded manufacturer supplement')]+src[src.index('# Validate that every photo'):]
extra='''
for url in [
 'https://www.platt.com/p/0062408/nm-b-12-2-solid-copper-yellow/980100163051/122nmbgx250c',
 'https://www.platt.com/p/0013179/12-2-w-ground-mc-aluminum-armor-solid/980100347024/122mcagx250',
 'https://www.platt.com/p/0172550/14-2-nm-b-solid-copper-white-500/980100162993/142nmbgx500c',
]:
 try:
  html=get(url).text
  found=None
  for block in re.findall(r'<script[^>]*type="application/ld\\+json"[^>]*>(.*?)</script>',html,re.S):
   data=json.loads(block)
   for p in (data if isinstance(data,list) else [data]):
    if p.get('@type')=='Product':found=p
  if not found:continue
  p=found;brand=p.get('brand',{});brand=brand.get('name','') if isinstance(brand,dict) else brand
  image=p.get('image','');image=image[0] if isinstance(image,list) else image
  if isinstance(image,dict):image=image.get('url')
  code=str(p.get('productID') or url.split('/p/')[1].split('/')[0]);part=str(p.get('sku') or '')
  rows.append({'name':p['name'],'brand':brand or 'Multiple','manufacturerPart':'' if brand=='Multiple' else part,'upc':str(p.get('gtin12') or p.get('gtin13') or ''),'cat':'eletrica','family':'wiring','subcategory':'wiring','unit':'ft','packQuantity':250 if '250' in part else 500,'packUnit':'ft','specs':'Purchase length in feet; reference pack '+('250' if '250' in part else '500')+' ft. Confirm package before ordering.','guidedUses':['circuit','recessed'],'recordType':'product','source':'Platt Electric Supply','sourceUrl':url,'sourceVerifiedAt':'2026-10-08','photoSourceUrl':image,'suppliers':[{'name':'Platt Electric Supply','code':code,'catalogReference':part,'url':url,'unit':'ft','verifiedAt':'2026-10-08'}]})
 except Exception as e:print('PLATT_ERROR',url,type(e).__name__)
'''
src=src.replace('# Validate that every photo',extra+'\n# Validate that every photo')
exec(compile(src,'supplement','exec'))
