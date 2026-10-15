from pathlib import Path
import re,fitz
for name,expected in [('summary',101),('complete',5),('compact-regression',12)]:
 doc=fitz.open(Path('tmp/pdfs')/(name+'.pdf'));nums=[]
 for i,page in enumerate(doc):
  text=page.get_text();assert 'Invalid Date' not in text
  nums += [int(v) for v in re.findall(r'Photo (\d+) ·',text)]
  for image in page.get_image_info():
   b=fitz.Rect(image['bbox']);assert b.x0>=35 and b.x1<=577 and b.y0>=35 and b.y1<=752,(name,i,b)
   assert abs(b.width/b.height-image['width']/image['height'])<.001
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     b=fitz.Rect(span['bbox']);assert b.x0>=35 and b.x1<=577 and b.y0>=30 and b.y1<=780,(name,i,span)
 assert len(nums)==expected and nums==list(range(1,expected+1)),(name,nums)
 if name=='compact-regression':
  assert len(doc)==5 and len(doc[0].get_links())==2
  assert 'Contents' in doc[0].get_text()
  assert 'No photos recorded' in doc[1].get_text() and 'Basement task 7' in doc[1].get_text()
  assert 'Overall Installation - Final Photos' in doc[-1].get_text()
 print('PASS:',name,len(doc),'pages;',expected,'photos, text/image bounds, proportions and sequence verified')
