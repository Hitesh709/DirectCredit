# DirectCredit Task Status

## Task 1 — Foundation: one source of truth for customer identity
**Status: COMPLETE (code implemented; deployment smoke test still required)**

Implemented:
- 100-task master roadmap added in `PROJECT_100_TASKS.md`.
- Customer database now has persistent `customer_code`, `login_id`, and `password_hash` fields.
- Startup migration adds the new fields to existing databases without requiring a destructive reset.
- Added `/api/customer/login` endpoint.
- New login IDs create a new database-backed customer profile instead of a browser-generated persona.
- Existing customer credentials are verified using PBKDF2 password hashing.
- Customer API responses never expose `password_hash`.
- Customer portal now loads the persistent login adapter.
- The customer profile is keyed by the database customer code/ID.
- Demo mode is explicitly labelled; provider integrations remain a later task.

## Task 2 — Canonical customer identity/session contract
**Status: COMPLETE (code implemented; deployment/browser verification still required)**

Implemented:
- Added signed bearer-session validation for customer portal requests.
- Added `/api/customer/me` as the canonical "who am I" endpoint.
- Customer profile reads are now scoped to the authenticated customer.
- Customer bank-analysis, KYC/employment, risk-score and loan-trend reads are customer-scoped.
- Customer loan reads and repayment reads are customer-scoped.
- Customer document reads are customer-scoped.
- Customer profile PATCH is restricted to the authenticated customer.
- A customer session cannot request another customer's profile by changing a numeric customer ID.
- Added `customer-session-task2.js` to refresh the portal from the backend session instead of trusting the old static/demo persona.
- Profile edits are sent back to the canonical database customer record.
- Customer login/session continues to use the Task 1 database-backed identity.
- Admin endpoints remain separate so Admin can aggregate all customers/loans.

Done when:
- Code is committed to `main`: yes.
- Deployed API smoke test: pending.
- Browser test with two different customer IDs: pending.
- Cross-customer access test: pending.

Next task:
**Task 3 — Make the Customer Profile a complete editable master record and synchronize every profile field into Admin.**
