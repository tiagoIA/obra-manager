"""Convert the public Leviton store export to review candidates, never live materials.

Usage: python scripts/stage_manufacturer_catalog.py INPUT_DIRECTORY OUTPUT_FILE
SKU is a source identifier until reviewed as an MPN. Variant image associations
are preserved; a shared image is never claimed to verify a color or size.
"""
import datetime
import html
import json
import pathlib
import re
import sys


def text(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value or ''))).strip()


def stage(products):
    seen, candidates = set(), []
    for product in products:
        for variant in product.get('variants', []):
            sku = str(variant.get('sku') or '').strip()
            brand = str(product.get('vendor') or '').strip()
            identity = (brand.casefold(), sku.casefold()) if sku else ('source', str(variant['id']))
            if identity in seen:
                continue
            seen.add(identity)
            options = {option['name']: variant.get('option' + str(option['position']))
                       for option in product.get('options', []) if option['name'] != 'Title'}
            images = product.get('images', [])
            exact = [image for image in images if variant['id'] in image.get('variant_ids', [])]
            featured = variant.get('featured_image')
            image = featured if isinstance(featured, dict) else (exact or images or [{}])[0]
            photo_references = []
            photo_seen = set()
            for photo in [image, *exact, *images]:
                url = photo.get('src', '')
                if not url.startswith('https://') or url.split('?')[0] in photo_seen:
                    continue
                photo_seen.add(url.split('?')[0])
                associated = photo.get('variant_ids', [])
                # Never include an image explicitly assigned to a different variant.
                if associated and variant['id'] not in associated:
                    continue
                photo_references.append({'url': url, 'sourceImageId': str(photo.get('id', '')),
                                         'variantLinked': variant['id'] in associated,
                                         'status': 'needs-review'})
                if len(photo_references) == 2:
                    break
            title = text(product.get('title', ''))
            suffix = ', '.join(str(v) for v in options.values() if v and str(v).lower() not in title.lower())
            name = title + (' — ' + suffix if suffix else '')
            issues = ['Confirm purchase unit, package quantity and manufacturer part number',
                      'Confirm category and family against the product specification']
            if not sku:
                issues.append('Source SKU missing')
            if not image.get('src'):
                issues.append('Photo missing')
            elif len(product.get('variants', [])) > 1 and not featured and not exact:
                issues.append('Shared product image: exact variant appearance requires review')
            raw_price = variant.get('price')
            try:
                price = float(raw_price)
                if not 0 <= price < float('inf'):
                    price = None
            except (TypeError, ValueError):
                price = None
            candidates.append({
                'candidateId': 'leviton-' + str(variant['id']),
                'name': name, 'description': text(product.get('body_html', '')),
                'brand': brand, 'manufacturerPart': '', 'sourceSku': sku,
                'supplier': 'Leviton Store', 'storeCode': sku,
                'url': 'https://store.leviton.com/products/' + product['handle'] + '?variant=' + str(variant['id']),
                'photoUrl': photo_references[0]['url'] if photo_references else '',
                'photoReferences': photo_references, 'sourceOptions': options,
                'price': price, 'currency': 'USD', 'unit': '',
                'date': datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
                'status': 'needs-review', 'source': 'Official Leviton store product export',
                'sourceProductId': str(product['id']), 'sourceVariantId': str(variant['id']),
                'reviewIssues': issues,
            })
    return candidates


def main():
    root, destination = map(pathlib.Path, sys.argv[1:3])
    products = [product for filename in sorted(root.glob('leviton-*.json'))
                for product in json.loads(filename.read_text())]
    candidates = stage(products)
    result = {'status': 'staged-only', 'liveWrites': 0,
              'sourceProductCount': len({p['id'] for p in products}),
              'candidateCount': len(candidates),
              'missingSku': sum(not c['sourceSku'] for c in candidates),
              'missingPhoto': sum(not c['photoUrl'] for c in candidates),
              'withTwoPhotoReferences': sum(len(c['photoReferences']) == 2 for c in candidates),
              'candidates': candidates}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'candidates'}))


if __name__ == '__main__':
    main()
