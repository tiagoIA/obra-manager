"""Read public Home Depot category pages and stage exact source records.

No logins, private endpoints, inferred compatibility, or live writes. HTTP
failures are recorded without retries. Only source-supplied models are kept.
"""
import argparse
import concurrent.futures
import datetime
import html
import json
import pathlib
import re
import time
import urllib.request

CATEGORIES = {
    'cable': 'Electrical-Wire/N-5yc1vZbm7v',
    'conduit': 'Electrical-Electrical-Boxes-Conduit-Fittings-Conduit/N-5yc1vZbohl',
    'fittings': 'Electrical-Electrical-Boxes-Conduit-Fittings-Conduit-Fittings/N-5yc1vZbohk',
    'boxes': 'Electrical-Electrical-Boxes-Conduit-Fittings-Boxes-Brackets/N-5yc1vZbohn',
    'weatherproof': 'Electrical-Electrical-Boxes-Conduit-Fittings-Weatherproof-Boxes/N-5yc1vZca29',
    'covers': 'Electrical-Electrical-Boxes-Conduit-Fittings-Covers/N-5yc1vZbohm',
    'breakers': 'Electrical-Power-Distribution-Electrical-Panels-Protective-Devices-Circuit-Breakers/N-5yc1vZbm16',
    'panels': 'Electrical-Power-Distribution-Electrical-Panels-Protective-Devices-Breaker-Boxes/N-5yc1vZbm2w',
    'disconnects': 'Electrical-Power-Distribution-Temporary-Power-Disconnects-Safety-Switches/N-5yc1vZbtvq',
    'devices': 'Electrical-Wiring-Devices-Light-Controls/N-5yc1vZc34h',
    'receptacles': 'Electrical-Wiring-Devices-Light-Controls-Electrical-Outlets-Receptacles/N-5yc1vZc33a',
    'switches': 'Electrical-Wiring-Devices-Light-Controls-Light-Switches/N-5yc1vZc33w',
    'dimmers': 'Electrical-Wiring-Devices-Light-Controls-Dimmers/N-5yc1vZc34i',
    'grounding': 'Electrical-Power-Distribution-Electrical-Panels-Protective-Devices-Breaker-Box-Parts-Grounding-Bars/N-5yc1vZbm0j',
    'recessed': 'Lighting-Recessed-Lighting/N-5yc1vZc7ni',
    'plates': 'Electrical-Wall-Plates/N-5yc1vZbm8m',
    'terminals': 'Electrical-Electrical-Tools-Wire-Conduit-Tools-Wire-Connectors-Wire-Terminals/N-5yc1vZbmco',
    'ties': 'Electrical-Electrical-Tools-Wire-Conduit-Tools-Cable-Zip-Ties/N-5yc1vZbm8e',
    'tape': 'Electrical-Electrical-Tools-Electrical-Tapes/N-5yc1vZbm4u',
}
FAMILY = {'weatherproof':'boxes','covers':'boxes','plates':'devices',
          'terminals':'fittings','ties':'supports','tape':'tools',
          'receptacles':'devices','switches':'devices','dimmers':'devices','recessed':'lighting'}


def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value or ''))).strip()


