"""Read-only contact sheets for reviewed existing library photo references."""
import os,json,io,base64,hashlib,requests,concurrent.futures
from PIL import Image,ImageDraw
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from importlib.machinery import SourceFileLoader
catalog=SourceFileLoader('catalog','scripts/import-central.py').load_module()
key=json.loads(os.environ['FIREBASE_SA']);assert key['project_id']=='obra-manager-4ecc7'
s=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
fire='https://firestore.googleapis.com/v1/projects/obra-manager-4ecc7/databases/(default)/documents'
plans=json.load(open('photo-coverage-reuse-final-candidates.json'))
ids=list(dict.fromkeys(p['sourceMaterialId'] for p in plans))
def photo(ident):
 try:
  r=s.get(fire+'/materials/'+ident,timeout=40);r.raise_for_status();fields={k:catalog.decode(v) for k,v in r.json()['fields'].items()}
  expected=next(p['sourceExpectedName'] for p in plans if p['sourceMaterialId']==ident);assert fields['name']==expected
  url=fields['photoUrl'];assert isinstance(url,str)
  if url.startswith('data:image/'):raw=base64.b64decode(url.split(',',1)[1])
  else:
   assert url.startswith('https://');r=requests.get(url,timeout=40);r.raise_for_status();raw=r.content
  assert len(raw)<12000000
  im=Image.open(io.BytesIO(raw));im.load();assert min(im.size)>=80
  return {'id':ident,'name':fields['name'],'sourceSha256':hashlib.sha256(raw).hexdigest(),'image':im.convert('RGB')}
 except Exception as e:return {'id':ident,'error':type(e).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(photo,ids))
for start in range(0,len(rows),24):
 batch=rows[start:start+24];canvas=Image.new('RGB',(1200,((len(batch)+5)//6)*220),'white');draw=ImageDraw.Draw(canvas)
 for n,row in enumerate(batch):
  x=(n%6)*200;y=(n//6)*220
  if 'image' in row:
   im=row['image'].copy();im.thumbnail((190,165));canvas.paste(im,(x+(200-im.width)//2,y))
  draw.text((x+4,y+168),str(start+n)+' '+row['id'][:16],fill='black')
  label=row.get('name',row.get('error',''))
  draw.text((x+4,y+185),label[:27],fill='black');draw.text((x+4,y+202),label[27:54],fill='black')
 buf=io.BytesIO();canvas.save(buf,'PNG');print('PHOTO_CONTACT_SHEET',start,base64.b64encode(buf.getvalue()).decode())
for i,row in enumerate(rows):print('PHOTO_SOURCE_REVIEW',json.dumps({'index':i,**{k:v for k,v in row.items() if k!='image'}},ensure_ascii=False))
