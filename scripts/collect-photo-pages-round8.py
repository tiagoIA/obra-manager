"""Read manufacturer product pages and brochure photos; never write application data."""
import json,requests,re,io,hashlib,base64,concurrent.futures
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
import fitz
def normalized(raw):
 im=Image.open(io.BytesIO(raw));im.load();assert min(im.size)>=80
 im=im.convert('RGB');im.thumbnail((1000,1000));b=io.BytesIO();im.save(b,'JPEG',quality=86);return b.getvalue()
def get(url):
 r=requests.get(url,timeout=45);r.raise_for_status();assert len(r.content)<40000000;return r
def collect(p):
 rows=[]
 try:
  r=get(p['url'])
  if p.get('pdf'):
   doc=fitz.open(stream=r.content,filetype='pdf');seen=set()
   for page in doc:
    if p['part'].lower() not in page.get_text().lower():continue
    for item in page.get_images(full=True):
     xref=item[0]
     if xref in seen:continue
     seen.add(xref)
     try:
      raw=normalized(doc.extract_image(xref)['image']);rows.append({'key':p['key'],'part':p['part'],'sourceUrl':p['url'],'photoSourceUrl':p['url'],'photoDocumentSha256':hashlib.sha256(r.content).hexdigest(),'photoImageXref':xref,'page':page.number+1,'raw':raw})
     except Exception:pass
    if rows:break
   return rows[:8]
  soup=BeautifulSoup(r.text,'html.parser');title=soup.find('h1');title=title.get_text(' ',strip=True) if title else soup.title.get_text() if soup.title else ''
  assert p['part'].lower().replace('-','') in soup.get_text().lower().replace('-','') or p['part'].lower() in r.text.lower()
  candidates=[]
  for img in soup.select('img'):
   src=img.get('data-src') or img.get('src') or ''
   alt=img.get('alt','')
   if p['part'].lower().replace('-','') in (alt+' '+src).lower().replace('-',''):candidates.append(urljoin(p['url'],src))
  for meta in soup.select('meta[property="og:image"]'):
   candidates.append(urljoin(p['url'],meta.get('content','')))
  for img in soup.select('main img'):
   src=img.get('data-src') or img.get('src') or ''
   if src and not re.search(r'logo|icon|banner',src,re.I):candidates.append(urljoin(p['url'],src))
  for url in list(dict.fromkeys(candidates))[:8]:
   try:
    raw=normalized(get(url).content);rows.append({'key':p['key'],'part':p['part'],'title':title,'sourceUrl':p['url'],'photoSourceUrl':url,'raw':raw})
   except Exception:pass
  return rows
 except Exception as e:
  print('MANUFACTURER_PHOTO_ERROR',p['key'],type(e).__name__);return []
pages=json.load(open('photo-source-pages-round8.json'))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=[r for group in pool.map(collect,pages) for r in group]
for n,row in enumerate(rows):row['photoSha256']=hashlib.sha256(row['raw']).hexdigest();row['index']=n
for start in range(0,len(rows),24):
 batch=rows[start:start+24];canvas=Image.new('RGB',(1200,((len(batch)+5)//6)*210),'white');draw=ImageDraw.Draw(canvas)
 for j,row in enumerate(batch):
  im=Image.open(io.BytesIO(row['raw']));im.thumbnail((190,165));x=(j%6)*200;y=(j//6)*210;canvas.paste(im,(x+(200-im.width)//2,y))
  draw.text((x+4,y+167),str(row['index'])+' '+row['key'],fill='black')
  draw.text((x+4,y+185),row['part']+' page '+str(row.get('page','')),fill='black')
 b=io.BytesIO();canvas.save(b,'PNG');print('MANUFACTURER_PHOTO_SHEET',start,base64.b64encode(b.getvalue()).decode())
for row in rows:print('MANUFACTURER_PHOTO_CANDIDATE',json.dumps({k:v for k,v in row.items() if k!='raw'},ensure_ascii=False))
print('MANUFACTURER_PHOTO_COUNT',len(rows))
