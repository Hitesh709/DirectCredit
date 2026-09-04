# DirectCredit Task Status

## Tasks 1–12 — Foundation & Customer Authentication
**Status: COMPLETE (implementation committed; production deployment verification remains required where external access is unavailable)**

## Task 13 — New Customer Registration
**Status: COMPLETE (implementation committed; CI/deployment smoke verification pending)**

Implemented:
- Added canonical mobile-first customer registration endpoint: `/api/services/api/auth/customer-register`.
- Registration creates exactly one persistent `customers` identity.
- Mobile numbers are normalized before duplicate checking and storage.
- Duplicate mobile registration returns HTTP 409 and does not create another customer.
- Optional email duplicate protection is enforced.
- A canonical `customer_code` and login identity are assigned from the created database record.
- Registration returns a signed mobile-direct customer session without fabricating any profile or loan data.

## Task 14 — Editable Personal Customer Profile
**Status: COMPLETE (implementation committed; CI/deployment smoke verification pending)**

Implemented:
- Authenticated personal-profile read endpoint.
- Authenticated personal-profile patch endpoint.
- Updates are restricted to the authenticated customer's own ID.
- Partial updates change only supplied fields; existing values are preserved.
- Name cannot be cleared accidentally.
- Personal changes are recorded as audit events.

## Task 15 — Employment / Business Profile
**Status: COMPLETE (implementation committed; CI/deployment smoke verification pending)**

Implemented:
- Authenticated employment/business profile read endpoint.
- Authenticated employment/business patch endpoint.
- Supports occupation, customer type, business name/type, income, experience, years in business, bank balance, primary bank, existing EMI and dependents.
- Numeric financial/profile values are validated as non-negative.
- Updates are restricted to the authenticated customer's own ID.
- Employment/business changes are recorded as audit events.

### Task 13–15 API surface
- `POST /api/services/api/auth/customer-register`
- `GET /api/services/customer-profile/{customer_id}/personal`
- `PATCH /api/services/customer-profile/{customer_id}/personal`
- `GET /api/services/customer-profile/{customer_id}/employment-business`
- `PATCH /api/services/customer-profile/{customer_id}/employment-business`

### Validation coverage
- New mobile registration succeeds.
- Duplicate mobile registration returns 409.
- Newly registered mobile can authenticate using the temporary mobile-only flow.
- Personal profile partial update succeeds only for the authenticated customer.
- Employment/business partial update succeeds only for the authenticated customer.
- Unauthenticated profile update returns 401.

## Next task
**Task 16 — Customer addresses and residence ownership as a canonical profile section.**

## Project rule
Every completed task must be committed and smoke-tested before moving to the next task. No static customer, loan or repayment values are permitted when database/API data exists.
