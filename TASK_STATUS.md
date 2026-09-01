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

## Task 3 — Canonical loan lifecycle/status/stage contract
**Status: COMPLETE (code implemented; deployment smoke test still required)**

Implemented:
- Added `backend/loan_lifecycle.py` as the single canonical loan lifecycle contract.
- Defined canonical statuses from `draft` through `assessment`, `sanctioned`, customer approval, E-Sign, E-Mandate, disbursement, repayment, overdue, repaid and closed.
- Defined canonical application stages including PAN, Aadhaar, Selfie, Bureau, Profile, Bank Analysis, Documents, Assessment, Sanction, Customer Approval, E-Sign, E-Mandate, Disbursement and Repayment.
- Added legacy status/stage normalization so older demo records do not create a second vocabulary.
- Added an explicit allowed-transition map to prevent invalid lifecycle jumps.
- Added `/api/services/loan-lifecycle/contract` for Customer Portal/Admin integration.
- Added `/api/services/loans/{loan_id}/lifecycle` to read the canonical lifecycle for a loan.
- Added `/api/services/loans/{loan_id}/lifecycle` transition API with validation and HTTP 409 for invalid transitions.
- Customer journey synchronization now normalizes loan status and stage into the canonical contract.
- Lifecycle response includes allowed next statuses and the financial amounts attached to the same loan record.

Done when:
- Code is committed to `main`: yes.
- Deployed API smoke test: pending.
- Existing demo portfolio compatibility test: pending.
- Customer Portal/Admin browser verification: pending.

Next task:
**Task 4 — Define document metadata, ownership and verification contract.**
