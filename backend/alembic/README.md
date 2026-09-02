# DirectCredit database migrations

This directory is the canonical schema-change mechanism for DirectCredit.

## Commands

Run these commands from the repository root:

```bash
alembic -c backend/alembic.ini upgrade head
```

For a new migration after changing `backend/db_models.py`:

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "describe schema change"
alembic -c backend/alembic.ini upgrade head
```

Production deployments must run migrations before starting the API. The application must not silently mutate production schema with ad-hoc `ALTER TABLE` statements.
