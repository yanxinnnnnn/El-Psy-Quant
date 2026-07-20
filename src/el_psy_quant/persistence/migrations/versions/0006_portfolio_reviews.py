"""Add compact durable portfolio reviews.

Revision ID: 0006_portfolio_reviews
Revises: 0005_paper_job_result_references
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_portfolio_reviews"
down_revision: str | Sequence[str] | None = "0005_paper_job_result_references"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only the compact portfolio-review table."""
    op.create_table(
        "portfolio_reviews",
        sa.Column("record_schema_version", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("source_schema_version", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.String(length=512), nullable=False),
        sa.Column("source_digest", sa.String(length=64), nullable=False),
        sa.Column("source_relative_path", sa.String(length=1024), nullable=False),
        sa.Column("baseline_scenario_id", sa.String(length=512), nullable=False),
        sa.Column(
            "baseline_scenario_digest", sa.String(length=64), nullable=False
        ),
        sa.Column("proposed_scenario_id", sa.String(length=512), nullable=False),
        sa.Column(
            "proposed_scenario_digest", sa.String(length=64), nullable=False
        ),
        sa.Column("proposed_component_id", sa.String(length=512), nullable=False),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analysis_digest", sa.String(length=64), nullable=False),
        sa.Column("analysis_relative_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "create_idempotency_key", sa.String(length=128), nullable=False
        ),
        sa.Column("create_command_digest", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=512), nullable=False),
        sa.Column("created_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_schema_version", sa.Integer(), nullable=True),
        sa.Column("decision_id", sa.String(length=512), nullable=True),
        sa.Column("decision_digest", sa.String(length=64), nullable=True),
        sa.Column("decision_relative_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "decision_idempotency_key", sa.String(length=128), nullable=True
        ),
        sa.Column("decision_command_digest", sa.String(length=64), nullable=True),
        sa.Column("outcome", sa.String(length=16), nullable=True),
        sa.Column("reviewed_by", sa.String(length=512), nullable=True),
        sa.Column("reviewed_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "record_schema_version = 1",
            name="ck_portfolio_reviews_record_schema_version",
        ),
        sa.CheckConstraint(
            "source_schema_version = 1",
            name="ck_portfolio_reviews_source_schema_version",
        ),
        sa.CheckConstraint(
            "analysis_schema_version = 1",
            name="ck_portfolio_reviews_analysis_schema_version",
        ),
        sa.CheckConstraint(
            "decision_schema_version IS NULL OR decision_schema_version = 1",
            name="ck_portfolio_reviews_decision_schema_version",
        ),
        sa.CheckConstraint(
            "status IN ('awaiting_decision', 'approved', 'rejected', 'deferred')",
            name="ck_portfolio_reviews_status",
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('approved', 'rejected', 'deferred')",
            name="ck_portfolio_reviews_outcome",
        ),
        sa.CheckConstraint("version IN (1, 2)", name="ck_portfolio_reviews_version"),
        sa.CheckConstraint(
            "length(source_digest) = 64 "
            "AND source_digest NOT GLOB '*[^0-9a-f]*' "
            "AND length(baseline_scenario_digest) = 64 "
            "AND baseline_scenario_digest NOT GLOB '*[^0-9a-f]*' "
            "AND length(proposed_scenario_digest) = 64 "
            "AND proposed_scenario_digest NOT GLOB '*[^0-9a-f]*' "
            "AND length(analysis_digest) = 64 "
            "AND analysis_digest NOT GLOB '*[^0-9a-f]*' "
            "AND length(create_command_digest) = 64 "
            "AND create_command_digest NOT GLOB '*[^0-9a-f]*' "
            "AND (decision_digest IS NULL OR "
            "(length(decision_digest) = 64 "
            "AND decision_digest NOT GLOB '*[^0-9a-f]*')) "
            "AND (decision_command_digest IS NULL OR "
            "(length(decision_command_digest) = 64 "
            "AND decision_command_digest NOT GLOB '*[^0-9a-f]*'))",
            name="ck_portfolio_reviews_digest_shapes",
        ),
        sa.CheckConstraint(
            "source_relative_path LIKE "
            "'portfolio-reviews/sources/%/source.json' "
            "AND source_relative_path NOT LIKE '%\\%' "
            "AND source_relative_path NOT LIKE '%/../%' "
            "AND analysis_relative_path LIKE "
            "'portfolio-reviews/reviews/%/analysis.json' "
            "AND analysis_relative_path NOT LIKE '%\\%' "
            "AND analysis_relative_path NOT LIKE '%/../%' "
            "AND (decision_relative_path IS NULL OR "
            "(decision_relative_path LIKE "
            "'portfolio-reviews/reviews/%/decision.json' "
            "AND decision_relative_path NOT LIKE '%\\%' "
            "AND decision_relative_path NOT LIKE '%/../%'))",
            name="ck_portfolio_reviews_path_shapes",
        ),
        sa.CheckConstraint(
            "(status = 'awaiting_decision' "
            "AND decision_schema_version IS NULL AND decision_id IS NULL "
            "AND decision_digest IS NULL AND decision_relative_path IS NULL "
            "AND decision_idempotency_key IS NULL "
            "AND decision_command_digest IS NULL AND outcome IS NULL "
            "AND reviewed_by IS NULL AND reviewed_timestamp IS NULL "
            "AND version = 1 AND updated_timestamp = created_timestamp) OR "
            "(status IN ('approved', 'rejected', 'deferred') "
            "AND decision_schema_version = 1 AND decision_id IS NOT NULL "
            "AND decision_digest IS NOT NULL "
            "AND decision_relative_path IS NOT NULL "
            "AND decision_idempotency_key IS NOT NULL "
            "AND decision_command_digest IS NOT NULL AND outcome = status "
            "AND reviewed_by IS NOT NULL AND reviewed_timestamp IS NOT NULL "
            "AND version = 2 AND updated_timestamp = reviewed_timestamp "
            "AND reviewed_timestamp >= created_timestamp)",
            name="ck_portfolio_reviews_decision_consistency",
        ),
        sa.PrimaryKeyConstraint("review_id", name="pk_portfolio_reviews"),
        sa.UniqueConstraint(
            "create_idempotency_key",
            name="uq_portfolio_reviews_create_idempotency_key",
        ),
        sa.UniqueConstraint(
            "analysis_digest",
            name="uq_portfolio_reviews_analysis_digest",
        ),
        sa.UniqueConstraint(
            "analysis_relative_path",
            name="uq_portfolio_reviews_analysis_relative_path",
        ),
        sa.UniqueConstraint("decision_id", name="uq_portfolio_reviews_decision_id"),
        sa.UniqueConstraint(
            "decision_digest",
            name="uq_portfolio_reviews_decision_digest",
        ),
        sa.UniqueConstraint(
            "decision_relative_path",
            name="uq_portfolio_reviews_decision_relative_path",
        ),
        sa.UniqueConstraint(
            "decision_idempotency_key",
            name="uq_portfolio_reviews_decision_idempotency_key",
        ),
    )


def downgrade() -> None:
    """Remove only the Sprint 174 portfolio-review table."""
    op.drop_table("portfolio_reviews")
