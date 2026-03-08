"""initial schema with auth and idempotent ingest constraints

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "20260308_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("size", sa.String(length=80), nullable=True),
        sa.Column("funding_stage", sa.String(length=80), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("linkedin_url", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("refresh_interval", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("custom_selectors", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "url", name="uq_sources_user_url"),
    )
    op.create_index("ix_sources_user_id", "sources", ["user_id"], unique=False)
    op.create_index("ix_sources_type", "sources", ["type"], unique=False)
    op.create_index("ix_sources_status", "sources", ["status"], unique=False)
    op.create_index("ix_sources_user_status", "sources", ["user_id", "status"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("remote_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("seniority_level", sa.Text(), nullable=True),
        sa.Column("employment_type", sa.Text(), nullable=True),
        sa.Column("apply_link", sa.Text(), nullable=True),
        sa.Column("ingest_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("posted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("semantic_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("final_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("dom_snapshot", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("source_id", "ingest_fingerprint", name="uq_jobs_source_fingerprint"),
    )
    op.create_index("ix_jobs_source_id", "jobs", ["source_id"], unique=False)
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"], unique=False)
    op.create_index("ix_jobs_title", "jobs", ["title"], unique=False)
    op.create_index("ix_jobs_ingest_fingerprint", "jobs", ["ingest_fingerprint"], unique=False)
    op.create_index("ix_jobs_source_score", "jobs", ["source_id", "final_score"], unique=False)
    op.create_index("ix_jobs_company_posted", "jobs", ["company_id", "posted_date"], unique=False)

    op.create_table(
        "embeddings",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("embedding_vector", Vector(dim=384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_embeddings_job_id", "embeddings", ["job_id"], unique=False)

    op.create_table(
        "recruiters",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("linkedin", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recruiters_company_id", "recruiters", ["company_id"], unique=False)

    op.create_table(
        "outreach_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_outreach_logs_job_id", "outreach_logs", ["job_id"], unique=False)

    op.create_table(
        "extraction_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("screenshot", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("dom_snapshot", sa.Text(), nullable=True),
        sa.Column("extraction_result", sa.JSON(), nullable=True),
        sa.Column("manual_corrections", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_extraction_logs_source_id", "extraction_logs", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_extraction_logs_source_id", table_name="extraction_logs")
    op.drop_table("extraction_logs")
    op.drop_index("ix_outreach_logs_job_id", table_name="outreach_logs")
    op.drop_table("outreach_logs")
    op.drop_index("ix_recruiters_company_id", table_name="recruiters")
    op.drop_table("recruiters")
    op.drop_index("ix_embeddings_job_id", table_name="embeddings")
    op.drop_table("embeddings")
    op.drop_index("ix_jobs_company_posted", table_name="jobs")
    op.drop_index("ix_jobs_source_score", table_name="jobs")
    op.drop_index("ix_jobs_ingest_fingerprint", table_name="jobs")
    op.drop_index("ix_jobs_title", table_name="jobs")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_index("ix_jobs_source_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_sources_user_status", table_name="sources")
    op.drop_index("ix_sources_status", table_name="sources")
    op.drop_index("ix_sources_type", table_name="sources")
    op.drop_index("ix_sources_user_id", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
