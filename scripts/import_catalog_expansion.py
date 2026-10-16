"""Create validated source-identified products; never modify existing records."""
import collections
import gzip
import hashlib
import json
import os
import pathlib
import re
from urllib.parse import urlsplit


def norm(value):
    return re.sub('[^a-z0-9]', '', str(value or '').lower())


def identity(row):
    brand, part = norm(row.get('brand')), norm(row.get('manufacturerPart') or row.get('model'))
    if not brand or not part or any(c in row.get('brand', '') for c in ',;'):
        return ''
    if brand in ('unbranded','unknown','generic','multiple') or part in ('wire','na','nocat','emtx','pvc'):
        return ''
    return 'mpn:'+brand+':'+part


def active(row):
    return not row.get('isTask') and row.get('active') is not False and row.get('status') != 'inactive'


def validate(row):
    key = identity(row)
    expected = 'catalog-'+hashlib.sha256(key.encode()).hexdigest()[:24]
    if not key or row.get('identity') != key or row.get('id') != expected:
        raise ValueError('Candidate identity mismatch')
    if not row.get('name') or not row.get('description') or not row.get('unit'):
        raise ValueError('Incomplete native product record')
    if row.get('cat') != 'eletrica' or row.get('recordType') != 'product':
        raise ValueError('Unexpected product category or record type')
    if urlsplit(row.get('sourceUrl','')).hostname != 'www.homedepot.com':
        raise ValueError('Unexpected source')
    if not urlsplit(row['sourceUrl']).path.startswith('/p/'):
        raise ValueError('Expected exact product page')
    photos = row.get('photoUrls', [])
    if not 1 <= len(photos) <= 2 or row.get('photoUrl') != photos[0]:
        raise ValueError('Expected primary photo and at most one optional photo')
    for url in photos:
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname != 'images.thdstatic.com':
            raise ValueError('Unexpected supplier image source')
    if not row.get('suppliers'):
        raise ValueError('Missing source supplier reference')
    for supplier in row['suppliers']:
        if supplier.get('name') != 'Home Depot' or not supplier.get('internetId'):
            raise ValueError('Missing exact retailer identity')
        if supplier.get('unit') != row['unit'] or supplier.get('price') != '':
            raise ValueError('Package or price data changed')
    return key


def main():
    import firebase_admin
    from firebase_admin import credentials, firestore
    path = pathlib.Path('catalog-expansion/prepared-products.json.gz')
    manifest = json.loads(pathlib.Path('catalog-expansion/import-manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError('Candidate file digest mismatch')
    data = json.loads(gzip.decompress(path.read_bytes()))
    candidates = data['materials']
    keys = [validate(row) for row in candidates]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate candidate manufacturer identity')
    key = json.loads(os.environ['FIREBASE_SA'])
    if key.get('project_id') != 'obra-manager-4ecc7':
        raise ValueError('Unexpected Firebase project')
    firebase_admin.initialize_app(credentials.Certificate(key))
    db = firestore.client()
    def read():
        return {doc.id:doc.to_dict() for doc in db.collection('materials').stream()}
    before = read()
    known = {identity(row) for row in before.values() if identity(row)}
    known_skus = {row.get('sku') for row in before.values() if row.get('sku')}
    exact_before = sum(active(row) and row.get('recordType') != 'family' and bool(identity(row)) for row in before.values())
    remaining = max(0, int(manifest['minimumExactProducts'])-exact_before)
    limit = int(os.environ.get('IMPORT_LIMIT','0'))
    if limit:
        remaining = min(remaining, limit)
    planned, skipped = [], []
    for candidate in candidates:
        if len(planned) >= remaining:
            break
        key = candidate['identity']
        if key in known or candidate['id'] in before or candidate['sku'] in known_skus:
            skipped.append(candidate['id'])
            continue
        planned.append(candidate)
        known.add(key)
        known_skus.add(candidate['sku'])
    # Create-only batches abort on a conflicting existing ID; no overwrite path.
    created = []
    for offset in range(0, len(planned), 100):
        batch = db.batch()
        part = planned[offset:offset+100]
        for candidate in part:
            body = {k:v for k,v in candidate.items() if k not in ('id','identity')}
            body.update(createdAt=firestore.SERVER_TIMESTAMP,updatedAt=firestore.SERVER_TIMESTAMP)
            batch.create(db.collection('materials').document(candidate['id']),body)
        batch.commit()
        created.extend(candidate['id'] for candidate in part)
        pathlib.Path('catalog-import-created-ids.json').write_text(json.dumps(created))
        print(json.dumps({'createdSoFar':len(created)}),flush=True)
    after = read()
    for candidate in planned:
        saved = after.get(candidate['id'], {})
        if identity(saved) != candidate['identity'] or saved.get('photoUrl') != candidate['photoUrl']:
            raise ValueError('Saved product verification failed')
    exact_after = sum(active(row) and row.get('recordType') != 'family' and bool(identity(row)) for row in after.values())
    report = {'created':len(created),'createdIds':created,'duplicatesSkipped':len(skipped),
              'beforeExactProducts':exact_before,'afterExactProducts':exact_after,
              'activeRecords':sum(active(row) for row in after.values()),
              'activeNamedProducts':sum(active(row) and row.get('recordType') != 'family' for row in after.values()),
              'target':manifest['minimumExactProducts'],'targetMet':exact_after >= manifest['minimumExactProducts'],
              'existingRecordsUpdated':0,'existingRecordsDeleted':0,
              'createdFamilies':dict(collections.Counter(row['catalogFamily'] for row in planned))}
    pathlib.Path('catalog-import-result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='createdIds'}))


if __name__ == '__main__':
    main()
