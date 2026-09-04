"""Add repayment collection contract fields.

Revision ID: 0003_repayment_contract
Revises: 0002_audit_events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_repayment_contract"
down_revision = "0002_audit_events"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("repayments")}
    if "payment_reference" not in columns:
        op.add_column("repayments", sa.Column("payment_reference", sa.String(length=160), nullable=True))
    if "payment_method" not in columns:
        op.add_column("repayments", sa.Column("payment_method", sa.String(length=40), nullable=True))
    if "paid_at" not in columns:
        op.add_column("repayments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    if "bounce_reason" not in columns:
        op.add_column("repayments", sa.Column("bounce_reason", sa.Text(), nullable=True))
    indexes = {i["name"] for i in inspect(bind).get_indexes("repayments")}
    if "ix_repayments_payment_reference" not in indexes:
        op.create_index("ix_repayments_payment_reference", "repayments", ["payment_reference"], unique=False)


def downgrade():
    bind = op.get_bind()
    indexes = {i["name"] for i in inspect(bind).get_indexes("repayments")}
    if "ix_repayments_payment_reference" in indexes:
        op.drop_index("ix_repayments_payment_reference", table_name="repayments")
    columns = {c["name"] for c in inspect(bind).get_columns("repayments")}
    for name in ("bounce_reason", "paid_at", "payment_method", "payment_reference"):
        if name in columns:
            op.drop_column("repayments", name)
