"""Durable portfolio-review orchestration and exact artifact inspection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, TypeAlias

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.persistence import (
    PortfolioReviewRecord,
    SqlAlchemyPortfolioReviewRepository,
    create_awaiting_portfolio_review_record,
    digest_portfolio_review_command,
    validate_portfolio_review_idempotency_key,
)
from el_psy_quant.portfolio_review import (
    PortfolioReviewAnalysisArtifact,
    PortfolioReviewDecisionArtifact,
    PortfolioReviewScenarioPair,
    PortfolioReviewSource,
    create_portfolio_review_analysis_artifact,
    create_portfolio_review_decision_artifact,
)
from el_psy_quant.portfolio_review.artifact_files import (
    PortfolioReviewArtifactConflictError,
    PortfolioReviewArtifactInvalidError,
    PortfolioReviewArtifactRootUnavailableError,
    PortfolioReviewArtifactUnavailableError,
    portfolio_review_analysis_relative_path,
    portfolio_review_decision_relative_path,
    portfolio_review_source_relative_path,
    read_portfolio_review_analysis,
    read_portfolio_review_decision,
    read_portfolio_review_source,
    validate_portfolio_review_artifact_root,
    write_portfolio_review_analysis,
    write_portfolio_review_decision,
    write_portfolio_review_source,
)


class PortfolioReviewNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("portfolio review not found")


class PortfolioReviewInvalidError(Exception):
    def __init__(self) -> None:
        super().__init__("portfolio review request is invalid")


class PortfolioReviewConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("portfolio review conflicts with existing authority")


class PortfolioReviewIdempotencyConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("portfolio review idempotency key conflicts")


class PortfolioReviewSettledConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("portfolio review is already settled")


PortfolioReviewCommandOutcome: TypeAlias = Literal["created", "replayed"]


@dataclass(frozen=True)
class PortfolioReviewSummaryView:
    """Compact database-only portfolio-review view."""

    record: PortfolioReviewRecord


@dataclass(frozen=True)
class PortfolioReviewDetailView:
    """Exact compact record plus reopened immutable file authority."""

    record: PortfolioReviewRecord
    source: PortfolioReviewSource
    analysis: PortfolioReviewAnalysisArtifact
    decision: PortfolioReviewDecisionArtifact | None


@dataclass(frozen=True)
class PortfolioReviewCreationResult:
    outcome: PortfolioReviewCommandOutcome
    review: PortfolioReviewDetailView


@dataclass(frozen=True)
class PortfolioReviewDecisionResult:
    outcome: PortfolioReviewCommandOutcome
    review: PortfolioReviewDetailView


def _timestamp(value: object) -> datetime:
    to_python = getattr(value, "to_pydatetime", None)
    if not callable(to_python):
        raise PortfolioReviewInvalidError()
    result = to_python()
    if not isinstance(result, datetime):
        raise PortfolioReviewInvalidError()
    return result


def _require_domain_inputs(
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
) -> None:
    if type(source) is not PortfolioReviewSource:
        raise PortfolioReviewInvalidError()
    if type(scenario_pair) is not PortfolioReviewScenarioPair:
        raise PortfolioReviewInvalidError()


def _cross_validate_detail(
    *,
    record: PortfolioReviewRecord,
    source: PortfolioReviewSource,
    analysis: PortfolioReviewAnalysisArtifact,
    decision: PortfolioReviewDecisionArtifact | None,
) -> None:
    if (
        record.source_relative_path
        != portfolio_review_source_relative_path(record.source_id)
        or record.analysis_relative_path
        != portfolio_review_analysis_relative_path(record.review_id)
        or source.source_id != record.source_id
        or source.source_digest != record.source_digest
        or analysis.review_id != record.review_id
        or analysis.source_id != record.source_id
        or analysis.source_digest != record.source_digest
        or analysis.analysis_digest != record.analysis_digest
        or analysis.baseline_scenario_id != record.baseline_scenario_id
        or analysis.baseline_scenario_digest
        != record.baseline_scenario_digest
        or analysis.proposed_scenario_id != record.proposed_scenario_id
        or analysis.proposed_scenario_digest
        != record.proposed_scenario_digest
        or analysis.proposed_component_id != record.proposed_component_id
        or analysis.created_by != record.created_by
        or _timestamp(analysis.created_timestamp) != record.created_timestamp
    ):
        raise PortfolioReviewArtifactInvalidError()
    if record.status == "awaiting_decision":
        if decision is not None:
            raise PortfolioReviewArtifactInvalidError()
        return
    if (
        decision is None
        or record.decision_relative_path
        != portfolio_review_decision_relative_path(record.review_id)
        or decision.review_id != record.review_id
        or decision.analysis_digest != record.analysis_digest
        or decision.source_id != record.source_id
        or decision.source_digest != record.source_digest
        or decision.baseline_scenario_id != record.baseline_scenario_id
        or decision.baseline_scenario_digest
        != record.baseline_scenario_digest
        or decision.proposed_scenario_id != record.proposed_scenario_id
        or decision.proposed_scenario_digest
        != record.proposed_scenario_digest
        or decision.decision_id != record.decision_id
        or decision.decision_digest != record.decision_digest
        or decision.outcome != record.outcome
        or decision.outcome != record.status
        or decision.reviewed_by != record.reviewed_by
        or _timestamp(decision.reviewed_timestamp) != record.reviewed_timestamp
    ):
        raise PortfolioReviewArtifactInvalidError()


def _detail_for_record(
    *,
    artifact_root: str | Path,
    record: PortfolioReviewRecord,
) -> PortfolioReviewDetailView:
    source = read_portfolio_review_source(
        root=artifact_root,
        source_id=record.source_id,
    )
    analysis = read_portfolio_review_analysis(
        root=artifact_root,
        review_id=record.review_id,
        source_id=record.source_id,
    )
    decision = (
        None
        if record.status == "awaiting_decision"
        else read_portfolio_review_decision(
            root=artifact_root,
            review_id=record.review_id,
            source_id=record.source_id,
        )
    )
    _cross_validate_detail(
        record=record,
        source=source,
        analysis=analysis,
        decision=decision,
    )
    return PortfolioReviewDetailView(
        record=record,
        source=source,
        analysis=analysis,
        decision=decision,
    )


def _create_replay(
    *,
    session: Session,
    artifact_root: str | Path,
    idempotency_key: str,
    command_digest: str,
) -> PortfolioReviewDetailView | None:
    record = SqlAlchemyPortfolioReviewRepository(
        session=session
    ).get_by_create_idempotency_key(idempotency_key=idempotency_key)
    if record is None:
        return None
    if record.create_command_digest != command_digest:
        raise PortfolioReviewIdempotencyConflictError()
    return _detail_for_record(artifact_root=artifact_root, record=record)


def create_portfolio_review_with_outcome(
    *,
    session_factory: sessionmaker[Session],
    artifact_root: str | Path,
    idempotency_key: str,
    review_id: str,
    source: PortfolioReviewSource,
    scenario_pair: PortfolioReviewScenarioPair,
    created_by: str,
    created_timestamp: object,
    assumptions: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    missing_evidence: tuple[str, ...] = (),
) -> PortfolioReviewCreationResult:
    """Create or exactly replay one durable review."""
    _require_domain_inputs(source, scenario_pair)
    try:
        key = validate_portfolio_review_idempotency_key(idempotency_key)
        root = validate_portfolio_review_artifact_root(artifact_root)
        analysis = create_portfolio_review_analysis_artifact(
            review_id=review_id,
            source=source,
            scenario_pair=scenario_pair,
            created_by=created_by,
            created_timestamp=created_timestamp,
            assumptions=assumptions,
            warnings=warnings,
            missing_evidence=missing_evidence,
        )
        command_digest = digest_portfolio_review_command(
            {"source": source.to_dict(), "analysis": analysis.to_dict()}
        )
    except PortfolioReviewArtifactRootUnavailableError:
        raise
    except (TypeError, ValueError) as exc:
        raise PortfolioReviewInvalidError() from exc

    try:
        with session_factory.begin() as session:
            replay = _create_replay(
                session=session,
                artifact_root=root,
                idempotency_key=key,
                command_digest=command_digest,
            )
            if replay is not None:
                return PortfolioReviewCreationResult(
                    outcome="replayed",
                    review=replay,
                )
            record = create_awaiting_portfolio_review_record(
                review_id=analysis.review_id,
                source_id=source.source_id,
                source_digest=source.source_digest,
                baseline_scenario_id=analysis.baseline_scenario_id,
                baseline_scenario_digest=analysis.baseline_scenario_digest,
                proposed_scenario_id=analysis.proposed_scenario_id,
                proposed_scenario_digest=analysis.proposed_scenario_digest,
                proposed_component_id=analysis.proposed_component_id,
                analysis_digest=analysis.analysis_digest,
                create_idempotency_key=key,
                create_command_digest=command_digest,
                created_by=analysis.created_by,
                created_timestamp=_timestamp(analysis.created_timestamp),
            )
            SqlAlchemyPortfolioReviewRepository(
                session=session
            ).add_awaiting_decision(record=record)
            write_portfolio_review_source(root=root, source=source)
            write_portfolio_review_analysis(
                root=root,
                source_id=source.source_id,
                analysis=analysis,
            )
            detail = _detail_for_record(artifact_root=root, record=record)
    except IntegrityError as exc:
        with session_factory() as session:
            replay = _create_replay(
                session=session,
                artifact_root=root,
                idempotency_key=key,
                command_digest=command_digest,
            )
        if replay is not None:
            return PortfolioReviewCreationResult(
                outcome="replayed",
                review=replay,
            )
        raise PortfolioReviewConflictError() from exc
    return PortfolioReviewCreationResult(outcome="created", review=detail)


def list_portfolio_reviews(
    *,
    session_factory: sessionmaker[Session],
    status: str | None = None,
    limit: int | None = None,
) -> tuple[PortfolioReviewSummaryView, ...]:
    """Return only compact database records in deterministic order."""
    try:
        with session_factory() as session:
            records = SqlAlchemyPortfolioReviewRepository(session=session).list(
                status=status,
                limit=limit,
            )
    except ValueError as exc:
        raise PortfolioReviewInvalidError() from exc
    return tuple(PortfolioReviewSummaryView(record=record) for record in records)


def get_portfolio_review_detail(
    *,
    session_factory: sessionmaker[Session],
    artifact_root: str | Path,
    review_id: str,
) -> PortfolioReviewDetailView:
    """Reopen and cross-validate one exact durable review."""
    with session_factory() as session:
        try:
            record = SqlAlchemyPortfolioReviewRepository(session=session).get(
                review_id=review_id
            )
        except ValueError as exc:
            raise PortfolioReviewInvalidError() from exc
    if record is None:
        raise PortfolioReviewNotFoundError()
    return _detail_for_record(artifact_root=artifact_root, record=record)


def _decision_replay(
    *,
    session: Session,
    artifact_root: str | Path,
    idempotency_key: str,
    command_digest: str,
    review_id: str,
) -> PortfolioReviewDetailView | None:
    record = SqlAlchemyPortfolioReviewRepository(
        session=session
    ).get_by_decision_idempotency_key(idempotency_key=idempotency_key)
    if record is None:
        return None
    if (
        record.decision_command_digest != command_digest
        or record.review_id != review_id
    ):
        raise PortfolioReviewIdempotencyConflictError()
    return _detail_for_record(artifact_root=artifact_root, record=record)


def _classify_settled_decision(
    *,
    artifact_root: str | Path,
    record: PortfolioReviewRecord,
    idempotency_key: str,
    command_digest: str,
) -> PortfolioReviewDetailView | None:
    if record.status == "awaiting_decision":
        return None
    if record.decision_idempotency_key != idempotency_key:
        raise PortfolioReviewSettledConflictError()
    if record.decision_command_digest != command_digest:
        raise PortfolioReviewIdempotencyConflictError()
    return _detail_for_record(artifact_root=artifact_root, record=record)


def record_portfolio_review_decision_with_outcome(
    *,
    session_factory: sessionmaker[Session],
    artifact_root: str | Path,
    review_id: str,
    idempotency_key: str,
    decision_id: str,
    outcome: str,
    rationale: str,
    reviewed_by: str,
    reviewed_timestamp: object,
    notes: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
) -> PortfolioReviewDecisionResult:
    """Settle or exactly replay the one human decision."""
    awaiting = get_portfolio_review_detail(
        session_factory=session_factory,
        artifact_root=artifact_root,
        review_id=review_id,
    )
    try:
        key = validate_portfolio_review_idempotency_key(idempotency_key)
        decision = create_portfolio_review_decision_artifact(
            decision_id=decision_id,
            analysis=awaiting.analysis,
            outcome=outcome,
            rationale=rationale,
            reviewed_by=reviewed_by,
            reviewed_timestamp=reviewed_timestamp,
            notes=notes,
            warnings=warnings,
        )
        if decision.reviewed_timestamp < awaiting.analysis.created_timestamp:
            raise ValueError("reviewed timestamp precedes analysis creation")
        command_digest = digest_portfolio_review_command(decision.to_dict())
    except (TypeError, ValueError) as exc:
        raise PortfolioReviewInvalidError() from exc

    settlement_missed = False
    try:
        with session_factory.begin() as session:
            replay = _decision_replay(
                session=session,
                artifact_root=artifact_root,
                idempotency_key=key,
                command_digest=command_digest,
                review_id=awaiting.record.review_id,
            )
            if replay is not None:
                return PortfolioReviewDecisionResult(
                    outcome="replayed",
                    review=replay,
                )
            repository = SqlAlchemyPortfolioReviewRepository(session=session)
            current = repository.get(review_id=awaiting.record.review_id)
            if current is None:
                raise PortfolioReviewNotFoundError()
            replay = _classify_settled_decision(
                artifact_root=artifact_root,
                record=current,
                idempotency_key=key,
                command_digest=command_digest,
            )
            if replay is not None:
                return PortfolioReviewDecisionResult(
                    outcome="replayed",
                    review=replay,
                )
            settled = repository.settle_decision(
                review_id=current.review_id,
                expected_status="awaiting_decision",
                expected_version=1,
                decision=decision,
                decision_idempotency_key=key,
                decision_command_digest=command_digest,
            )
            if settled is None:
                settlement_missed = True
            else:
                write_portfolio_review_decision(
                    root=artifact_root,
                    source_id=settled.source_id,
                    decision=decision,
                )
                detail = _detail_for_record(
                    artifact_root=artifact_root,
                    record=settled,
                )
    except IntegrityError as exc:
        with session_factory() as session:
            replay = _decision_replay(
                session=session,
                artifact_root=artifact_root,
                idempotency_key=key,
                command_digest=command_digest,
                review_id=awaiting.record.review_id,
            )
            current = SqlAlchemyPortfolioReviewRepository(session=session).get(
                review_id=awaiting.record.review_id
            )
        if replay is not None:
            return PortfolioReviewDecisionResult(
                outcome="replayed",
                review=replay,
            )
        if current is not None and current.status != "awaiting_decision":
            raise PortfolioReviewSettledConflictError() from exc
        raise PortfolioReviewConflictError() from exc
    if settlement_missed:
        with session_factory() as session:
            current = SqlAlchemyPortfolioReviewRepository(session=session).get(
                review_id=awaiting.record.review_id
            )
        if current is None:
            raise PortfolioReviewNotFoundError()
        replay = _classify_settled_decision(
            artifact_root=artifact_root,
            record=current,
            idempotency_key=key,
            command_digest=command_digest,
        )
        if replay is not None:
            return PortfolioReviewDecisionResult(
                outcome="replayed",
                review=replay,
            )
        raise PortfolioReviewConflictError()
    return PortfolioReviewDecisionResult(outcome="created", review=detail)


__all__ = [
    "PortfolioReviewArtifactConflictError",
    "PortfolioReviewArtifactInvalidError",
    "PortfolioReviewArtifactRootUnavailableError",
    "PortfolioReviewArtifactUnavailableError",
    "PortfolioReviewConflictError",
    "PortfolioReviewCreationResult",
    "PortfolioReviewDecisionResult",
    "PortfolioReviewDetailView",
    "PortfolioReviewIdempotencyConflictError",
    "PortfolioReviewInvalidError",
    "PortfolioReviewNotFoundError",
    "PortfolioReviewSettledConflictError",
    "PortfolioReviewSummaryView",
    "create_portfolio_review_with_outcome",
    "get_portfolio_review_detail",
    "list_portfolio_reviews",
    "record_portfolio_review_decision_with_outcome",
]
