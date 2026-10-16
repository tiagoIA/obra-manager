# Company signup release requirements

Scope: synthetic CFC Electric and PNV Electric accounts in local Firebase emulators.
No production company onboarding, employee migration or real data import is authorized
by passing these checks alone. The user authorized a separate staging deployment;
the current service account received HTTP 403 PERMISSION_DENIED on project creation.

## Implemented in this pilot

- Company creation, owner membership and private lookup are provisioned atomically
  by a trusted function. Repeated registration returns the same company.
- Company membership and the private lookup cannot be written by clients.
- Invitations derive their company from the authenticated owner's membership;
  the browser cannot choose a company or grant owner privileges.
- Invitation links contain a random 256-bit token in the URL fragment. Only its
  SHA-256 hash is stored. No token, credential or request body is logged.
- Acceptance requires the invited verified email, expires after seven days,
  checks that the inviter is still an owner, and atomically creates membership.
- Acceptance retries are idempotent; another company's existing account is rejected.
- Owners can revoke pending invitations. Revocation is not employee removal.
- Browser account changes clear company name, role, invitation links and workspace.
- Only names, authentication email and company identity are used in signup. No
  Social Security numbers, financial account numbers or identity documents are collected.

## Required before commercial release

- Provision the separately authorized staging project and verify complete hosted flows.
- Adapt every operational query, listener, export and offline queue in the existing
  application to the company scope. Preserve current company records during migration.
- Define job-specific access for employee/supervisor roles: current pilot data rules
  isolate companies but do not implement all within-company operational permissions.
- Complete authenticated private photo delivery. Existing download tokens are a
  separate release blocker; Storage SDK rules tests do not validate bearer URLs.
- Implement removal of employees and revocation of their company access.
- Configure administrator MFA, appropriate abuse controls, monitoring and alerts.
- Define retention, deletion/export requests, backup restoration and incident handling.
- Inventory location collection in the existing application and provide clear notice,
  purpose, permitted access and collection limits before enabling it for new companies.
- Review privacy notice, company processing terms, subprocessors and applicable state
  laws with counsel. Determine whether Massachusetts 201 CMR 17 and its WISP duty
  apply to the actual data collected. A privacy checkbox or Firebase hosting alone
  does not establish compliance.

## Official references reviewed on 2026-10-16

- https://www.mass.gov/regulations/201-CMR-1700-standards-for-the-protection-of-personal-information-of-ma-residents
- https://www.mass.gov/info-details/obligations-under-the-data-security-regulations-and-breach-notification-law
- https://www.ftc.gov/business-guidance/resources/start-security-guide-business
- https://www.oag.ca.gov/privacy/ccpa

These are engineering release requirements, not a certification or legal opinion.
