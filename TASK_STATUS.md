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

## Task 4 — Document metadata, ownership and verification contract
**Status: COMPLETE (code implemented; deployment smoke test still required)**

Implemented:
- Expanded the document master record so every document can be linked to both `customer_id` and `loan_id`.
- Added document role, MIME type, file size, checksum, source, required flag and storage provider/key metadata.
- Added verification audit fields: `verification_status`, `verified_by`, `verified_at` and `rejection_reason`.
- Added controlled document types for PAN, Aadhaar, Selfie, Bank Statement, Business Proof, Ownership Proof, Rent Agreement, Address Proof, Income Proof and Other.
- Added controlled verification statuses: pending, under_review, verified and rejected.
- Added `/api/services/documents/register` as the canonical customer document registration/upsert endpoint.
- Added `/api/services/documents/customer/{customer_id}` for the authenticated customer's document master.
- Added `/api/services/documents/loan/{loan_id}` for documents belonging to one authenticated loan.
- Added `/api/services/documents/admin/master` so Admin can read the same document records rather than a separate static dataset.
- Added `/api/services/documents/admin/{document_id}/verification` for verification status updates and verification timestamps.
- Added a non-destructive database migration for the new document fields; existing documents are preserved.
- Document registration rejects a loan that does not belong to the authenticated customer.
- Document metadata is now part of the same customer/loan source of truth used by the project.

Done when:
- Code is committed to `main`: yes.
- Database migration compatibility: implemented; deployment smoke test pending.
- Real file/object-storage upload: not yet implemented; current contract stores metadata/storage references only.
- Customer Portal/Admin browser verification: pending.

Next task:
**Task 5 — Build the real document upload/storage pipeline and connect uploaded files to the Customer Portal and Admin Documents screens.**
