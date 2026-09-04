# DirectCredit Production Readiness — Tasks 76–100

## Reporting & controls
- Bank analysis: `/api/services/api/admin/phase-76-100/bank-analysis`
- Risk breakdown: `/api/services/api/admin/phase-76-100/risk-breakdown`
- Portfolio quality/DPD: `/api/services/api/admin/phase-76-100/portfolio-quality`
- CSV exports: `/api/services/api/admin/phase-76-100/export/{customers|loans|documents|repayments}`
- Reconciliation: `/api/services/api/admin/phase-76-100/reconciliation`
- Document repository: `/api/services/api/admin/phase-76-100/documents`
- Notifications/settings/permissions/support/audit contracts are exposed under the same secured admin namespace.

## Provider boundary
PAN, Aadhaar, bureau, selfie, e-sign, mandate and disbursement providers are selected only through environment configuration. No provider credential is stored in source code. Unconfigured external providers return an explicit pending/adapter-ready state.

## File storage boundary
Document metadata and checksum live in the database. `storage_provider` and `storage_key` are the abstraction boundary for object storage. Production deployments should set a private object-storage provider and never expose local filesystem paths.

## Database backup
Use your managed PostgreSQL provider's encrypted backup/PITR facility. For self-managed PostgreSQL, run `pg_dump --format=custom --file=directcredit-YYYYMMDD.dump "$DATABASE_URL"` and verify restore into a separate database before release.

## Security
Security headers and an application rate limiter are installed. Production must use HTTPS, a strong `DIRECTCREDIT_SECRET`, restrictive `CORS_ORIGINS`, managed secrets, and a reverse proxy/WAF for distributed rate limiting.

## Deployment
Backend is ASGI/FastAPI and can run on Render or another managed service. Frontends can call the API through the configured public API origin. Health endpoint: `/health`. Startup runs the migration runner.

## Final audit
Before production approval, verify the live deployment against the same database, environment variables, migration head, customer/admin authentication, all menu routes, exports, repayment calculations, document access, audit records and provider configuration. The official 125-point scorecard remains an explicit configuration/provider dependency until its authoritative rules are supplied; this release does not invent those rules.
