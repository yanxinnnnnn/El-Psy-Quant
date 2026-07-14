"""Add compact paper-job result references.

Revision ID: 0005_paper_job_result_references
Revises: 0004_paper_job_recovery_audit
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_paper_job_result_references"
down_revision: str | Sequence[str] | None = "0004_paper_job_recovery_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only the compact paper-job result-reference table."""
    op.create_table(
        "paper_job_result_references",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("root_type", sa.String(length=16), nullable=False),
        sa.Column("artifact_schema_version", sa.Integer(), nullable=False),
        sa.Column("result_summary_schema_version", sa.Integer(), nullable=False),
        sa.Column("artifact_relative_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "result_summary_relative_path", sa.String(length=1024), nullable=False
        ),
        sa.Column("created_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_paper_job_result_references_record_schema_version",
        ),
        sa.CheckConstraint(
            "root_type = 'paper'",
            name="ck_paper_job_result_references_root_type",
        ),
        sa.CheckConstraint(
            "artifact_schema_version = 1",
            name="ck_paper_job_result_references_artifact_schema_version",
        ),
        sa.CheckConstraint(
            "result_summary_schema_version = 1",
            name="ck_paper_job_result_references_summary_schema_version",
        ),
        sa.CheckConstraint(
            "artifact_relative_path NOT LIKE '/%' "
            "AND artifact_relative_path NOT LIKE '%\\%' "
            "AND artifact_relative_path NOT LIKE '%/../%'",
            name="ck_paper_job_result_references_artifact_path_shape",
        ),
        sa.CheckConstraint(
            "result_summary_relative_path NOT LIKE '/%' "
            "AND result_summary_relative_path NOT LIKE '%\\%' "
            "AND result_summary_relative_path NOT LIKE '%/../%'",
            name="ck_paper_job_result_references_summary_path_shape",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["paper_jobs.job_id"],
            name="fk_paper_job_result_references_job_id_paper_jobs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("job_id", name="pk_paper_job_result_references"),
        sa.UniqueConstraint(
            "artifact_relative_path",
            name="uq_paper_job_result_references_artifact_path",
        ),
        sa.UniqueConstraint(
            "result_summary_relative_path",
            name="uq_paper_job_result_references_summary_path",
        ),
    )


def downgrade() -> None:
    """Remove only the Sprint 150 result-reference table."""
    op.drop_table("paper_job_result_references")
