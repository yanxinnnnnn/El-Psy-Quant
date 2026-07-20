"""Versioned durable portfolio-review create, read, and decision routes."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Literal, NoReturn

import pandas as pd
from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.dependencies import (
    get_portfolio_review_artifact_root,
    get_product_session_factory,
    portfolio_review_artifact_root_unavailable,
    product_database_unavailable,
)
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.observability import log_portfolio_review_command_completed
from el_psy_quant.api.portfolio_review_schemas import (
    PortfolioReviewAnalysisResponse,
    PortfolioReviewCommandResponse,
    PortfolioReviewCreateRequest,
    PortfolioReviewDecisionRequest,
    PortfolioReviewDecisionResponse,
    PortfolioReviewDetailResponse,
    PortfolioReviewRecordResponse,
    PortfolioReviewSourceResponse,
)
from el_psy_quant.application import (
    PortfolioReviewArtifactConflictError,
    PortfolioReviewArtifactInvalidError,
    PortfolioReviewArtifactRootUnavailableError,
    PortfolioReviewArtifactUnavailableError,
    PortfolioReviewConflictError,
    PortfolioReviewDetailView,
    PortfolioReviewIdempotencyConflictError,
    PortfolioReviewInvalidError,
    PortfolioReviewNotFoundError,
    PortfolioReviewSettledConflictError,
    create_portfolio_review_with_outcome,
    get_portfolio_review_detail,
    list_portfolio_reviews,
    record_portfolio_review_decision_with_outcome,
)
from el_psy_quant.portfolio_review import (
    create_portfolio_review_baseline_scenario,
    create_portfolio_review_component,
    create_portfolio_review_evidence_reference,
    create_portfolio_review_proposed_scenario,
    create_portfolio_review_scenario_pair,
    create_portfolio_review_source,
)

router = APIRouter(prefix="/portfolio-reviews")
SessionFactory = Annotated[
    sessionmaker[Session], Depends(get_product_session_factory)
]
ArtifactRoot = Annotated[Path, Depends(get_portfolio_review_artifact_root)]
ReviewStatusFilter = Literal[
    "awaiting_decision", "approved", "rejected", "deferred"
]


def _raise_application_error(exc: Exception) -> NoReturn:
    if isinstance(exc, PortfolioReviewNotFoundError):
        error = PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="portfolio_review_not_found",
            message="Portfolio review was not found",
        )
    elif isinstance(exc, PortfolioReviewIdempotencyConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_idempotency_conflict",
            message="Portfolio review idempotency key conflicts",
        )
    elif isinstance(exc, PortfolioReviewSettledConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_settled_conflict",
            message="Portfolio review is already settled",
        )
    elif isinstance(exc, PortfolioReviewArtifactConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_artifact_conflict",
            message="Portfolio review artifact conflicts",
        )
    elif isinstance(exc, PortfolioReviewArtifactInvalidError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_artifact_invalid",
            message="Portfolio review artifact is invalid",
        )
    elif isinstance(exc, PortfolioReviewArtifactUnavailableError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_artifact_unavailable",
            message="Portfolio review artifact is unavailable",
        )
    elif isinstance(exc, PortfolioReviewConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="portfolio_review_conflict",
            message="Portfolio review conflicts with existing authority",
        )
    elif isinstance(exc, (PortfolioReviewInvalidError, ValueError)):
        error = PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="portfolio_review_invalid",
            message="Portfolio review request is invalid",
        )
    elif isinstance(exc, PortfolioReviewArtifactRootUnavailableError):
        raise portfolio_review_artifact_root_unavailable() from exc
    else:
        raise exc
    raise error from exc


def _record_response(record: object) -> PortfolioReviewRecordResponse:
    payload = asdict(record)  # type: ignore[arg-type]
    for path_field in (
        "source_relative_path",
        "analysis_relative_path",
        "decision_relative_path",
        "create_idempotency_key",
        "create_command_digest",
        "decision_idempotency_key",
        "decision_command_digest",
    ):
        payload.pop(path_field)
    return PortfolioReviewRecordResponse.model_validate(payload)


def _detail_response(view: PortfolioReviewDetailView) -> PortfolioReviewDetailResponse:
    return PortfolioReviewDetailResponse(
        record=_record_response(view.record),
        source=PortfolioReviewSourceResponse.model_validate(view.source.to_dict()),
        analysis=PortfolioReviewAnalysisResponse.model_validate(
            view.analysis.to_dict()
        ),
        decision=(
            None
            if view.decision is None
            else PortfolioReviewDecisionResponse.model_validate(
                view.decision.to_dict()
            )
        ),
    )


def _source_and_pair(command: PortfolioReviewCreateRequest):
    components = tuple(
        create_portfolio_review_component(
            component_id=component.component_id,
            strategy_id=component.strategy_id,
            evidence_references=tuple(
                create_portfolio_review_evidence_reference(
                    reference_type=reference.reference_type,
                    reference_id=reference.reference_id,
                    label=reference.label,
                    description=reference.description,
                )
                for reference in component.evidence_references
            ),
            symbols=component.symbols,
            label=component.label,
            description=component.description,
        )
        for component in command.source.components
    )
    component_ids = tuple(component.component_id for component in components)
    aligned_returns = pd.DataFrame(
        [
            observation.component_returns
            for observation in command.source.return_observations
        ],
        index=pd.DatetimeIndex(
            [
                observation.timestamp
                for observation in command.source.return_observations
            ]
        ),
        columns=component_ids,
    )
    source = create_portfolio_review_source(
        source_id=command.source.source_id,
        components=components,
        aligned_returns=aligned_returns,
        evaluation_frequency=command.source.evaluation_frequency,
        periods_per_year=command.source.periods_per_year,
        created_by=command.source.created_by,
        created_timestamp=command.source.created_timestamp,
        assumptions=command.source.assumptions,
        warnings=command.source.warnings,
        missing_evidence=command.source.missing_evidence,
    )
    baseline = create_portfolio_review_baseline_scenario(
        scenario_id=command.baseline_scenario.scenario_id,
        source=source,
        weights=command.baseline_scenario.weights,
        rationale=command.baseline_scenario.rationale,
        assumptions=command.baseline_scenario.assumptions,
        warnings=command.baseline_scenario.warnings,
    )
    proposed = create_portfolio_review_proposed_scenario(
        scenario_id=command.proposed_scenario.scenario_id,
        source=source,
        weights=command.proposed_scenario.weights,
        proposed_component_id=command.proposed_scenario.proposed_component_id,
        rationale=command.proposed_scenario.rationale,
        assumptions=command.proposed_scenario.assumptions,
        warnings=command.proposed_scenario.warnings,
    )
    return source, create_portfolio_review_scenario_pair(
        source=source,
        baseline=baseline,
        proposed=proposed,
    )


def _request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if not isinstance(value, str):
        raise RuntimeError("server request ID is unavailable")
    return value


@router.post(
    "",
    response_model=PortfolioReviewCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PortfolioReviewCommandResponse}},
)
def post_portfolio_review(
    request: Request,
    response: Response,
    command: PortfolioReviewCreateRequest,
    session_factory: SessionFactory,
    artifact_root: ArtifactRoot,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> PortfolioReviewCommandResponse:
    """Create or exactly replay one immutable portfolio review."""
    try:
        source, pair = _source_and_pair(command)
        result = create_portfolio_review_with_outcome(
            session_factory=session_factory,
            artifact_root=artifact_root,
            idempotency_key=idempotency_key,
            review_id=command.review_id,
            source=source,
            scenario_pair=pair,
            created_by=command.analysis.created_by,
            created_timestamp=command.analysis.created_timestamp,
            assumptions=tuple(command.analysis.assumptions),
            warnings=tuple(command.analysis.warnings),
            missing_evidence=tuple(command.analysis.missing_evidence),
        )
        response.status_code = (
            HTTPStatus.CREATED if result.outcome == "created" else HTTPStatus.OK
        )
        body = PortfolioReviewCommandResponse(
            outcome=result.outcome,
            review=_detail_response(result.review),
        )
        log_portfolio_review_command_completed(
            event="portfolio_review_create_completed",
            request_id=_request_id(request),
            command="create",
            review_id=result.review.record.review_id,
            decision_id=None,
            durable_status=result.review.record.status,
            command_outcome=result.outcome,
            human_decision_outcome=result.review.record.outcome,
        )
        return body
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)

@router.get("", response_model=list[PortfolioReviewRecordResponse])
def get_portfolio_reviews(
    session_factory: SessionFactory,
    status: Annotated[ReviewStatusFilter | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PortfolioReviewRecordResponse]:
    """Return compact database-only review metadata."""
    try:
        return [
            _record_response(view.record)
            for view in list_portfolio_reviews(
                session_factory=session_factory,
                status=status,
                limit=limit,
            )
        ]
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get("/{review_id}", response_model=PortfolioReviewDetailResponse)
def get_portfolio_review(
    review_id: str,
    session_factory: SessionFactory,
    artifact_root: ArtifactRoot,
) -> PortfolioReviewDetailResponse:
    try:
        return _detail_response(
            get_portfolio_review_detail(
                session_factory=session_factory,
                artifact_root=artifact_root,
                review_id=review_id,
            )
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.post(
    "/{review_id}/decision",
    response_model=PortfolioReviewCommandResponse,
    status_code=HTTPStatus.CREATED,
    responses={HTTPStatus.OK: {"model": PortfolioReviewCommandResponse}},
)
def post_portfolio_review_decision(
    review_id: str,
    request: Request,
    response: Response,
    command: PortfolioReviewDecisionRequest,
    session_factory: SessionFactory,
    artifact_root: ArtifactRoot,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> PortfolioReviewCommandResponse:
    """Settle or exactly replay the one human governance decision."""
    try:
        result = record_portfolio_review_decision_with_outcome(
            session_factory=session_factory,
            artifact_root=artifact_root,
            review_id=review_id,
            idempotency_key=idempotency_key,
            decision_id=command.decision_id,
            outcome=command.outcome,
            rationale=command.rationale,
            reviewed_by=command.reviewed_by,
            reviewed_timestamp=command.reviewed_timestamp,
            notes=tuple(command.notes),
            warnings=tuple(command.warnings),
        )
        response.status_code = (
            HTTPStatus.CREATED if result.outcome == "created" else HTTPStatus.OK
        )
        body = PortfolioReviewCommandResponse(
            outcome=result.outcome,
            review=_detail_response(result.review),
        )
        log_portfolio_review_command_completed(
            event="portfolio_review_decision_completed",
            request_id=_request_id(request),
            command="decision",
            review_id=result.review.record.review_id,
            decision_id=result.review.record.decision_id,
            durable_status=result.review.record.status,
            command_outcome=result.outcome,
            human_decision_outcome=result.review.record.outcome,
        )
        return body
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)
