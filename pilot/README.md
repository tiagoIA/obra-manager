# Multi-company isolation groundwork

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
