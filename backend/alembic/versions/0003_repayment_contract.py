"""add repayment collection contract fields

Revision ID: 0003_repayment_contract
Revises: 0002_audit_events
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_repayment_contract"
down_revision = "0002_audit_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("repayments", sa.Column("payment_reference", sa.String(length=160), nullable=True))
    op.add_column("repayments", sa.Column("payment_method", sa.String(length=40), nullable=True))
    op.add_column("repayments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("repayments", sa.Column("bounce_reason", sa.Text(), nullable=True))
    op.create_index("ix_repayments_payment_reference", "repayments", ["payment_reference"], unique=False)


def downgrade():
    op.drop_index("ix_repayments_payment_reference", table_name="repayments")
    op.drop_column("repayments", "bounce_reason")
    op.drop_column("repayments", "paid_at")
    op.drop_column("repayments", "payment_method")
    op.drop_column("repayments", "payment_reference")
