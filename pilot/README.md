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
The registration screen is a pilot shell. Full app integration, employee invitations,
shared catalog policy and private media delivery remain release blockers below.

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
