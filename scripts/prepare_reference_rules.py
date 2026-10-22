from pathlib import Path
source=Path('reference-audit/firestore.rules').read_text()
fragment=Path('scripts/installation-reference.rules').read_text()
marker='    match /{document=**} { allow read, write: if false; }'
if fragment in source: target=source
else:
 if '/installationReferences/' in source or source.count(marker)!=1: raise SystemExit('Unexpected rules layout')
 target=source.replace(marker,fragment+marker)
Path('hosting-test').mkdir(exist_ok=True)
Path('hosting-test/reference-firestore.rules').write_text(target)
