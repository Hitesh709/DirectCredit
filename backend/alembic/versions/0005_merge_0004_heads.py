"""Merge the customer-session and servicing/accounting migration branches.

Revision ID: 0005_merge_0004_heads
Revises: 0004_customer_session_version, 0004_servicing_accounting
"""
from alembic import op

revision = "0005_merge_0004_heads"
down_revision = ("0004_customer_session_version", "0004_servicing_accounting")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
