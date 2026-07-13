"""Add the compact rebuildable artifact index.

Revision ID: 0002_artifact_index
Revises: 0001_product_baseline
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_artifact_index"
down_revision: str | Sequence[str] | None = "0001_product_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only the compact artifact-index table."""
    op.create_table(
        "artifact_index_entries",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("artifact_key", sa.String(length=512), nullable=False),
        sa.Column("root_type", sa.String(length=16), nullable=False),
        sa.Column("relative_path", sa.String(length=1024), nullable=False),
        sa.Column("source_id", sa.String(length=512), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_artifact_index_schema_version",
        ),
        sa.CheckConstraint(
            "artifact_type IN ('research_run_manifest', "
            "'strategy_decision_manifest', 'report_artifact_manifest', "
            "'strategy_review_workflow_manifest')",
            name="ck_artifact_index_artifact_type",
        ),
        sa.CheckConstraint(
            "root_type IN ('research', 'evidence')",
            name="ck_artifact_index_root_type",
        ),
        sa.CheckConstraint(
            "(artifact_type = 'research_run_manifest' AND root_type = 'research') "
            "OR (artifact_type IN ('strategy_decision_manifest', "
            "'report_artifact_manifest', 'strategy_review_workflow_manifest') "
            "AND root_type = 'evidence')",
            name="ck_artifact_index_type_root_mapping",
        ),
        sa.PrimaryKeyConstraint(
            "artifact_type",
            "artifact_key",
            name="pk_artifact_index_entries",
        ),
        sa.UniqueConstraint(
            "root_type",
            "relative_path",
            name="uq_artifact_index_root_locator",
        ),
    )


def downgrade() -> None:
    """Remove only the compact artifact-index table."""
    op.drop_table("artifact_index_entries")
