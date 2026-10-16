# Local consumption baseline — 2026-10-16

Validated with `test-consumption.mjs` against the local Firestore emulator.
These counts describe calls made by the application, not billable cloud metrics.
One transaction attempt per operation was observed; retries increase requests.

| Successful server operation | Document read requests | Document write requests |
| --- | ---: | ---: |
| Register a new company | 1 | 3 |
| Repeat company registration | 1 | 0 |
| Create an invitation | 3 | 1 |
| Accept an invitation | 5 | 3 |
| Repeat accepted invitation | 4 | 0 |
| Revoke an invitation | 2 | 1 |

For C new companies and I invitations created and accepted once, the code executes
C + 2I callable operations, C + 8I document read requests, and 3C + 4I document
write requests. Example only: 5 companies and 50 accepted invitations imply
105 callable operations, 405 read requests and 215 write requests on the server.
This is an onboarding scenario, not a forecast of monthly customer activity.

Excluded: client-side reads, Security Rules dependent reads, Auth/email usage,
transaction retries, unsuccessful requests, compute time, network bytes, build
minutes, artifact storage, photos and all existing application screens. The frontend
also reads membership and company documents when restoring account state.
An emulator's elapsed time must not be used as a production compute price.

Before estimating a commercial subscription, measure actual invocations, allocated
CPU/memory and billed execution time, retries, errors, Firestore usage, storage bytes
and downloads in the isolated hosted project. Record activity volume and date range
alongside every estimate. Review current regional prices, free-tier eligibility and
shared billing-account quotas. Budget alerts are notifications, not a hard spending cap.
No billing was enabled and no cloud-cost measurement was performed here.

Official references checked on 2026-10-16:
- https://firebase.google.com/pricing
- https://firebase.google.com/docs/functions/get-started

## Reproduce

Use Node 22 and Java 17 with the committed Firebase CLI version:

```sh
cd pilot
npm ci --ignore-scripts
npm --prefix functions ci --ignore-scripts
npx firebase emulators:exec --project demo-obra-company-pilot --only firestore 'node test-registration.mjs && node test-invitations.mjs && node test-consumption.mjs'
```

The measurement script requires a loopback emulator host and uses only synthetic
accounts in `demo-obra-company-pilot`. It resets that emulator's fixtures before its
scenarios. Run sequentially with the other tests, never against a live database.

## Hosted environment status

Firebase project `obra-manager-teste` was created on the free Spark plan. Auth,
Firestore, callable functions and the pilot Hosting release have not been configured
or deployed. The existing pilot's browser/backend project guards still accept the
older `obra-company-staging*` naming convention, so they must explicitly allow this
new test project before a future deployment. Production must remain denied.
Cloud Functions publication and deployment permissions remain separate prerequisites.
