"""Read-only Firebase staging discovery. Never prints credentials or changes a project."""
import json
import os
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

report = {"status": "blocked", "production_changed": False, "staging_projects": [], "blockers": []}
out = Path("company-pilot-results")
out.mkdir(exist_ok=True)

def save():
    (out / "staging-access.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)

raw = os.environ.get("FIREBASE_SA", "")
if not raw:
    report["blockers"].append("Firebase service-account connection is unavailable.")
    save()
    raise SystemExit(0)

key = json.loads(raw)
session = AuthorizedSession(service_account.Credentials.from_service_account_info(
    key, scopes=["https://www.googleapis.com/auth/cloud-platform"]))
url = "https://firebase.googleapis.com/v1beta1/projects"
token = None
projects = []
while True:
    params = {"pageSize": 100}
    if token:
        params["pageToken"] = token
    response = session.get(url, params=params, timeout=30)
    if not response.ok:
        report["blockers"].append(f"Firebase project discovery returned HTTP {response.status_code}.")
        break
    data = response.json()
    projects.extend(data.get("results", []))
    token = data.get("nextPageToken")
    if not token:
        break

for project in projects:
    project_id = project.get("projectId", "")
    if not project_id.startswith("obra-company-staging") or project.get("state") != "ACTIVE":
        continue
    item = {"project_id": project_id}
    # Presence of a project does not establish permission to deploy Functions.
    apis = {
        "hosting": f"https://firebasehosting.googleapis.com/v1beta1/projects/{project_id}/sites",
        "firestore": f"https://firestore.googleapis.com/v1/projects/{project_id}/databases",
        "functions": f"https://cloudfunctions.googleapis.com/v2/projects/{project_id}/locations/us-central1/functions",
        "auth": f"https://identitytoolkit.googleapis.com/admin/v2/projects/{project_id}/config",
        "billing": f"https://cloudbilling.googleapis.com/v1/projects/{project_id}/billingInfo",
    }
    for name, endpoint in apis.items():
        result = session.get(endpoint, timeout=30)
        item[name + "_read_http"] = result.status_code
        if name == "billing" and result.ok:
            item["billing_enabled"] = bool(result.json().get("billingEnabled"))
        if name == "auth" and result.ok:
            provider = result.json().get("signIn", {}).get("email", {})
            item["email_password_enabled"] = bool(provider.get("enabled")) and bool(provider.get("passwordRequired"))
    report["staging_projects"].append(item)

if not report["staging_projects"]:
    report["blockers"].append("No active obra-company-staging project is visible to the connected service account.")
else:
    report["status"] = "project-found-deployment-not-yet-validated"
save()
