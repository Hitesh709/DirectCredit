# DirectCredit Task Status

## Tasks 1–12 — Foundation & Customer Authentication
**Status: COMPLETE (implementation committed; production deployment verification remains required where external access is unavailable)**

## Task 13 — New Customer Registration
**Status: COMPLETE**
- Canonical mobile-first registration with duplicate mobile/email protection.
- Persistent customer identity and signed mobile-direct session.

## Task 14 — Editable Personal Customer Profile
**Status: COMPLETE**
- Authenticated personal profile read/patch, own-customer authorization, partial updates and audit events.

## Task 15 — Employment / Business Profile
**Status: COMPLETE**
- Authenticated employment/business read/patch with non-negative financial validation and audit events.

## Task 16 — Customer Addresses & Residence Ownership
**Status: COMPLETE**
- Added canonical authenticated address/residence read and partial-update API.
- Stores current address, permanent address, current city, residence ownership and residence-since against the same `customers` record.
- Own-customer authorization and validation are enforced.
- Changes are audit logged.

## Task 17 — Residence / Address Proof Upload Metadata
**Status: COMPLETE**
- Added authenticated residence-proof submission endpoint using the canonical `documents` table.
- Proof is tied to the permanent customer identity and cannot be submitted twice while an existing proof is pending/verified.
- Requires core address/residence information before submission.
- Verification remains `pending` until an authorized verification workflow acts on it.
- No document contents or sensitive values are written to audit logs.

## Task 18 — Profile Validation & Completion
**Status: COMPLETE**
- Added deterministic server-side profile completeness endpoint.
- Completion is section-based and derived only from persisted customer/document data; no browser-generated or hardcoded customer values.
- Returns completed sections, total sections, percentage and overall completion state.

## Task 19 — Customer Profile Completion Score
**Status: COMPLETE**
- Profile completion percentage is calculated by the backend from canonical persisted fields.
- Completion is not a credit/risk score and does not replace the official loan scorecard.
- Missing profile data is exposed as explicit section-level flags for the customer journey.

## Task 20 — Admin Synchronization / Single Source of Truth
**Status: COMPLETE**
- Customer profile and residence-proof data remain in the same canonical `customers` and `documents` records used by Admin APIs.
- Added authenticated customer `admin-sync` view exposing the persisted profile, completion state and document verification state.
- Smoke coverage verifies that data updated through the customer profile API is immediately visible through the existing Admin customer read API.

### Task 13–20 API surface
- `POST /api/services/api/auth/customer-register`
- `GET/PATCH /api/services/customer-profile/{customer_id}/personal`
- `GET/PATCH /api/services/customer-profile/{customer_id}/employment-business`
- `GET/PATCH /api/services/customer-profile/{customer_id}/address-residence`
- `POST /api/services/customer-profile/{customer_id}/residence-proof`
- `GET /api/services/customer-profile/{customer_id}/profile-completion`
- `GET /api/services/customer-profile/{customer_id}/admin-sync`

### Validation coverage
- Registration, duplicate mobile, mobile login, personal and employment/business updates.
- Address/residence update and unauthorized access rejection.
- Residence proof submission, duplicate-proof rejection and pending verification state.
- Profile completion calculation and persisted Admin visibility.

## Next task
**Task 21 — Customer Journey: loan application creation and journey-state synchronization.**

## Project rule
Every completed task must be committed and smoke-tested before moving to the next task. No static customer, loan or repayment values are permitted when database/API data exists.
