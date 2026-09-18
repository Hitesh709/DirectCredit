"""Safe startup migration runner for DirectCredit.

Existing MVP databases are adopted into the migration history once, without
rewriting or dropping business data. New databases are created exclusively by
Alembic migrations. Legacy deployments that already contain the audit table are
adopted at the audit revision; all newer migrations are then applied.

The runner also repairs known non-destructive migration-history drift: some
legacy databases contain the Phase 1 Customer 360 tables while still recording
0007 as their Alembic revision. Those databases are stamped to 0008 because
the 0008 schema is already present, then the normal upgrade continues.
"""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from .database import engine

BASELINE = "0001_baseline"
AUDIT_REVISION = "0002_audit_events"
PHASE1_REVISION = "0008_phase1_customer_360"
HEAD_REPAIR_REVISION = "0009_customer_session_repair"
BACKEND_DIR = Path(__file__).resolve().parent


def _config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def _repair_known_revision_drift(conn, tables: set[str]) -> None:
    """Repair only a known, verified schema/revision mismatch.

    This does not create, drop, or alter business tables. It only advances the
    migration marker when all Phase 1 tables are already present, preventing
    Alembic from trying to recreate them during application startup.
    """
    if "alembic_version" not in tables:
        return

    current = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
    phase1_tables = {
        "customer_businesses",
        "customer_contacts",
        "customer_addresses",
        "customer_kyc_profiles",
        "customer_bank_accounts",
        "customer_consents",
        "customer_preferences",
        "customer_risk_profiles",
        "customer_events",
    }
    if current == "0007_loan_settlements" and phase1_tables.issubset(tables):
        conn.execute(
            text("UPDATE alembic_version SET version_num = :revision"),
            {"revision": PHASE1_REVISION},
        )


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
                tables.add("alembic_version")

        _repair_known_revision_drift(conn, tables)

    # Applies any migrations after the adopted/repair revision. Safe migration
    # files also tolerate columns already added by an earlier deployment.
    command.upgrade(cfg, "head")
