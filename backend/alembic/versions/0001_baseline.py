"""DirectCredit baseline schema.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_code", sa.String(80), unique=True),
        sa.Column("login_id", sa.String(120), unique=True),
        sa.Column("password_hash", sa.Text()),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("pan", sa.String(20), unique=True),
        sa.Column("mobile", sa.String(30)), sa.Column("email", sa.String(200)),
        sa.Column("address", sa.Text()), sa.Column("permanent_address", sa.Text()),
        sa.Column("current_city", sa.String(100)), sa.Column("gender", sa.String(40)),
        sa.Column("business_name", sa.String(200)), sa.Column("business_type", sa.String(120)),
        sa.Column("date_of_birth", sa.String(20)), sa.Column("aadhaar_masked", sa.String(30)),
        sa.Column("marital_status", sa.String(40)), sa.Column("customer_type", sa.String(40), server_default="Individual"),
        sa.Column("occupation", sa.String(100), server_default="Business"),
        sa.Column("monthly_income", sa.Float(), server_default="0"), sa.Column("work_experience_years", sa.Float(), server_default="0"),
        sa.Column("years_in_business", sa.Float(), server_default="0"), sa.Column("average_bank_balance", sa.Float(), server_default="0"),
        sa.Column("primary_bank", sa.String(120)), sa.Column("cibil_score", sa.Integer(), server_default="0"),
        sa.Column("foir", sa.Float(), server_default="0"), sa.Column("existing_emi", sa.Float(), server_default="0"),
        sa.Column("dependents", sa.Integer(), server_default="0"), sa.Column("residence_ownership", sa.String(50)),
        sa.Column("residence_since", sa.String(50)), sa.Column("ownership_proof_name", sa.String(255)),
        sa.Column("ownership_proof_status", sa.String(40), server_default="pending"),
        sa.Column("kyc_status", sa.String(40), server_default="pending"),
        sa.Column("email_verified", sa.String(20), server_default="pending"),
        sa.Column("selfie_status", sa.String(40), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "loan_applications",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("requested_amount", sa.Float(), nullable=False), sa.Column("eligible_amount", sa.Float(), server_default="0"),
        sa.Column("monthly_emi", sa.Float(), server_default="0"), sa.Column("sanctioned_amount", sa.Float(), server_default="0"),
        sa.Column("disbursed_amount", sa.Float(), server_default="0"), sa.Column("outstanding_amount", sa.Float(), server_default="0"),
        sa.Column("interest_rate", sa.Float(), server_default="0"), sa.Column("tenure_months", sa.Integer(), server_default="6"),
        sa.Column("status", sa.String(50), server_default="draft"), sa.Column("current_stage", sa.String(50), server_default="PAN"),
        sa.Column("product", sa.String(120), server_default="Micro Business Loan"), sa.Column("disbursement_details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_id", sa.Integer(), nullable=False), sa.Column("loan_id", sa.Integer()),
        sa.Column("document_type", sa.String(80), nullable=False), sa.Column("document_role", sa.String(80), server_default="supporting"),
        sa.Column("file_name", sa.String(255), nullable=False), sa.Column("mime_type", sa.String(120)), sa.Column("file_size", sa.Integer(), server_default="0"),
        sa.Column("checksum", sa.String(128)), sa.Column("source", sa.String(40), server_default="customer_portal"),
        sa.Column("required", sa.Boolean(), server_default=sa.false()), sa.Column("verification_status", sa.String(40), server_default="pending"),
        sa.Column("verified_by", sa.String(120)), sa.Column("verified_at", sa.DateTime(timezone=True)), sa.Column("rejection_reason", sa.Text()),
        sa.Column("storage_provider", sa.String(50)), sa.Column("storage_key", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "repayments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("loan_id", sa.Integer(), nullable=False), sa.Column("installment", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.String(20), nullable=False), sa.Column("due_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), server_default="0"), sa.Column("status", sa.String(30), server_default="upcoming"),
    )
    op.create_table(
        "customer_journey",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_id", sa.Integer(), nullable=False), sa.Column("loan_id", sa.Integer()),
        sa.Column("step_key", sa.String(80), nullable=False), sa.Column("step_number", sa.Integer(), server_default="0"),
        sa.Column("step_label", sa.String(160)), sa.Column("status", sa.String(40), server_default="pending"),
        sa.Column("details", sa.Text()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for table, column in (("customers", "customer_code"), ("customers", "login_id"), ("customers", "pan"), ("customers", "mobile"), ("loan_applications", "status"), ("loan_applications", "current_stage"), ("documents", "verification_status"), ("documents", "checksum"), ("repayments", "status"), ("customer_journey", "step_key"), ("customer_journey", "status")):
        op.create_index(f"ix_{table}_{column}", table, [column], unique=False)
    for table, column in (("loan_applications", "customer_id"), ("documents", "customer_id"), ("documents", "loan_id"), ("repayments", "loan_id"), ("customer_journey", "customer_id"), ("customer_journey", "loan_id")):
        op.create_index(f"ix_{table}_{column}", table, [column], unique=False)


def downgrade():
    for table in ("customer_journey", "repayments", "documents", "loan_applications", "customers"):
        op.drop_table(table)
