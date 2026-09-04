"""Safe startup migration runner for DirectCredit.

Existing MVP databases are adopted into the migration history once, without
rewriting or dropping business data. New databases are created exclusively by
Alembic migrations. Legacy deployments that already contain the audit table are
adopted at the audit revision; all newer migrations are then applied.
"""
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from .database import engine

BASELINE = "0001_baseline"
AUDIT_REVISION = "0002_audit_events"


def _config() -> Config:
    cfg = Config("backend/alembic.ini")
    cfg.set_main_option("script_location", "backend/alembic")
    return cfg


def migrate_database() -> None:
    cfg = _config()
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())
        if "alembic_version" not in tables:
            business_tables = {"customers", "loan_applications", "documents", "repayments", "customer_journey"}
            if tables.intersection(business_tables):
                # Adopt existing MVP data without modifying or dropping it.
                # If audit_events is already present, record that revision too;
                # otherwise the baseline is the correct adoption point.
                conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
                adopted_revision = AUDIT_REVISION if "audit_events" in tables else BASELINE
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": adopted_revision})
    # Applies any migrations after the adopted revision. Safe migration files
    # also tolerate columns already added by an earlier deployment.
    command.upgrade(cfg, "head")
