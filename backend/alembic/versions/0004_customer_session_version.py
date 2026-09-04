"""Add customer session version for persistent logout revocation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004_customer_session_version"
down_revision = "0003_repayment_contract"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("customers")}
    if "session_version" not in columns:
        op.add_column("customers", sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("customers")}
    if "session_version" in columns:
        op.drop_column("customers", "session_version")
