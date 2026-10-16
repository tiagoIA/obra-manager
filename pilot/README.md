# Multi-company isolation groundwork

## Company registration pilot — 2026-10-16

The separate `site/` landing page links to its company registration form. It requires
email confirmation and calls the trusted `registerCompany` function to create the
company, owner membership and private user-to-company index in one transaction.
Duplicate/concurrent submissions return the same company. Clients cannot choose a
company ID or grant roles. The test workspace reads only its registered company.
The production application and landing page are unchanged. This is not published.

The host must be a separate Firebase project with an ID beginning
`obra-company-staging`. Both browser and backend reject the current production
project. Enable Email/Password authentication and the staging authorized domain,
install dependencies in `functions/`, and deploy from this directory using an
explicit staging project. A project with Functions deployment enabled is required.
Never use the current production project for this configuration: its rules default
to denying legacy global collections.

Run the additional registration integration test with the Firestore emulator:

```sh
npm --prefix functions install --ignore-scripts
npx firebase emulators:exec --project demo-obra-company-pilot --only firestore 'node test-registration.mjs'
```

CFC Electric and PNV Electric are the user-selected test companies. All company
records used for validation are synthetic. Test accounts use `.invalid` email addresses in emulator fixtures;
public contact details are never used as login credentials or recipients. No real
company data, account, project or email is created by the integration test.
The registration screen is a pilot shell. Employee invitation creation, acceptance
and revocation are implemented as trusted callables and a browser flow. Full app
integration, shared catalog policy and private media delivery remain release blockers.

## Invitations and browser checks — 2026-10-16

The owner generates an email-bound invitation link for an employee or supervisor.
The 256-bit token appears only in the link fragment; the backend stores its hash.
It expires after seven days and can be revoked. Acceptance requires the invited
verified email, checks that the inviter remains an owner, and atomically creates
membership. Existing accounts belonging to another company are rejected. Acceptance
retries are idempotent. No invitation email is sent automatically.

```sh
npx firebase emulators:exec --project demo-obra-company-pilot --only firestore 'node test-invitations.mjs'
npx firebase emulators:exec --project demo-obra-company-pilot --only auth,firestore,functions,hosting 'node ../scripts/check-company-signup.cjs'
```

The browser script uses Playwright (`npm install --no-save playwright` and
`npx playwright install chromium` in a suitable environment). Optional
`CHROMIUM_PATH` selects an installed browser. Optional `FIREBASE_SDK_CACHE` points to
unmodified Firebase 10.12.0 web SDK files for network-independent browser testing.
Local validation passed 33 invitation checks and 32 browser checks, in addition
to the earlier 23 registration and 28 company isolation checks. The local Functions
emulator transport was changed only in untracked dependencies from Unix sockets to
loopback TCP because the environment denies Unix socket listeners. Production code
was not changed for that transport limitation.

Staging access was checked through the existing GitHub Actions connection. It found
no active `obra-company-staging*` project, and attempting to create
`obra-company-staging-4ecc7` returned HTTP 403 `PERMISSION_DENIED`. No billing account
was attached. To publish, a Google Cloud/Firebase administrator must provision the
isolated project and grant this deployment integration appropriate access in it.
Functions deployment also requires billing configuration; none was changed here.
See `SECURITY-RELEASE.md` for the remaining security and privacy release requirements.

This branch is not deployed and does not modify production data or production rules.
It is an emulator-only proof of the company path/membership model, not a usable multi-company release.

Pilot scope: CFC Electric with Arlington; PNV Electric initially empty. Fixture Arlington is synthetic, not an imported project.

Implemented and verified:
- Company-scoped document and file paths; records carry companyId.
- Trusted membership provisioning; clients cannot add or change memberships.
- Firestore and authenticated Storage access deny cross-company reads, lists, creates, updates and deletes.
- Company branding input in the photo report generator, including name fallback and Summary/Complete; rejects a company/project mismatch.
- Separate upload queue keys by company and user (helper only; current application queue not yet adapted).

Run from this directory:

```sh
npm ci --ignore-scripts
npx firebase emulators:exec --project demo-obra-company-pilot --only firestore,storage 'node test-isolation.mjs'
```

Run report checks from repository root:

```sh
node --experimental-vm-modules scripts/check-company-brand.cjs
node --experimental-vm-modules scripts/check-photo-report.cjs
```

Verified locally on 2026-10-13: 28 isolation/helper checks plus both report checks passed.

Release blockers:
1. Adapt all existing application data calls, listeners and offline queues to the company scope. Clear state/listeners on account changes.
2. Add actual company onboarding/settings/logo upload UI and trusted owner/member provisioning.
3. Replace bearer-token media URLs with authenticated private media delivery. Storage SDK authorization tests passed, but token URLs are not proof of isolated delivery. The emulator did not reject a supplied reserved token metadata field; do not rely on that rule condition.
4. Import an authorized test copy of actual Arlington with IDs and relationships preserved, validate photos and reports, and keep PNV empty.
5. Provision a separate hosted staging environment and test full signup/logout/company access flows before any real company usage.

Existing app.html remains connected to production and unmodified. New scope helpers and branding input are not wired into its runtime. No company has been registered in production by this work.
