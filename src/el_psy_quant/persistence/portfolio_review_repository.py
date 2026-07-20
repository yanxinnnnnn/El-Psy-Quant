"""Caller-transaction-owned repository for compact portfolio reviews."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from el_psy_quant.persistence.portfolio_review_model import PortfolioReviewRow
from el_psy_quant.persistence.portfolio_reviews import (
    PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM,
    PortfolioReviewRecord,
    PortfolioReviewStatus,
    _digest,
    _required_string,
    _status,
    validate_portfolio_review_idempotency_key,
)
from el_psy_quant.portfolio_review import (
    PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION,
    PortfolioReviewDecisionArtifact,
)
from el_psy_quant.portfolio_review.artifact_files import (
    portfolio_review_decision_relative_path,
)


class PortfolioReviewRepository(Protocol):
    """Caller-owned persistence operations for portfolio reviews."""

    def add_awaiting_decision(
        self, *, record: PortfolioReviewRecord
    ) -> PortfolioReviewRecord: ...

    def get(self, *, review_id: str) -> PortfolioReviewRecord | None: ...

    def get_by_create_idempotency_key(
        self, *, idempotency_key: str
    ) -> PortfolioReviewRecord | None: ...

    def get_by_decision_idempotency_key(
        self, *, idempotency_key: str
    ) -> PortfolioReviewRecord | None: ...

    def list(
        self, *, status: str | None = None, limit: int | None = None
    ) -> tuple[PortfolioReviewRecord, ...]: ...

    def settle_decision(
        self,
        *,
        review_id: str,
        expected_status: PortfolioReviewStatus,
        expected_version: int,
        decision: PortfolioReviewDecisionArtifact,
        decision_idempotency_key: str,
        decision_command_digest: str,
    ) -> PortfolioReviewRecord | None: ...


def _utc_from_sqlite(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _record_from_row(row: PortfolioReviewRow) -> PortfolioReviewRecord:
    return PortfolioReviewRecord(
        record_schema_version=row.record_schema_version,  # type: ignore[arg-type]
        review_id=row.review_id,
        status=row.status,  # type: ignore[arg-type]
        source_schema_version=row.source_schema_version,  # type: ignore[arg-type]
        source_id=row.source_id,
        source_digest=row.source_digest,
        source_relative_path=row.source_relative_path,
        baseline_scenario_id=row.baseline_scenario_id,
        baseline_scenario_digest=row.baseline_scenario_digest,
        proposed_scenario_id=row.proposed_scenario_id,
        proposed_scenario_digest=row.proposed_scenario_digest,
        proposed_component_id=row.proposed_component_id,
        analysis_schema_version=row.analysis_schema_version,  # type: ignore[arg-type]
        analysis_digest=row.analysis_digest,
        analysis_relative_path=row.analysis_relative_path,
        create_idempotency_key=row.create_idempotency_key,
        create_command_digest=row.create_command_digest,
        created_by=row.created_by,
        created_timestamp=_utc_from_sqlite(row.created_timestamp),  # type: ignore[arg-type]
        decision_schema_version=row.decision_schema_version,  # type: ignore[arg-type]
        decision_id=row.decision_id,
        decision_digest=row.decision_digest,
        decision_relative_path=row.decision_relative_path,
        decision_idempotency_key=row.decision_idempotency_key,
        decision_command_digest=row.decision_command_digest,
        outcome=row.outcome,  # type: ignore[arg-type]
        reviewed_by=row.reviewed_by,
        reviewed_timestamp=_utc_from_sqlite(row.reviewed_timestamp),
        version=row.version,
        updated_timestamp=_utc_from_sqlite(row.updated_timestamp),  # type: ignore[arg-type]
    )


def _row_from_record(record: PortfolioReviewRecord) -> PortfolioReviewRow:
    return PortfolioReviewRow(
        **{
            field_name: getattr(record, field_name)
            for field_name in PortfolioReviewRow.__table__.columns.keys()
        }
    )


class SqlAlchemyPortfolioReviewRepository:
    """SQLAlchemy implementation that never commits the caller transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def add_awaiting_decision(
        self, *, record: PortfolioReviewRecord
    ) -> PortfolioReviewRecord:
        """Add and flush one valid initial record."""
        if type(record) is not PortfolioReviewRecord:
            raise ValueError("record must be a PortfolioReviewRecord")
        if record.status != "awaiting_decision" or record.version != 1:
            raise ValueError("only awaiting_decision records may be added")
        self._session.add(_row_from_record(record))
        self._session.flush()
        return record

    def get(self, *, review_id: str) -> PortfolioReviewRecord | None:
        row = self._session.get(
            PortfolioReviewRow,
            _required_string(review_id, "review_id"),
        )
        return None if row is None else _record_from_row(row)

    def get_by_create_idempotency_key(
        self, *, idempotency_key: str
    ) -> PortfolioReviewRecord | None:
        row = self._session.scalar(
            select(PortfolioReviewRow).where(
                PortfolioReviewRow.create_idempotency_key
                == validate_portfolio_review_idempotency_key(idempotency_key)
            )
        )
        return None if row is None else _record_from_row(row)

    def get_by_decision_idempotency_key(
        self, *, idempotency_key: str
    ) -> PortfolioReviewRecord | None:
        row = self._session.scalar(
            select(PortfolioReviewRow).where(
                PortfolioReviewRow.decision_idempotency_key
                == validate_portfolio_review_idempotency_key(idempotency_key)
            )
        )
        return None if row is None else _record_from_row(row)

    def list(
        self, *, status: str | None = None, limit: int | None = None
    ) -> tuple[PortfolioReviewRecord, ...]:
        if limit is not None and (
            type(limit) is not int
            or limit < 1
            or limit > PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM
        ):
            raise ValueError("limit must be an integer from 1 to 200")
        statement = select(PortfolioReviewRow)
        if status is not None:
            statement = statement.where(
                PortfolioReviewRow.status == _status(status)
            )
        statement = statement.order_by(
            PortfolioReviewRow.created_timestamp.desc(),
            PortfolioReviewRow.review_id.asc(),
        )
        if limit is not None:
            statement = statement.limit(limit)
        return tuple(
            _record_from_row(row) for row in self._session.scalars(statement).all()
        )

    def settle_decision(
        self,
        *,
        review_id: str,
        expected_status: PortfolioReviewStatus,
        expected_version: int,
        decision: PortfolioReviewDecisionArtifact,
        decision_idempotency_key: str,
        decision_command_digest: str,
    ) -> PortfolioReviewRecord | None:
        """Atomically reserve every field of the one winning decision."""
        validated_review_id = _required_string(review_id, "review_id")
        if _status(expected_status) != "awaiting_decision" or expected_version != 1:
            raise ValueError("decision settlement requires awaiting_decision version 1")
        if type(decision) is not PortfolioReviewDecisionArtifact:
            raise ValueError("decision must be a PortfolioReviewDecisionArtifact")
        if decision.review_id != validated_review_id:
            raise ValueError("decision must reference the exact review")
        key = validate_portfolio_review_idempotency_key(decision_idempotency_key)
        command_digest = _digest(
            decision_command_digest,
            "decision_command_digest",
        )
        reviewed = decision.reviewed_timestamp.to_pydatetime()
        row = self._session.scalar(
            update(PortfolioReviewRow)
            .where(
                PortfolioReviewRow.review_id == validated_review_id,
                PortfolioReviewRow.status == "awaiting_decision",
                PortfolioReviewRow.version == 1,
                PortfolioReviewRow.decision_schema_version.is_(None),
                PortfolioReviewRow.decision_id.is_(None),
                PortfolioReviewRow.decision_digest.is_(None),
                PortfolioReviewRow.decision_relative_path.is_(None),
                PortfolioReviewRow.decision_idempotency_key.is_(None),
                PortfolioReviewRow.decision_command_digest.is_(None),
                PortfolioReviewRow.outcome.is_(None),
                PortfolioReviewRow.reviewed_by.is_(None),
                PortfolioReviewRow.reviewed_timestamp.is_(None),
            )
            .values(
                status=decision.outcome,
                decision_schema_version=(
                    PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION
                ),
                decision_id=decision.decision_id,
                decision_digest=decision.decision_digest,
                decision_relative_path=portfolio_review_decision_relative_path(
                    validated_review_id
                ),
                decision_idempotency_key=key,
                decision_command_digest=command_digest,
                outcome=decision.outcome,
                reviewed_by=decision.reviewed_by,
                reviewed_timestamp=reviewed,
                version=2,
                updated_timestamp=reviewed,
            )
            .returning(PortfolioReviewRow)
            .execution_options(synchronize_session=False)
        )
        if row is None:
            return None
        self._session.flush()
        return _record_from_row(row)


__all__ = [
    "PortfolioReviewRepository",
    "SqlAlchemyPortfolioReviewRepository",
]
