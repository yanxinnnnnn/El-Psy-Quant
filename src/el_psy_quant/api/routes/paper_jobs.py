"""Versioned durable paper-job submission, control, and result routes."""

from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Literal, NoReturn

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.dependencies import (
    get_paper_artifact_root,
    get_product_session_factory,
    paper_artifact_root_unavailable,
    product_database_unavailable,
)
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.paper_job_schemas import (
    PaperJobAttemptResponse,
    PaperJobRecoveryRequest,
    PaperJobRecoveryResponse,
    PaperJobResponse,
    PaperJobResultAuditResponse,
    PaperJobResultReferenceResponse,
    PaperJobResultResponse,
    PaperJobResultSummaryResponse,
    PaperJobSubmissionResponse,
)
from el_psy_quant.api.paper_run_schemas import PaperRunCommandRequest
from el_psy_quant.api.routes.paper_runs import (
    paper_run_command_from_request,
    paper_trading_artifact_response,
)
from el_psy_quant.application import (
    PaperArtifactRootUnavailableError,
    PaperJobClaim,
    PaperJobAttemptRecord,
    PaperJobConflictError,
    PaperJobExecutionError,
    PaperJobIdempotencyConflictError,
    PaperJobNotFoundError,
    PaperJobOutputConflictError,
    PaperJobRecoveryError,
    PaperJobResultInvalidError,
    PaperJobResultUnavailableError,
    PaperJobResultView,
    PaperJobStateConflictError,
    PaperJobStatusView,
    PaperRunInvalidError,
    cancel_paper_job,
    claim_product_paper_job,
    execute_claimed_product_paper_job,
    get_paper_job_status_view,
    list_paper_job_attempts,
    list_paper_job_status_views,
    read_paper_job_result,
    recover_product_paper_job,
    retry_product_paper_job,
    submit_paper_job_with_outcome,
)

router = APIRouter(prefix="/paper-jobs")
SessionFactory = Annotated[
    sessionmaker[Session], Depends(get_product_session_factory)
]
PaperRoot = Annotated[Path, Depends(get_paper_artifact_root)]
JobStatusFilter = Literal["queued", "running", "succeeded", "failed", "canceled"]


def _raise_application_error(exc: Exception) -> NoReturn:
    if isinstance(exc, PaperJobNotFoundError):
        error = PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="paper_job_not_found",
            message="Paper job was not found",
        )
    elif isinstance(exc, PaperRunInvalidError | ValueError):
        error = PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="paper_job_invalid",
            message="Paper job request is invalid",
        )
    elif isinstance(exc, PaperJobIdempotencyConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_idempotency_conflict",
            message="Paper job idempotency key conflicts",
        )
    elif isinstance(exc, PaperJobConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_conflict",
            message="Paper job conflicts with an existing job",
        )
    elif isinstance(exc, PaperJobStateConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_state_conflict",
            message="Paper job state conflicts with the requested operation",
        )
    elif isinstance(exc, PaperJobOutputConflictError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_output_conflict",
            message="Paper job output conflicts with an existing file",
        )
    elif isinstance(exc, PaperJobRecoveryError):
        error = PublicApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="paper_job_recovery_failed",
            message="Paper job recovery inspection failed",
        )
    elif isinstance(exc, PaperJobResultUnavailableError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_result_unavailable",
            message="Paper job result is unavailable",
        )
    elif isinstance(exc, PaperJobResultInvalidError):
        error = PublicApiError(
            status_code=HTTPStatus.CONFLICT,
            code="paper_job_result_invalid",
            message="Paper job result is invalid",
        )
    elif isinstance(exc, PaperArtifactRootUnavailableError):
        raise paper_artifact_root_unavailable() from exc
    else:
        raise exc
    raise error from exc


def _attempt_response(attempt: PaperJobAttemptRecord) -> PaperJobAttemptResponse:
    return PaperJobAttemptResponse(
        attempt_id=attempt.attempt_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_timestamp=attempt.started_timestamp,
        completed_timestamp=attempt.completed_timestamp,
        error_code=attempt.error_code,
    )


def _job_response(view: PaperJobStatusView) -> PaperJobResponse:
    job = view.job
    return PaperJobResponse(
        job_id=job.job_id,
        run_id=job.run_id,
        status=job.status,
        submitted_timestamp=job.submitted_timestamp,
        updated_timestamp=job.updated_timestamp,
        attempt_count=view.attempt_count,
        latest_attempt=(
            None if view.latest_attempt is None else _attempt_response(view.latest_attempt)
        ),
        result_available=view.result_available,
        result_url=(
            f"/api/v1/paper-jobs/{job.job_id}/result"
            if view.result_available
            else None
        ),
    )


def _result_response(view: PaperJobResultView) -> PaperJobResultResponse:
    reference = view.result_reference
    summary = view.result_summary
    audit = summary.audit
    return PaperJobResultResponse(
        job_id=view.job_id,
        run_id=view.run_id,
        result_reference=PaperJobResultReferenceResponse(
            record_schema_version=reference.record_schema_version,
            root_type=reference.root_type,
            artifact_schema_version=reference.artifact_schema_version,
            result_summary_schema_version=reference.result_summary_schema_version,
            created_timestamp=reference.created_timestamp,
        ),
        artifact=paper_trading_artifact_response(view.artifact),
        result_summary=PaperJobResultSummaryResponse(
            schema_version=summary.schema_version,
            run_id=summary.run_id,
            request_schema_version=summary.request_schema_version,
            request_created_timestamp=summary.request_created_timestamp,
            artifact_schema_version=summary.artifact_schema_version,
            artifact_created_timestamp=summary.artifact_created_timestamp,
            audit=PaperJobResultAuditResponse(
                schema_version=audit.schema_version,
                created_timestamp=audit.created_timestamp,
                session_start_timestamp=audit.session_start_timestamp,
                session_end_timestamp=audit.session_end_timestamp,
                starting_cash=audit.starting_cash,
                ending_cash=audit.ending_cash,
                cash_change=audit.cash_change,
                order_count=audit.order_count,
                fill_count=audit.fill_count,
                starting_position_count=audit.starting_position_count,
                ending_position_count=audit.ending_position_count,
                position_change_count=audit.position_change_count,
            ),
        ),
    )


