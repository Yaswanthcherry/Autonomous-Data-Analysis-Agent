"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

# Use JSONB on PostgreSQL, JSON otherwise
def _jsonb():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("col_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE")),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("current_stage", sa.String(100), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_analysis_jobs_dataset_id", "analysis_jobs", ["dataset_id"])

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE")),
        sa.Column("result_type", sa.String(50), nullable=False),
        sa.Column("data", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_analysis_results_job_id", "analysis_results", ["job_id"])

    op.create_table(
        "charts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("chart_type", sa.String(50), nullable=False),
        sa.Column("plotly_json", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_charts_job_id", "charts", ["job_id"])

    op.create_table(
        "ml_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE")),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("metrics", _jsonb(), nullable=False),
        sa.Column("feature_importance", _jsonb(), nullable=True),
        sa.Column("is_best", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_ml_models_job_id", "ml_models", ["job_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE")),
        sa.Column("pdf_path", sa.String(1000), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("business_insights", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_reports_job_id", "reports", ["job_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE")),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_chat_messages_job_id", "chat_messages", ["job_id"])


def downgrade():
    op.drop_table("chat_messages")
    op.drop_table("reports")
    op.drop_table("ml_models")
    op.drop_table("charts")
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")
    op.drop_table("datasets")
    op.drop_table("users")
