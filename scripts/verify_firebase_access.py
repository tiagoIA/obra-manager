import json, os
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
key = json.loads(os.environ["FIREBASE_SA"])
project = key.get("project_id")
if project != "obra-manager-4ecc7":
    raise SystemExit("Credential belongs to another project; stopped")
session = AuthorizedSession(service_account.Credentials.from_service_account_info(key, scopes=["https://www.googleapis.com/auth/cloud-platform"]))
checks = {
 "hosting_read": f"https://firebasehosting.googleapis.com/v1beta1/projects/{project}/sites",
 "firestore_read": f"https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents:listCollectionIds",
 "storage_read": f"https://storage.googleapis.com/storage/v1/b/{project}.firebasestorage.app/o?maxResults=1",
 "rules_read": f"https://firebaserules.googleapis.com/v1/projects/{project}/releases?pageSize=1"
}
for name, url in checks.items():
    response = session.post(url, json={"pageSize":1}, timeout=30) if name == "firestore_read" else session.get(url, timeout=30)
    print(name, response.status_code)
response = session.post(f"https://cloudresourcemanager.googleapis.com/v1/projects/{project}:testIamPermissions", json={"permissions":["firebasehosting.versions.create","firebasehosting.releases.create","datastore.databases.export","firebaseauth.users.get","storage.objects.list","firebaserules.rulesets.get"]}, timeout=30)
print("permission_check",response.status_code)
if response.ok:
    print("granted_permissions",json.dumps(response.json().get("permissions",[])))
