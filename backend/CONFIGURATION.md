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

## Phase 2C external provider gateway

External providers are intentionally disabled until credentials and endpoints are configured. Never commit provider secrets.

Supported provider kinds:

- `account_aggregator` — bank/account data through an AA/FIP/FIU integration
- `bureau` — credit bureau/CIBIL integration
- `gst` — GST/GSTR evidence provider
- `itr` — income-tax/ITR evidence provider
- `trade` — trade/reference validation provider
- `geo` — address/geolocation verification provider

For each provider, configure these deployment secrets as required:

```text
DC_ACCOUNT_AGGREGATOR_URL=<provider endpoint>
DC_ACCOUNT_AGGREGATOR_TOKEN=<secret>
DC_ACCOUNT_AGGREGATOR_SIGNING_SECRET=<optional signing secret>
DC_ACCOUNT_AGGREGATOR_TIMEOUT_SECONDS=15

DC_BUREAU_URL=<provider endpoint>
DC_BUREAU_TOKEN=<secret>
DC_BUREAU_SIGNING_SECRET=<optional signing secret>
DC_BUREAU_TIMEOUT_SECONDS=15

DC_GST_URL=<provider endpoint>
DC_GST_TOKEN=<secret>
DC_GST_SIGNING_SECRET=<optional signing secret>
DC_GST_TIMEOUT_SECONDS=15

DC_ITR_URL=<provider endpoint>
DC_ITR_TOKEN=<secret>
DC_ITR_SIGNING_SECRET=<optional signing secret>
DC_ITR_TIMEOUT_SECONDS=15

DC_TRADE_URL=<provider endpoint>
DC_TRADE_TOKEN=<secret>
DC_TRADE_SIGNING_SECRET=<optional signing secret>
DC_TRADE_TIMEOUT_SECONDS=15

DC_GEO_URL=<provider endpoint>
DC_GEO_TOKEN=<secret>
DC_GEO_SIGNING_SECRET=<optional signing secret>
DC_GEO_TIMEOUT_SECONDS=15
```

The gateway sends an idempotency key and request id on every configured call. Responses are normalized only for common fields and retain provenance. Provider failures never become fabricated credit evidence.

### Account Aggregator consent

DirectCredit requires an explicit customer consent event before an Account Aggregator request can be initiated. This is a control boundary; the actual AA provider/FIP/FIU onboarding and consent-handle flow must be configured with the selected AA ecosystem participant.

### Provider onboarding notes

TransUnion CIBIL's API Marketplace requires organization onboarding/UAT/production access and contractual setup before production API use. GST/ITR/AA providers likewise require the appropriate authorized integration and customer consent. The application therefore ships with an adapter boundary rather than pretending that production credentials or provider access already exist.

Do not commit `.env` or real secrets. Vercel/Render/Railway should inject secrets through their environment-variable settings.
