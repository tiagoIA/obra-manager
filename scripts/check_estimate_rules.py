"""Read-only Firebase rule inventory. No deployment or customer data access."""
import json,os,re
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
key=json.loads(os.environ['FIREBASE_SA'])
assert key.get('project_id')=='obra-manager-4ecc7'
session=AuthorizedSession(service_account.Credentials.from_service_account_info(key,scopes=['https://www.googleapis.com/auth/cloud-platform']))
for release in ['cloud.firestore','firebase.storage/obra-manager-4ecc7.firebasestorage.app']:
 response=session.get('https://firebaserules.googleapis.com/v1/projects/obra-manager-4ecc7/releases/'+release,timeout=30)
 if not response.ok:
  print('RULE_ACCESS',release.split('/')[0],response.status_code);continue
 rule=session.get('https://firebaserules.googleapis.com/v1/'+response.json()['rulesetName'],timeout=30)
 if not rule.ok:
  print('RULESET_ACCESS',rule.status_code);continue
 # Rules source only; no document contents, customer data or credentials.
 for f in rule.json().get('source',{}).get('files',[]):
  content=f.get('content','')
  # Exclude hard-coded identifiers or literals from logs.
  safe=re.sub(r'([\'\"])(?:\\.|(?!\1).)*?\1',"'<literal>'",content)
  print('RULES',release.split('/')[0],safe)
