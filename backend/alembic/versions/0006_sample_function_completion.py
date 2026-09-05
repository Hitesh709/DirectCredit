"""Add persisted scorecard, bank transaction and collection operations.

Revision ID: 0006_sample_function_completion
Revises: 0005_merge_0004_heads
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0006_sample_function_completion"
down_revision = "0005_merge_0004_heads"
branch_labels = None
depends_on = None


def _add_column(table, column):
    bind = op.get_bind()
    if column.name not in {c["name"] for c in inspect(bind).get_columns(table)}:
        op.add_column(table, column)


def _table(name, columns):
    bind = op.get_bind()
    if name not in inspect(bind).get_table_names():
        op.create_table(name, *columns)


def upgrade():
    for column in [
        sa.Column("scorecard_score", sa.Integer),
        sa.Column("scorecard_max", sa.Integer),
        sa.Column("scorecard_version", sa.String(40)),
        sa.Column("scorecard_decision", sa.String(40)),
        sa.Column("scorecard_approval_percent", sa.Integer),
        sa.Column("scorecard_reasons", sa.Text),
        sa.Column("scorecard_hard_rejects", sa.Text),
        sa.Column("scorecard_factor_scores", sa.Text),
    ]:
        _add_column("loan_applications", column)

    _table("collection_agents", [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("agent_code", sa.String(80), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("mobile", sa.String(30)),
        sa.Column("active", sa.Boolean, default=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ])
    _table("collection_actions", [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("loan_id", sa.Integer, index=True, nullable=False),
        sa.Column("customer_id", sa.Integer, index=True, nullable=False),
        sa.Column("agent_id", sa.Integer, index=True),
        sa.Column("action_type", sa.String(50), index=True, nullable=False),
        sa.Column("amount", sa.Float, default=0),
        sa.Column("reference", sa.String(160), index=True),
        sa.Column("status", sa.String(40), index=True, default="recorded"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    ])
    _table("bank_transactions", [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_id", sa.Integer, index=True, nullable=False),
        sa.Column("loan_id", sa.Integer, index=True),
        sa.Column("transaction_date", sa.String(20), index=True, nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("direction", sa.String(10), index=True, nullable=False),
        sa.Column("category", sa.String(80), index=True),
        sa.Column("description", sa.Text),
        sa.Column("reference", sa.String(160), index=True),
        sa.Column("balance", sa.Float),
        sa.Column("source", sa.String(40), default="bank_statement"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    ])


def downgrade():
    bind = op.get_bind()
    for name in ("bank_transactions", "collection_actions", "collection_agents"):
        if name in inspect(bind).get_table_names():
            op.drop_table(name)
    for name in ("scorecard_factor_scores", "scorecard_hard_rejects", "scorecard_reasons", "scorecard_approval_percent", "scorecard_decision", "scorecard_version", "scorecard_max", "scorecard_score"):
        cols = {c["name"] for c in inspect(bind).get_columns("loan_applications")}
        if name in cols:
            op.drop_column("loan_applications", name)
