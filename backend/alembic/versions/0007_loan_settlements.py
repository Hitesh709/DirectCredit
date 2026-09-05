"""Add settlement and closure workflow records.

Revision ID: 0007_loan_settlements
Revises: 0006_sample_function_completion
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
revision="0007_loan_settlements"
down_revision="0006_sample_function_completion"
branch_labels=None
depends_on=None

def upgrade():
    if "loan_settlements" not in inspect(op.get_bind()).get_table_names():
        op.create_table("loan_settlements",
            sa.Column("id",sa.Integer,primary_key=True),sa.Column("loan_id",sa.Integer,index=True,nullable=False),sa.Column("customer_id",sa.Integer,index=True,nullable=False),sa.Column("settlement_type",sa.String(40),index=True,nullable=False),sa.Column("outstanding_amount",sa.Float,default=0),sa.Column("proposed_amount",sa.Float,default=0),sa.Column("approved_amount",sa.Float,default=0),sa.Column("waiver_amount",sa.Float,default=0),sa.Column("status",sa.String(40),index=True,default="quoted"),sa.Column("reason",sa.Text),sa.Column("reference",sa.String(160),index=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.Column("approved_at",sa.DateTime(timezone=True)))

def downgrade():
    if "loan_settlements" in inspect(op.get_bind()).get_table_names(): op.drop_table("loan_settlements")
