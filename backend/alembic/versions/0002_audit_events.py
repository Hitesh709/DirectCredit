"""Add audit event ledger.

Revision ID: 0002_audit_events
Revises: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_audit_events"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("event_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor_type", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.String(120)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(120)),
        sa.Column("customer_id", sa.Integer()),
        sa.Column("loan_id", sa.Integer()),
        sa.Column("request_id", sa.String(36)),
        sa.Column("source", sa.String(60), server_default="api"),
        sa.Column("outcome", sa.String(30), server_default="success"),
        sa.Column("reason_code", sa.String(100)),
        sa.Column("details", sa.Text()),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
    )
    for column in ("event_id", "event_time", "actor_type", "actor_id", "action", "entity_type", "entity_id", "customer_id", "loan_id", "request_id", "source", "outcome", "reason_code"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column], unique=False)


def downgrade():
    op.drop_table("audit_events")
