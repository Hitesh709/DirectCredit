# DirectCredit Backup & Restore Procedure

## Production backup
1. Enable automated point-in-time backups on the managed PostgreSQL provider.
2. Take a daily full database backup and retain at least 30 days.
3. Store backups in a separate account/bucket with encryption and restricted access.
4. Keep document/object storage versioning enabled separately from database backups.
5. Never place database dumps, PAN/Aadhaar values, tokens or provider secrets in Git.

## Restore drill
1. Provision an isolated PostgreSQL instance from the selected backup.
2. Set `DATABASE_URL` and the production `DIRECTCREDIT_SECRET` only through the deployment secret store.
3. Run `alembic upgrade head` before application startup.
4. Verify `/health`, customer-to-loan ownership, document metadata, repayment balances and accounting reconciliation.
5. Run the API smoke/regression suite against the restored environment.
6. Promote the restored database only after reconciliation and application checks pass.

## Recovery targets
Define the final RPO/RTO with the hosting/database provider before production launch. The application does not claim a recovery target that the infrastructure has not configured.
