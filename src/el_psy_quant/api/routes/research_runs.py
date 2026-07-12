"""Versioned configured research-run artifact inspection routes."""

from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Request

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.research_schemas import (
    ResearchArtifactReferencesResponse,
    ResearchMetricRecordResponse,
    ResearchRunDataResponse,
    ResearchRunDetailResponse,
    ResearchRunEvaluationResponse,
    ResearchRunListResponse,
    ResearchRunParametersResponse,
    ResearchRunSummaryResponse,
)
from el_psy_quant.application import (
    ResearchArtifactInvalidError,
    ResearchArtifactRootUnavailableError,
    ResearchRunDetail,
    ResearchRunNotFoundError,
    ResearchRunSummary,
    get_research_run_detail,
    list_research_runs,
)

router = APIRouter(prefix="/research-runs")


def _public_error(error: Exception) -> PublicApiError:
    if isinstance(error, ResearchArtifactRootUnavailableError):
        return PublicApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="research_artifact_root_unavailable",
            message="Research artifact root is unavailable",
        )
    if isinstance(error, ResearchRunNotFoundError):
        return PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="research_run_not_found",
            message="Research run not found",
        )
    return PublicApiError(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="research_artifact_invalid",
        message="Research artifact is invalid",
    )


def _artifact_root(request: Request) -> Path:
    root = request.app.state.research_artifact_root
    if root is None:
        raise _public_error(
            ResearchArtifactRootUnavailableError("research artifact root unavailable")
        )
    return root


def _summary_response(summary: ResearchRunSummary) -> ResearchRunSummaryResponse:
    return ResearchRunSummaryResponse(
        experiment_slug=summary.experiment_slug,
        run_id=summary.run_id,
        experiment_name=summary.experiment_name,
        strategy=summary.strategy,
        data_source=summary.data_source,
        symbols=list(summary.symbols),
    )


def _detail_response(detail: ResearchRunDetail) -> ResearchRunDetailResponse:
    return ResearchRunDetailResponse(
        manifest_schema_version=detail.manifest_schema_version,
        metrics_schema_version=detail.metrics_schema_version,
        experiment_slug=detail.experiment_slug,
        run_id=detail.run_id,
        experiment_name=detail.experiment_name,
        strategy=detail.strategy,
        data=ResearchRunDataResponse(
            source=detail.data.source,
            symbols=list(detail.data.symbols),
        ),
        parameters=ResearchRunParametersResponse(
            fast_window=detail.parameters.fast_window,
            slow_window=detail.parameters.slow_window,
            initial_capital=detail.parameters.initial_capital,
            transaction_cost_rate=detail.parameters.transaction_cost_rate,
            slippage_rate=detail.parameters.slippage_rate,
        ),
        evaluation=ResearchRunEvaluationResponse(
            periods_per_year=detail.evaluation.periods_per_year,
            annual_risk_free_rate=detail.evaluation.annual_risk_free_rate,
        ),
        artifacts=ResearchArtifactReferencesResponse(
            config=detail.artifacts.config,
            metadata=detail.artifacts.metadata,
            summary=detail.artifacts.summary,
            metrics=detail.artifacts.metrics,
            logs_dir=detail.artifacts.logs_dir,
        ),
        metrics=[
            ResearchMetricRecordResponse(
                symbol=metric.symbol,
                initial_equity=metric.initial_equity,
                final_equity=metric.final_equity,
                total_return=metric.total_return,
                max_drawdown=metric.max_drawdown,
                periods=metric.periods,
                cagr=metric.cagr,
                annualized_volatility=metric.annualized_volatility,
                sharpe_ratio=metric.sharpe_ratio,
            )
            for metric in detail.metrics
        ],
    )


@router.get("", response_model=ResearchRunListResponse)
async def get_research_runs(request: Request) -> ResearchRunListResponse:
    """List direct configured research runs from their manifests only."""
    try:
        runs = list_research_runs(artifact_root=_artifact_root(request))
    except (
        ResearchArtifactRootUnavailableError,
        ResearchArtifactInvalidError,
    ) as exc:
        raise _public_error(exc) from exc
    return ResearchRunListResponse(
        runs=[_summary_response(summary) for summary in runs]
    )


@router.get(
    "/{experiment_slug}/{run_id}",
    response_model=ResearchRunDetailResponse,
)
async def get_research_run(
    request: Request,
    experiment_slug: str,
    run_id: str,
) -> ResearchRunDetailResponse:
    """Read one fixed manifest and its safely referenced metrics artifact."""
    try:
        detail = get_research_run_detail(
            artifact_root=_artifact_root(request),
            experiment_slug=experiment_slug,
            run_id=run_id,
        )
    except (
        ResearchArtifactRootUnavailableError,
        ResearchRunNotFoundError,
        ResearchArtifactInvalidError,
    ) as exc:
        raise _public_error(exc) from exc
    return _detail_response(detail)
