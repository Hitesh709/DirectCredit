"""Safe startup migration runner for DirectCredit.

Existing MVP databases are adopted into the migration history once, without
rewriting or dropping their data. New databases are created exclusively by
Alembic migrations. After adoption, all newer migrations are applied.
"""
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from .database import engine

BASELINE = "0001_baseline"


def _config() -> Config:
    cfg = Config("backend/alembic.ini")
    cfg.set_main_option("script_location", "backend/alembic")
    return cfg


def migrate_database() -> None:
    cfg = _config()
    adopted_legacy = False
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())
        has_version = "alembic_version" in tables
        if not has_version and tables.intersection({"customers", "loan_applications", "documents", "repayments", "customer_journey"}):
            # Legacy MVP schema: preserve it and mark the matching baseline as applied.
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": BASELINE})
            adopted_legacy = True
    # This also upgrades an adopted legacy database through all migrations after baseline.
    command.upgrade(cfg, "head")