def _status_after(
    *, session_factory: sessionmaker[Session], job_id: str
) -> PaperJobResponse:
    return _job_response(
        get_paper_job_status_view(session_factory=session_factory, job_id=job_id)
    )


def _run_selected_job(
    *,
    session_factory: sessionmaker[Session],
    claim: PaperJobClaim,
) -> None:
    try:
        execute_claimed_product_paper_job(
            session_factory=session_factory,
            claim=claim,
        )
    except (
        PaperArtifactRootUnavailableError,
        PaperJobExecutionError,
        PaperJobNotFoundError,
        PaperJobOutputConflictError,
        PaperJobStateConflictError,
    ):
        return


@router.post("", response_model=PaperJobSubmissionResponse)
def post_paper_job(
    request: PaperRunCommandRequest,
    session_factory: SessionFactory,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaperJobSubmissionResponse:
    """Durably submit or exactly replay one queued paper job without execution."""
    try:
        result = submit_paper_job_with_outcome(
            session_factory=session_factory,
            command=paper_run_command_from_request(request),
            idempotency_key=idempotency_key,
        )
        return PaperJobSubmissionResponse(
            submission_outcome=result.outcome,
            job=_status_after(
                session_factory=session_factory,
                job_id=result.job.job_id,
            ),
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get("", response_model=list[PaperJobResponse])
def get_paper_jobs(
    session_factory: SessionFactory,
    status: Annotated[JobStatusFilter | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PaperJobResponse]:
    """Return a bounded deterministic database-only job list."""
    try:
        return [
            _job_response(view)
            for view in list_paper_job_status_views(
                session_factory=session_factory,
                status=status,
                limit=limit,
            )
        ]
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get("/{job_id}", response_model=PaperJobResponse)
def get_paper_job_detail(
    job_id: str,
    session_factory: SessionFactory,
) -> PaperJobResponse:
    try:
        return _status_after(session_factory=session_factory, job_id=job_id)
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get("/{job_id}/attempts", response_model=list[PaperJobAttemptResponse])
def get_paper_job_attempts(
    job_id: str,
    session_factory: SessionFactory,
) -> list[PaperJobAttemptResponse]:
    try:
        return [
            _attempt_response(attempt)
            for attempt in list_paper_job_attempts(
                session_factory=session_factory,
                job_id=job_id,
            )
        ]
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.post(
    "/{job_id}/run",
    response_model=PaperJobResponse,
    status_code=HTTPStatus.ACCEPTED,
)
def run_paper_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    session_factory: SessionFactory,
    paper_artifact_root: PaperRoot,
) -> PaperJobResponse:
    try:
        claim = claim_product_paper_job(
            session_factory=session_factory,
            job_id=job_id,
            paper_artifact_root=paper_artifact_root,
        )
        response = _status_after(
            session_factory=session_factory,
            job_id=claim.job.job_id,
        )
        background_tasks.add_task(
            _run_selected_job,
            session_factory=session_factory,
            claim=claim,
        )
        return response
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.post("/{job_id}/cancel", response_model=PaperJobResponse)
def cancel_paper_job_route(
    job_id: str,
    session_factory: SessionFactory,
) -> PaperJobResponse:
    try:
        job = cancel_paper_job(session_factory=session_factory, job_id=job_id)
        return _status_after(session_factory=session_factory, job_id=job.job_id)
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.post("/{job_id}/retry", response_model=PaperJobResponse)
def retry_paper_job_route(
    job_id: str,
    session_factory: SessionFactory,
    paper_artifact_root: PaperRoot,
) -> PaperJobResponse:
    try:
        job = retry_product_paper_job(
            session_factory=session_factory,
            job_id=job_id,
            paper_artifact_root=paper_artifact_root,
        )
        return _status_after(session_factory=session_factory, job_id=job.job_id)
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.post("/{job_id}/recover", response_model=PaperJobRecoveryResponse)
def recover_paper_job_route(
    job_id: str,
    request: PaperJobRecoveryRequest,
    session_factory: SessionFactory,
    paper_artifact_root: PaperRoot,
) -> PaperJobRecoveryResponse:
    try:
        result = recover_product_paper_job(
            session_factory=session_factory,
            job_id=job_id,
            paper_artifact_root=paper_artifact_root,
            stale_before=request.stale_before,
        )
        return PaperJobRecoveryResponse(
            recovery_outcome=result.outcome,
            job=_status_after(
                session_factory=session_factory,
                job_id=result.job.job_id,
            ),
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get("/{job_id}/result", response_model=PaperJobResultResponse)
def get_paper_job_result(
    job_id: str,
    session_factory: SessionFactory,
    paper_artifact_root: PaperRoot,
) -> PaperJobResultResponse:
    try:
        return _result_response(
            read_paper_job_result(
                session_factory=session_factory,
                job_id=job_id,
                paper_artifact_root=paper_artifact_root,
            )
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)
