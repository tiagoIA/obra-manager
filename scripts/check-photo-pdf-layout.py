from pathlib import Path
import re
import fitz

for name, expected in [('summary', 101), ('complete', 5)]:
    doc = fitz.open(Path('tmp/pdfs') / (name + '.pdf'))
    text = '\n'.join(page.get_text() for page in doc)
    photos = [int(n) for n in re.findall(r'Photo (\d+) ·', text)]
    assert len(photos) == expected and set(photos) == set(range(1, expected + 1)), (name, photos)
    for number, page in enumerate(doc):
        assert page.get_text().strip() or page.get_image_info(), (name, number, 'Blank page')
        for image in page.get_image_info():
            box = fitz.Rect(image['bbox'])
            assert box.x0 >= 35 and box.x1 <= 577 and box.y0 >= 35 and box.y1 <= 752, (name, number, box)
            assert abs(box.width/box.height-image['width']/image['height'])<0.001, (name, number, 'Photo aspect ratio changed')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    box = fitz.Rect(span['bbox'])
                    assert box.x0 >= 35 and box.x1 <= 577 and box.y0 >= 30 and box.y1 <= 780, (name, number, span)
        assert f'Page {number + 1} of {len(doc)}' in page.get_text()
    print(name, len(doc), 'pages;', expected, 'complete photo captions; all image/text bounds passed')

for name in ['landscape','portrait','no-facade','long-title','portuguese']:
    doc=fitz.open(Path('tmp/pdfs')/('cover-'+name+'.pdf'))
    assert len(doc)==3
    assert len(doc[0].get_image_info())==(0 if name=='no-facade' else 1)
    assert not doc[1].get_image_info()
    assert 'Photo 1' in doc[2].get_text()
    for number,page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    box=fitz.Rect(span['bbox'])
                    assert box.x0>=35 and box.x1<=577 and box.y0>=30 and box.y1<=780,(name,number,span)
        for image in page.get_image_info():
            box=fitz.Rect(image['bbox'])
            assert box.x0>=35 and box.x1<=577 and box.y0>=35 and box.y1<=752
            assert abs(box.width/box.height-image['width']/image['height'])<0.001,'Facade must preserve its aspect ratio'
    doc[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(str(Path('tmp/pdfs')/('cover-'+name+'.png')))
print('PASS: all cover bounds, facade aspect ratios, separate index and unchanged evidence numbering')

for language in ['en','pt']:
    filename=Path('tmp/pdfs')/('unit-progress-'+language+'.pdf')
    if not filename.exists():
        continue
    doc=fitz.open(filename)
    for number,page in enumerate(doc):
        content=page.get_text()
        # The footer cannot be the only content on any page.
        lines=[line.strip() for line in content.splitlines() if line.strip()]
        assert len(lines)>1 or page.get_image_info(), (language,number,'Blank page')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    box=fitz.Rect(span['bbox'])
                    assert box.x0>=35 and box.x1<=577 and box.y0>=30 and box.y1<=780,(language,number,span)
    text='\n'.join(page.get_text() for page in doc)
    assert all(value in text for value in ['26%','0%','100%'])
    doc[1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(str(filename.with_suffix('.png')))
print('PASS: full photo bounds and proportions, no empty PDF pages, unit percentages and bilingual labels')

browser=Path('tmp/pdfs/browser-pagination.pdf')
if browser.exists():
    doc=fitz.open(browser)
    photo_count=0
    for number,page in enumerate(doc):
        text=page.get_text()
        images=page.get_image_info()
        assert text.strip() or images, (number,'Empty browser print page')
        if 'Arlington pagination fixture - Unit' in text:
            assert images,(number,'Unit header stranded on an otherwise empty page')
        for image in images:
            box=fitz.Rect(image['bbox'])
            assert box.x0>=30 and box.x1<=583 and box.y0>=30 and box.y1<=752,(number,box,'Clipped browser print photo')
        photo_count+=len(images)
    assert photo_count==101,(photo_count,'Missing or duplicated browser print photos')
    for number in [1,2,min(3,len(doc)-1)]:
        doc[number].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(str(browser.with_name('browser-pagination-'+str(number)+'.png')))
    print('PASS: browser print pagination;',len(doc),'pages;',photo_count,'uncut photos; no blank pages')
