"""Add durable queued paper-job operational input.

Revision ID: 0003_paper_jobs
Revises: 0002_artifact_index
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_paper_jobs"
down_revision: str | Sequence[str] | None = "0002_artifact_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only the durable paper-jobs table."""
    op.create_table(
        "paper_jobs",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("request_schema_version", sa.Integer(), nullable=False),
        sa.Column("request_payload", sa.Text(), nullable=False),
        sa.Column("submitted_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_jobs_record_schema_version",
        ),
        sa.CheckConstraint(
            "request_schema_version = 1",
            name="ck_paper_jobs_request_schema_version",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_paper_jobs_status",
        ),
        sa.PrimaryKeyConstraint("job_id", name="pk_paper_jobs"),
        sa.UniqueConstraint("run_id", name="uq_paper_jobs_run_id"),
    )


def downgrade() -> None:
    """Remove only the durable paper-jobs table."""
    op.drop_table("paper_jobs")
