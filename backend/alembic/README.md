# DirectCredit database migrations

This directory is the canonical schema-change mechanism for DirectCredit.

## Commands

From the repository root:

```bash
cd backend
alembic upgrade head
```

For a new migration after changing `db_models.py`:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

Production deployments must run migrations before starting the API. The application must not silently mutate production schema with ad-hoc `ALTER TABLE` statements.
