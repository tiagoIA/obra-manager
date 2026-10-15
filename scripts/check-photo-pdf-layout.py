from pathlib import Path
import re
import fitz

for name, expected in [('summary', 101), ('complete', 5)]:
    doc = fitz.open(Path('tmp/pdfs') / (name + '.pdf'))
    text = '\n'.join(page.get_text() for page in doc)
    photos = [int(n) for n in re.findall(r'Photo (\d+) ·', text)]
    assert len(photos) == expected and set(photos) == set(range(1, expected + 1)), (name, photos)
    for number, page in enumerate(doc):
        for image in page.get_image_info():
            box = fitz.Rect(image['bbox'])
            assert box.x0 >= 35 and box.x1 <= 577 and box.y0 >= 35 and box.y1 <= 752, (name, number, box)
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    box = fitz.Rect(span['bbox'])
                    assert box.x0 >= 35 and box.x1 <= 577 and box.y0 >= 30 and box.y1 <= 780, (name, number, span)
        assert f'Page {number + 1} of {len(doc)}' in page.get_text()
    print(name, len(doc), 'pages;', expected, 'complete photo captions; all image/text bounds passed')
