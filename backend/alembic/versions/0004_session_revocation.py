"""Add persistent customer session revocation records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004_session_revocation"
down_revision = "0003_repayment_contract"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "revoked_tokens" not in tables:
        op.create_table(
            "revoked_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
            sa.Column("user_id", sa.Integer(), nullable=True, index=True),
            sa.Column("role", sa.String(length=40), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_revoked_tokens_token_hash", "revoked_tokens", ["token_hash"], unique=True)


def downgrade():
    bind = op.get_bind()
    if "revoked_tokens" in inspect(bind).get_table_names():
        op.drop_index("ix_revoked_tokens_token_hash", table_name="revoked_tokens")
        op.drop_table("revoked_tokens")
