# DirectCredit Configuration

Task 9 establishes one configuration source: `backend/config.py`.

## Environments

Set `APP_ENV` to `development`, `staging`, or `production`.

Production safety checks require:

- `DIRECTCREDIT_SECRET` to be explicitly configured and not a known placeholder.
- `DEBUG=false`.
- `ALLOW_DEMO_CREDENTIAL_CLAIM=false`.
- `SEED_DEMO_DATA=false`.
- `CORS_ORIGINS` to contain explicit frontend origins rather than `*`.

## Required production variables

```text
APP_ENV=production
DATABASE_URL=<managed PostgreSQL connection string>
DIRECTCREDIT_SECRET=<long random secret>
CORS_ORIGINS=https://<frontend-domain>
DEBUG=false
SEED_DEMO_DATA=false
ALLOW_DEMO_CREDENTIAL_CLAIM=false
ACCESS_TOKEN_HOURS=24
MAX_UPLOAD_MB=10
```

Do not commit `.env` or real secrets. Local development can use `.env.example` as the template; Vercel/Render should inject secrets through their environment-variable settings.
