"""Add loan servicing, disbursement and accounting tables.

Revision ID: 0004_servicing_accounting
Revises: 0003_repayment_contract
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
revision = "0004_servicing_accounting"
down_revision = "0003_repayment_contract"
branch_labels = None
depends_on = None

def _table(name, columns):
    bind = op.get_bind()
    if name not in inspect(bind).get_table_names():
        op.create_table(name, *columns)

def upgrade():
    _table("disbursements", [sa.Column("id",sa.Integer,primary_key=True),sa.Column("loan_id",sa.Integer,index=True,nullable=False),sa.Column("customer_id",sa.Integer,index=True,nullable=False),sa.Column("amount",sa.Float,nullable=False),sa.Column("reference",sa.String(160),index=True),sa.Column("method",sa.String(40)),sa.Column("status",sa.String(40),index=True),sa.Column("disbursed_at",sa.DateTime(timezone=True)),sa.Column("details",sa.Text),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now())])
    _table("loan_ledger", [sa.Column("id",sa.Integer,primary_key=True),sa.Column("loan_id",sa.Integer,index=True,nullable=False),sa.Column("customer_id",sa.Integer,index=True,nullable=False),sa.Column("entry_type",sa.String(40),index=True,nullable=False),sa.Column("reference",sa.String(160),index=True),sa.Column("debit",sa.Float,default=0),sa.Column("credit",sa.Float,default=0),sa.Column("balance",sa.Float,default=0),sa.Column("description",sa.String(255)),sa.Column("entry_time",sa.DateTime(timezone=True),server_default=sa.func.now(),index=True)])
    _table("accounting_ledger", [sa.Column("id",sa.Integer,primary_key=True),sa.Column("loan_id",sa.Integer,index=True),sa.Column("customer_id",sa.Integer,index=True),sa.Column("account",sa.String(80),index=True,nullable=False),sa.Column("entry_type",sa.String(40),index=True,nullable=False),sa.Column("reference",sa.String(160),index=True),sa.Column("debit",sa.Float,default=0),sa.Column("credit",sa.Float,default=0),sa.Column("narration",sa.String(255)),sa.Column("entry_time",sa.DateTime(timezone=True),server_default=sa.func.now(),index=True)])

def downgrade():
    for name in ("accounting_ledger","loan_ledger","disbursements"):
        if name in inspect(op.get_bind()).get_table_names(): op.drop_table(name)
