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

Done when:
- Code is committed to `main`: yes.
- API syntax/runtime smoke test in the deployed environment: pending.
- Browser test with two different login IDs: pending after deployment.

Next task:
**Task 2 — Define and enforce the canonical customer identity/session contract across Customer Portal and Admin.**