def extract(source, family, url):
    marker = re.search(r'window\.__APOLLO_STATE__\s*=\s*', source)
    if not marker:
        raise ValueError('Public product state not found')
    state, _ = json.JSONDecoder().raw_decode(source[marker.end():])
    grouped = {}
    for row in state.values():
        if isinstance(row, dict) and row.get('__typename') == 'BaseProduct' and row.get('itemId'):
            grouped.setdefault(row['itemId'], []).append(row)
    output = []
    for item_id, versions in grouped.items():
        exact = next((p for p in versions if p.get('identifiers', {}).get('brandName')
                      and p.get('identifiers', {}).get('modelNumber')), None)
        if not exact:
            continue
        ids = exact['identifiers']
        if not ids.get('canonicalUrl', '').startswith('/p/'):
            continue
        name = clean(ids.get('productLabel', ''))
        descriptions = [clean(p.get('details', {}).get('description', '')) for p in versions]
        images = []
        for version in [exact, *versions]:
            for image in version.get('media', {}).get('images', []):
                src = image.get('url', '').replace('<SIZE>', '600')
                if src.startswith('https://images.thdstatic.com/') and src not in images:
                    images.append(src)
        pricing = next((v for k, v in exact.items() if k.startswith('pricing') and isinstance(v, dict)), {})
        # "each" can refer to an entire package; never silently convert to pieces.
        source_unit = pricing.get('unitOfMeasure', '')
        pack = re.search(r'\b(\d+)\s*[- ](?:pack|piece|count)\b', name, re.I)
        package = {'packQuantity':int(pack[1]), 'packUnit':'ea'} if pack else {}
        unit = 'pack' if pack else ('ea' if source_unit == 'each' else source_unit)
        attrs = {}
        size = re.search(r'\b(\d+(?:[ -]\d+/\d+)?|\d+/\d+|\d*\.\d+)\s*in\b', name, re.I)
        length = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:ft\.?|feet)\b', name, re.I)
        amps = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:amp|a)\b', name, re.I)
        if size and FAMILY.get(family, family) in ('conduit','fittings'):
            attrs['tradeSize'] = size[1]
        if length:
            attrs['length'] = length[1] + ' ft'
        if amps and family in ('breakers','panels','disconnects','devices'):
            attrs['amperage'] = amps[1]
        configuration = re.search(r'\b(\d{1,2})\s*[/\-]\s*([234])\b', name)
        if family == 'cable' and configuration:
            attrs.update(wireGauge=configuration[1], cableConfiguration=configuration[1]+'/'+configuration[2])
        brand, model = clean(ids['brandName']), clean(ids['modelNumber'])
        output.append({
            'candidateId':'homedepot-'+item_id, 'name':name, 'brand':brand,
            'manufacturerPart':model, 'description':max(descriptions, key=len) or name,
            'cat':'eletrica', 'catalogFamily':FAMILY.get(family, family), 'recordType':'product',
            'unit':unit, **package, **attrs,
            'photoUrl':images[0] if images else '', 'photoReferences':[
                {'url':src,'status':'needs-review','variantLinked':True} for src in images[:2]],
            'supplier':'Home Depot','storeCode':ids.get('storeSkuNumber') or '',
            'internetId':item_id, 'url':'https://www.homedepot.com'+ids['canonicalUrl'],
            'sourceCategoryUrl':url, 'sourcePurchaseUnit':source_unit,
            'price':None, 'currency':'USD',
            'date':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
            'status':'needs-review', 'source':'Public Home Depot category product data',
            'reviewIssues':['Verify exact package, unit and specifications before import'],
        })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', type=int, default=12)
    parser.add_argument('--output', required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--families', default='')
    parser.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    destination = pathlib.Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)
    selected = set(args.families.split(',')) if args.families else set(CATEGORIES)
    jobs = [(family, page, 'https://www.homedepot.com/b/'+path+'?Nao='+str(page*24+args.offset))
            for family, path in CATEGORIES.items() if family in selected for page in range(args.pages)]

    def collect(job):
        family, page, url = job
        file = destination / (family+'-'+str(page)+'.json')
        if file.exists():
            return json.loads(file.read_text())
        result = {'family':family,'page':page,'url':url,'candidates':[]}
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0', 'Accept':'text/html'})
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError('Page size limit exceeded')
            result['candidates'] = extract(data.decode('utf-8'), family, url)
            result['status'] = 'collected' if result['candidates'] else 'empty'
        except Exception as error:
            result.update(status='unavailable', reason=type(error).__name__)
        file.write_text(json.dumps(result, ensure_ascii=False))
        print(json.dumps({'family':family,'page':page,'count':len(result['candidates']),
                          'status':result['status']}), flush=True)
        time.sleep(.4)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(collect, jobs))
    unique = {}
    for result in results:
        for row in result['candidates']:
            unique.setdefault(row['internetId'], row)
    candidates = list(unique.values())
    report = {'status':'staged-only','liveWrites':0,'pagesChecked':len(results),
              'unavailablePages':sum(r['status']=='unavailable' for r in results),
              'candidateCount':len(candidates),'candidates':candidates}
    (destination/'candidates.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'}), flush=True)


if __name__ == '__main__':
    main()
