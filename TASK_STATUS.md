# DirectCredit Task Status

## Tasks 1–12 — Foundation & Customer Authentication
**Status: COMPLETE**

## Tasks 13–20 — Customer Registration & Canonical Profile
**Status: COMPLETE**

## Task 21 — Loan Application Start
**Status: COMPLETE**
- Customer-authenticated journey synchronization can create the customer's loan application record only within the MBL amount range of ₹5,000–₹15,000.
- Loan is persisted against the canonical customer ID.

## Task 22 — PAN Verification Journey State
**Status: COMPLETE**
- PAN verification is represented as a persisted customer-journey step and can be synchronized/read through the canonical journey API.
- Existing PAN validation service remains the provider-facing validation boundary.

## Task 23 — Aadhaar Verification Journey State
**Status: COMPLETE**
- Aadhaar verification is represented as a persisted journey step.
- Existing Aadhaar validation service remains the provider-facing validation boundary.

## Task 24 — Selfie Verification Journey State
**Status: COMPLETE**
- Selfie verification is represented as a persisted journey step tied to the customer.
- No browser-only identity is introduced.

## Task 25 — Bureau Check Journey State
**Status: COMPLETE**
- Bureau check is represented as a persisted journey step.
- External bureau remains provider-gateway controlled; no fabricated bureau score is introduced.

## Task 26 — Bank Analysis Journey State
**Status: COMPLETE**
- Bank analysis is represented as a persisted journey step.
- Bank/provider results are not fabricated in the customer journey record.

## Task 27 — Business Profile Journey State
**Status: COMPLETE**
- Business profile is linked to the canonical customer profile and represented in the persisted journey.
- Customer business information continues to come from the database-backed profile.

## Task 28 — Credit Assessment / Decision Readiness
**Status: COMPLETE**
- Credit assessment is represented as a persisted journey step.
- The journey does not invent a credit score or sanction decision; official scoring remains the backend scorecard boundary.
- Current lifecycle state remains `assessment` until a valid decision workflow changes it.

## Task 29 — E-Sign Journey State
**Status: COMPLETE**
- E-sign is represented as a persisted journey step tied to the same customer/loan.
- No fake signature completion is generated.

## Task 30 — E-Mandate Journey State
**Status: COMPLETE**
- E-mandate is represented as a persisted journey step tied to the same customer/loan.
- No fake mandate activation is generated.

### Customer Journey API surface used for Tasks 21–30
- `POST /api/services/customers/{customer_id}/journey`
- `GET /api/services/customers/{customer_id}/journey`
- `GET /api/services/loans/{loan_id}/lifecycle`
- Existing provider boundaries: `/api/services/pan/validate` and `/api/services/aadhaar/validate`

### Validation coverage
- Customer registration and authenticated journey synchronization.
- MBL application amount boundary and canonical customer/loan linkage.
- Ten persisted journey steps 21–30 are stored and returned in order.
- Lifecycle remains database-backed and reflects the created assessment loan.
- Journey read is restricted to the authenticated customer's own identity.

## Next task
**Task 31 — Eligibility engine: connect the canonical customer/loan data to the backend eligibility and official scorecard inputs without creating a second scoring source.**

## Project rule
Every completed task must be committed and smoke-tested before moving to the next task. No static customer, loan or repayment values are permitted when database/API data exists.
