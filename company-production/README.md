# Company workspace on existing project

Authorized 2026-10-17: use existing obra-manager-4ecc7 Blaze project for company testing instead of adding billing to obra-manager-teste.

Backend deployment attempt: run 39049368469 stopped before deployment because firebase-adminsdk-fbsvc@obra-manager-4ecc7.iam.gserviceaccount.com lacks iam.serviceAccounts.ActAs on obra-manager-4ecc7@appspot.gserviceaccount.com. Narrow fix: Service Account User on that runtime service account. Other required deployment permissions have not yet been confirmed.

Production company data rules and legacy app boundary are candidates only; not released. New companies must never be given the legacy any-authenticated-user access. rules-test.mjs verifies this boundary, including pending signup accounts, Storage and accidental legacy profiles.

site/ contains the prepared separate /companies/ workspace. Do not copy pilot hosting config to production, replace the existing landing, or restore app.html from this old branch. Before exposing signup: verify production rule baselines, run boundary tests, release Firestore/Storage rules with rollback references, deploy verified functions, clone current Hosting and add only /companies/*, verify bytes and live signup. No existing company migration or data import is authorized merely for testing.

Only own-company project creation/edit/archive and invitations are implemented here. Operational tasks, schedules, purchases, time, Estimates and media migration into the company scope remain pending. Existing users remain in their current workspace; existing user profiles are prevented from self-registering a new company.
