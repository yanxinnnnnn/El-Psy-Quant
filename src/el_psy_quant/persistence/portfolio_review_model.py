"""Internal SQLAlchemy model for compact durable portfolio reviews."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


_AWAITING_NULLS = (
    "decision_schema_version IS NULL AND decision_id IS NULL "
    "AND decision_digest IS NULL AND decision_relative_path IS NULL "
    "AND decision_idempotency_key IS NULL AND decision_command_digest IS NULL "
    "AND outcome IS NULL AND reviewed_by IS NULL AND reviewed_timestamp IS NULL "
    "AND version = 1 AND updated_timestamp = created_timestamp"
)
_SETTLED_VALUES = (
    "decision_schema_version = 1 AND decision_id IS NOT NULL "
    "AND decision_digest IS NOT NULL AND decision_relative_path IS NOT NULL "
    "AND decision_idempotency_key IS NOT NULL "
    "AND decision_command_digest IS NOT NULL AND outcome = status "
    "AND reviewed_by IS NOT NULL AND reviewed_timestamp IS NOT NULL "
    "AND version = 2 AND updated_timestamp = reviewed_timestamp "
    "AND reviewed_timestamp >= created_timestamp"
)


class PortfolioReviewRow(ProductPersistenceBase):
    """Internal persisted representation of one portfolio review."""

    __tablename__ = "portfolio_reviews"
    __table_args__ = (
        PrimaryKeyConstraint("review_id", name="pk_portfolio_reviews"),
        UniqueConstraint(
            "create_idempotency_key",
            name="uq_portfolio_reviews_create_idempotency_key",
        ),
        UniqueConstraint(
            "analysis_digest",
            name="uq_portfolio_reviews_analysis_digest",
        ),
        UniqueConstraint(
            "analysis_relative_path",
            name="uq_portfolio_reviews_analysis_relative_path",
        ),
        UniqueConstraint("decision_id", name="uq_portfolio_reviews_decision_id"),
        UniqueConstraint(
            "decision_digest",
            name="uq_portfolio_reviews_decision_digest",
        ),
        UniqueConstraint(
            "decision_relative_path",
            name="uq_portfolio_reviews_decision_relative_path",
        ),
        UniqueConstraint(
            "decision_idempotency_key",
            name="uq_portfolio_reviews_decision_idempotency_key",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_portfolio_reviews_record_schema_version",
        ),
        CheckConstraint(
            "source_schema_version = 1",
            name="ck_portfolio_reviews_source_schema_version",
        ),
        CheckConstraint(
            "analysis_schema_version = 1",
            name="ck_portfolio_reviews_analysis_schema_version",
        ),
        CheckConstraint(
            "decision_schema_version IS NULL OR decision_schema_version = 1",
            name="ck_portfolio_reviews_decision_schema_version",
        ),
        CheckConstraint(
            "status IN ('awaiting_decision', 'approved', 'rejected', 'deferred')",
            name="ck_portfolio_reviews_status",
        ),
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('approved', 'rejected', 'deferred')",
            name="ck_portfolio_reviews_outcome",
        ),
        CheckConstraint(
            "version IN (1, 2)",
            name="ck_portfolio_reviews_version",
        ),
        CheckConstraint(
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
        CheckConstraint(
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
        CheckConstraint(
            f"(status = 'awaiting_decision' AND {_AWAITING_NULLS}) OR "
            f"(status IN ('approved', 'rejected', 'deferred') "
            f"AND {_SETTLED_VALUES})",
            name="ck_portfolio_reviews_decision_consistency",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    review_id: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    source_schema_version: Mapped[int] = mapped_column(nullable=False)
    source_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    source_relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    baseline_scenario_id: Mapped[str] = mapped_column(String(512), nullable=False)
    baseline_scenario_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_scenario_id: Mapped[str] = mapped_column(String(512), nullable=False)
    proposed_scenario_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_component_id: Mapped[str] = mapped_column(String(512), nullable=False)
    analysis_schema_version: Mapped[int] = mapped_column(nullable=False)
    analysis_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    analysis_relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    create_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    create_command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(512), nullable=False)
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    decision_schema_version: Mapped[int | None] = mapped_column(nullable=True)
    decision_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    decision_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_relative_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    decision_idempotency_key: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    decision_command_digest: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reviewed_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    version: Mapped[int] = mapped_column(nullable=False)
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
