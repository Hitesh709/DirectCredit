# DirectCredit Task Status

## Tasks 1–11 — Foundation & Customer Authentication
**Status: COMPLETE (implementation committed; production deployment verification remains required where external access is unavailable)**

## Task 12 — Customer Logout / Session Expiry / Revocation
**Status: COMPLETE (implementation committed; CI/deployment smoke verification pending)**

Implemented:
- Customer access tokens now carry a persistent `session_version`.
- Customer authentication validates the token session version against the live customer database record.
- Logout increments the customer's session version, immediately invalidating all previously issued customer access and refresh tokens.
- Refresh tokens are checked against the current session version before a new access token is issued.
- Password reset also increments session version, invalidating existing sessions after credential change.
- Added `/api/auth/customer-session` authenticated session validation endpoint.
- Missing/legacy customer tokens without session version are rejected by the current customer session guard.
- Session expiry continues to be enforced by the token `exp` claim.
- Session revocation is database-backed rather than browser/local-storage-only.
- No customer, loan, repayment or profile record is created during logout, refresh or session validation.

Validation requirements:
- Login → access token works while session version matches.
- Logout → old access token returns HTTP 401.
- Logout → old refresh token cannot create a new access token.
- Refresh before logout → returns a fresh access token.
- Refresh after logout → HTTP 401.
- Password reset → prior sessions are invalidated.
- Expired token → HTTP 401.

## Next task
**Task 13 — New customer registration with canonical identity creation and duplicate-mobile protection.**

## Project rule
Every completed task must be committed and smoke-tested before moving to the next task. No static customer, loan or repayment values are permitted when database/API data exists.
