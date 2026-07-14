"""Add paper-job idempotency and execution-attempt audit.

Revision ID: 0004_paper_job_recovery_audit
Revises: 0003_paper_jobs
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_paper_job_recovery_audit"
down_revision: str | Sequence[str] | None = "0003_paper_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only submission-key and execution-attempt audit tables."""
    op.create_table(
        "paper_job_submission_keys",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("request_schema_version", sa.Integer(), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("created_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_submission_keys_record_schema_version",
        ),
        sa.CheckConstraint(
            "request_schema_version = 1",
            name="ck_paper_job_submission_keys_request_schema_version",
        ),
        sa.CheckConstraint(
            "length(idempotency_key) BETWEEN 1 AND 128 "
            "AND idempotency_key NOT GLOB '*[^A-Za-z0-9._:-]*'",
            name="ck_paper_job_submission_keys_key",
        ),
        sa.CheckConstraint(
            "length(request_digest) = 64 "
            "AND request_digest NOT GLOB '*[^0-9a-f]*'",
            name="ck_paper_job_submission_keys_digest",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["paper_jobs.job_id"],
            name="fk_paper_job_submission_keys_job_id_paper_jobs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "idempotency_key",
            name="pk_paper_job_submission_keys",
        ),
        sa.UniqueConstraint(
            "job_id",
            name="uq_paper_job_submission_keys_job_id",
        ),
    )
    op.create_table(
        "paper_job_attempts",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_attempts_record_schema_version",
        ),
        sa.CheckConstraint(
            "attempt_number >= 1",
            name="ck_paper_job_attempts_number",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'failed', 'interrupted')",
            name="ck_paper_job_attempts_status",
        ),
        sa.CheckConstraint(
            "error_code IS NULL OR error_code IN ("
            "'workflow_validation_failed', 'output_conflict', "
            "'filesystem_io_failed', 'interrupted_without_output', "
            "'partial_output_detected', 'invalid_output_detected')",
            name="ck_paper_job_attempts_error_code",
        ),
        sa.CheckConstraint(
            "(status = 'running' AND completed_timestamp IS NULL "
            "AND error_code IS NULL) OR "
            "(status = 'succeeded' AND completed_timestamp IS NOT NULL "
            "AND error_code IS NULL) OR "
            "(status IN ('failed', 'interrupted') "
            "AND completed_timestamp IS NOT NULL AND error_code IS NOT NULL)",
            name="ck_paper_job_attempts_state_fields",
        ),
        sa.CheckConstraint(
            "completed_timestamp IS NULL OR completed_timestamp >= started_timestamp",
            name="ck_paper_job_attempts_timestamp_order",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["paper_jobs.job_id"],
            name="fk_paper_job_attempts_job_id_paper_jobs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("attempt_id", name="pk_paper_job_attempts"),
        sa.UniqueConstraint(
            "job_id",
            "attempt_number",
            name="uq_paper_job_attempts_job_number",
        ),
    )


def downgrade() -> None:
    """Remove only the Sprint 149 audit tables."""
    op.drop_table("paper_job_attempts")
    op.drop_table("paper_job_submission_keys")
