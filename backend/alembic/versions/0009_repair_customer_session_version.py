"""Repair customer session-version schema drift.

Some legacy databases reached 0007 without the session_version column even
though the 0004 migration is recorded in the revision graph. This migration is
idempotent and repairs that drift without changing customer data.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0009_customer_session_repair"
down_revision = "0008_phase1_customer_360"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "customers" not in tables:
        return
    columns = {c["name"] for c in inspector.get_columns("customers")}
    if "session_version" not in columns:
        op.add_column("customers", sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    bind = op.get_bind()
    if "customers" not in inspect(bind).get_table_names():
        return
    columns = {c["name"] for c in inspect(bind).get_columns("customers")}
    if "session_version" in columns:
        op.drop_column("customers", "session_version")
