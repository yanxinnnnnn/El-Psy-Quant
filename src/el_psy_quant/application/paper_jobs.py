"""Explicit durable paper-job submission, execution, recovery, and control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, TypeAlias
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.paper_runs import (
    PaperRunCommand,
    PaperTradingArtifactView,
    create_paper_run_request_from_command,
    paper_trading_artifact_view_from_payload,
)
from el_psy_quant.configured_paper import (
    PaperWorkflowRunResult,
    run_paper_workflow_request,
)
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.paper import (
    read_paper_run_result_summary_file,
    read_paper_trading_artifact_file,
    validate_paper_run_recovery_consistency,
)
from el_psy_quant.persistence import (
    PaperJobAttemptRecord,
    PaperJobAttemptStatus,
    PaperJobErrorCode,
    PaperJobRecord,
    PaperJobResultReference,
    PaperJobStatus,
    SqlAlchemyPaperJobAttemptRepository,
    SqlAlchemyPaperJobRepository,
    SqlAlchemyPaperJobResultReferenceRepository,
    SqlAlchemyPaperJobSubmissionKeyRepository,
    create_paper_job_submission_key_record,
    create_paper_job_result_reference,
    create_queued_paper_job_record,
    create_running_paper_job_attempt,
    digest_prepared_paper_run_request,
    prepare_paper_run_request_for_persistence,
    validate_paper_job_idempotency_key,
)


class PaperJobConflictError(Exception):
    """Sanitized conflict for a duplicate durable job or run identity."""

    def __init__(self) -> None:
        super().__init__("paper job conflicts with an existing identity")


class PaperJobIdempotencyConflictError(Exception):
    """Sanitized conflict for a caller key reused with another request."""

    def __init__(self) -> None:
        super().__init__("paper job idempotency key conflicts with another request")


class PaperJobNotFoundError(Exception):
    """Sanitized absence of an exact durable paper job."""

    def __init__(self) -> None:
        super().__init__("paper job not found")


class PaperJobStateConflictError(Exception):
    """Sanitized conflict between current and requested operational state."""

    def __init__(self) -> None:
        super().__init__("paper job state conflicts with the requested operation")


class PaperJobOutputConflictError(Exception):
    """Sanitized conflict with a reserved durable-run output file."""

    def __init__(self) -> None:
        super().__init__("paper job output conflicts with an existing file")


class PaperJobExecutionError(Exception):
    """Sanitized expected local paper workflow failure."""

    def __init__(self) -> None:
        super().__init__("paper job execution failed")


class PaperJobRecoveryError(Exception):
    """Sanitized uncertainty while inspecting interrupted-job outputs."""

    def __init__(self) -> None:
        super().__init__("paper job recovery inspection failed")


class PaperJobResultUnavailableError(Exception):
    """Sanitized absence of an authoritative result for a durable job."""

    def __init__(self) -> None:
        super().__init__("paper job result is unavailable")


class PaperJobResultInvalidError(Exception):
    """Sanitized invalidity of referenced authoritative result files."""

    def __init__(self) -> None:
        super().__init__("paper job result is invalid")


class PaperArtifactRootUnavailableError(Exception):
    """Sanitized unavailable configured paper artifact root."""

    def __init__(self) -> None:
        super().__init__("paper artifact root is unavailable")


@dataclass(frozen=True)
class PaperJobRunResult:
    """Succeeded durable job and its authoritative file workflow result."""

    job: PaperJobRecord
    attempt: PaperJobAttemptRecord
    workflow: PaperWorkflowRunResult


PaperJobRecoveryOutcome: TypeAlias = Literal["requeued", "succeeded", "failed"]


@dataclass(frozen=True)
class PaperJobRecoveryResult:
    """Deterministic manual reconciliation result for one interrupted job."""

    outcome: PaperJobRecoveryOutcome
    job: PaperJobRecord
    attempt: PaperJobAttemptRecord


@dataclass(frozen=True)
class PaperJobStatusView:
    """Compact database-only operational view for one paper job."""

    job: PaperJobRecord
    attempt_count: int
    latest_attempt: PaperJobAttemptRecord | None
    result_available: bool


@dataclass(frozen=True)
class PaperJobResultReferenceView:
    record_schema_version: Literal[1]
    root_type: Literal["paper"]
    artifact_schema_version: Literal[1]
    result_summary_schema_version: Literal[1]
    created_timestamp: datetime


@dataclass(frozen=True)
class PaperJobResultAuditView:
    schema_version: int
    created_timestamp: str
    session_start_timestamp: str
    session_end_timestamp: str
    starting_cash: float
    ending_cash: float
    cash_change: float
    order_count: int
    fill_count: int
    starting_position_count: int
    ending_position_count: int
    position_change_count: int


@dataclass(frozen=True)
class PaperJobResultSummaryView:
    schema_version: Literal[1]
    run_id: str
    request_schema_version: Literal[1]
    request_created_timestamp: str
    artifact_schema_version: Literal[1]
    artifact_created_timestamp: str
    audit: PaperJobResultAuditView


@dataclass(frozen=True)
class PaperJobResultView:
    job_id: str
    run_id: str
    result_reference: PaperJobResultReferenceView
    artifact: PaperTradingArtifactView
    result_summary: PaperJobResultSummaryView


ResultReferenceFactory: TypeAlias = Callable[[datetime], PaperJobResultReference]


def _new_job_id() -> str:
    return str(uuid4())


def _new_attempt_id() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_job_id(job_id: str) -> str:
    if not isinstance(job_id, str):
        raise ValueError("job_id must be a canonical UUID string")
    try:
        parsed = UUID(job_id)
    except (AttributeError, ValueError) as exc:
        raise ValueError("job_id must be a canonical UUID string") from exc
    if str(parsed) != job_id:
        raise ValueError("job_id must be a canonical UUID string")
    return job_id


def _validate_utc_timestamp(value: object, *, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a timezone-aware UTC datetime"
        ) from exc
    if offset is None or offset.total_seconds() != 0:
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    return value.astimezone(timezone.utc)


def _validate_run_dir(run_dir: str | Path) -> Path:
    if isinstance(run_dir, str) and not run_dir.strip():
        raise ValueError("run_dir must be a non-empty path")
    if not isinstance(run_dir, (str, Path)):
        raise ValueError("run_dir must be a string or Path")
    path = Path(run_dir)
    if not path.exists():
        raise ValueError("run_dir must already exist")
    if not path.is_dir():
        raise ValueError("run_dir must be a directory")
    return path


def _validate_paper_artifact_root(root: str | Path) -> Path:
    if isinstance(root, str) and not root.strip():
        raise PaperArtifactRootUnavailableError()
    if not isinstance(root, (str, Path)):
        raise PaperArtifactRootUnavailableError()
    try:
        path = Path(root)
        if not path.exists() or not path.is_dir():
            raise PaperArtifactRootUnavailableError()
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PaperArtifactRootUnavailableError() from exc


def _contained_directory(*, root: Path, path: Path, create: bool) -> Path:
    try:
        if create:
            path.mkdir(exist_ok=True)
        if not path.exists() or not path.is_dir() or path.is_symlink():
            raise PaperArtifactRootUnavailableError()
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except PaperArtifactRootUnavailableError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise PaperArtifactRootUnavailableError() from exc


def _product_paper_job_run_dir(
    *,
    paper_artifact_root: str | Path,
    job_id: str,
    create: bool,
) -> Path:
    validated_job_id = _validate_job_id(job_id)
    root = _validate_paper_artifact_root(paper_artifact_root)
    jobs = _contained_directory(root=root, path=root / "jobs", create=create)
    run_dir = _contained_directory(
        root=root,
        path=jobs / validated_job_id,
        create=create,
    )
    _contained_directory(root=root, path=run_dir / "paper", create=create)
    return run_dir


def validate_paper_artifact_root(root: str | Path) -> Path:
    """Validate an existing server-owned paper root without creating anything."""
    return _validate_paper_artifact_root(root)


def _preflight_run_dir(run_dir: str | Path) -> Path:
    path = _validate_run_dir(run_dir)
    paths = create_configured_paper_run_output_paths(run_dir=path)
    if (
        paths.paper_run_artifact_path.exists()
        or paths.paper_run_result_summary_path.exists()
    ):
        raise PaperJobOutputConflictError()
    return path


def _raise_transition_conflict(
    *,
    repository: SqlAlchemyPaperJobRepository,
    job_id: str,
) -> None:
    if repository.get(job_id=job_id) is None:
        raise PaperJobNotFoundError()
    raise PaperJobStateConflictError()


def _transition_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    expected_status: PaperJobStatus,
    target_status: PaperJobStatus,
) -> PaperJobRecord:
    with session_factory.begin() as session:
        repository = SqlAlchemyPaperJobRepository(session=session)
        transitioned = repository.transition_status(
            job_id=job_id,
            expected_status=expected_status,
            target_status=target_status,
            updated_timestamp=_utc_now(),
        )
        if transitioned is None:
            _raise_transition_conflict(repository=repository, job_id=job_id)
        return transitioned


def _claim_job_and_attempt(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> tuple[PaperJobRecord, PaperJobAttemptRecord]:
    timestamp = _utc_now()
    with session_factory.begin() as session:
        jobs = SqlAlchemyPaperJobRepository(session=session)
        running_job = jobs.transition_status(
            job_id=job_id,
            expected_status="queued",
            target_status="running",
            updated_timestamp=timestamp,
        )
        if running_job is None:
            _raise_transition_conflict(repository=jobs, job_id=job_id)
        attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
        attempt = create_running_paper_job_attempt(
            attempt_id=_new_attempt_id(),
            job_id=job_id,
            attempt_number=attempts.next_attempt_number(job_id=job_id),
            started_timestamp=timestamp,
        )
        attempts.start_attempt(attempt=attempt)
        return running_job, attempt


def _complete_job_and_attempt(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    attempt_id: str,
    job_status: Literal["succeeded", "failed"],
    attempt_status: Literal["succeeded", "failed"],
    error_code: PaperJobErrorCode | None = None,
    result_reference_factory: ResultReferenceFactory | None = None,
) -> tuple[PaperJobRecord, PaperJobAttemptRecord]:
    timestamp = _utc_now()
    with session_factory.begin() as session:
        jobs = SqlAlchemyPaperJobRepository(session=session)
        job = jobs.transition_status(
            job_id=job_id,
            expected_status="running",
            target_status=job_status,
            updated_timestamp=timestamp,
        )
        if job is None:
            _raise_transition_conflict(repository=jobs, job_id=job_id)
        attempt = SqlAlchemyPaperJobAttemptRepository(
            session=session
        ).complete_attempt(
            attempt_id=attempt_id,
            status=attempt_status,
            completed_timestamp=timestamp,
            error_code=error_code,
        )
        if attempt is None:
            raise PaperJobStateConflictError()
        if result_reference_factory is not None:
            SqlAlchemyPaperJobResultReferenceRepository(session=session).add(
                reference=result_reference_factory(timestamp)
            )
        return job, attempt


def _classify_execution_error(exc: ValueError | OSError) -> PaperJobErrorCode:
    if isinstance(exc, FileExistsError):
        return "output_conflict"
    if isinstance(exc, OSError):
        return "filesystem_io_failed"
    return "workflow_validation_failed"


def _run_paper_job_once(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
    result_reference_factory: ResultReferenceFactory | None,
) -> PaperJobRunResult:
    """Claim and execute one explicitly selected queued paper job once."""
    validated_job_id = _validate_job_id(job_id)
    validated_run_dir = _preflight_run_dir(run_dir)
    running_job, running_attempt = _claim_job_and_attempt(
        session_factory=session_factory,
        job_id=validated_job_id,
    )

    try:
        workflow = run_paper_workflow_request(
            request=running_job.request,
            run_dir=validated_run_dir,
            output_write_mode="exclusive",
        )
    except (ValueError, OSError) as exc:
        _complete_job_and_attempt(
            session_factory=session_factory,
            job_id=validated_job_id,
            attempt_id=running_attempt.attempt_id,
            job_status="failed",
            attempt_status="failed",
            error_code=_classify_execution_error(exc),
        )
        raise PaperJobExecutionError() from exc

    succeeded_job, succeeded_attempt = _complete_job_and_attempt(
        session_factory=session_factory,
        job_id=validated_job_id,
        attempt_id=running_attempt.attempt_id,
        job_status="succeeded",
        attempt_status="succeeded",
        result_reference_factory=result_reference_factory,
    )
    return PaperJobRunResult(
        job=succeeded_job,
        attempt=succeeded_attempt,
        workflow=workflow,
    )


def run_paper_job_once(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
) -> PaperJobRunResult:
    """Run one manual operator-owned job without product reference registration."""
    return _run_paper_job_once(
        session_factory=session_factory,
        job_id=job_id,
        run_dir=run_dir,
        result_reference_factory=None,
    )


def run_product_paper_job_once(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    paper_artifact_root: str | Path,
) -> PaperJobRunResult:
    """Run one selected job in the server-owned layout with atomic registration."""
    validated_job_id = _validate_job_id(job_id)
    run_dir = _product_paper_job_run_dir(
        paper_artifact_root=paper_artifact_root,
        job_id=validated_job_id,
        create=True,
    )
    return _run_paper_job_once(
        session_factory=session_factory,
        job_id=validated_job_id,
        run_dir=run_dir,
        result_reference_factory=lambda timestamp: create_paper_job_result_reference(
            job_id=validated_job_id,
            created_timestamp=timestamp,
        ),
    )


def cancel_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> PaperJobRecord:
    """Cancel one queued job without executing or touching files."""
    return _transition_job(
        session_factory=session_factory,
        job_id=_validate_job_id(job_id),
        expected_status="queued",
        target_status="canceled",
    )


def _replay_job(
    *,
    session: Session,
    idempotency_key: str,
    request_digest: str,
) -> PaperJobRecord | None:
    mapping = SqlAlchemyPaperJobSubmissionKeyRepository(
        session=session
    ).get_by_key(idempotency_key=idempotency_key)
    if mapping is None:
        return None
    if mapping.request_digest != request_digest:
        raise PaperJobIdempotencyConflictError()
    job = SqlAlchemyPaperJobRepository(session=session).get(job_id=mapping.job_id)
    if job is None:
        raise RuntimeError("submission key references a missing paper job")
    return job


def submit_paper_job(
    *,
    session_factory: sessionmaker[Session],
    command: PaperRunCommand,
    idempotency_key: str | None = None,
) -> PaperJobRecord:
    """Validate and durably enqueue or replay one paper job."""
    request = create_paper_run_request_from_command(command=command)
    prepared_request = prepare_paper_run_request_for_persistence(request)
    request_digest = digest_prepared_paper_run_request(prepared_request)
    validated_key = (
        None
        if idempotency_key is None
        else validate_paper_job_idempotency_key(idempotency_key)
    )
    try:
        with session_factory.begin() as session:
            if validated_key is not None:
                replay = _replay_job(
                    session=session,
                    idempotency_key=validated_key,
                    request_digest=request_digest,
                )
                if replay is not None:
                    return replay
            timestamp = _utc_now()
            job = create_queued_paper_job_record(
                job_id=_new_job_id(),
                request=request,
                submitted_timestamp=timestamp,
            )
            SqlAlchemyPaperJobRepository(session=session).add(
                job=job,
                prepared_request=prepared_request,
            )
            if validated_key is not None:
                SqlAlchemyPaperJobSubmissionKeyRepository(session=session).add(
                    record=create_paper_job_submission_key_record(
                        idempotency_key=validated_key,
                        job_id=job.job_id,
                        request_digest=request_digest,
                        created_timestamp=timestamp,
                    )
                )
            return job
    except IntegrityError as exc:
        if validated_key is not None:
            with session_factory() as session:
                replay = _replay_job(
                    session=session,
                    idempotency_key=validated_key,
                    request_digest=request_digest,
                )
            if replay is not None:
                return replay
        raise PaperJobConflictError() from exc


def get_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> PaperJobRecord:
    """Get one exact durable job without executing or inspecting artifacts."""
    with session_factory() as session:
        job = SqlAlchemyPaperJobRepository(session=session).get(job_id=job_id)
    if job is None:
        raise PaperJobNotFoundError()
    return job


def get_paper_job_by_run_id(
    *,
    session_factory: sessionmaker[Session],
    run_id: str,
) -> PaperJobRecord:
    """Get one exact durable job by its unique paper-run identity."""
    with session_factory() as session:
        job = SqlAlchemyPaperJobRepository(session=session).get_by_run_id(run_id=run_id)
    if job is None:
        raise PaperJobNotFoundError()
    return job


def get_paper_job_by_idempotency_key(
    *,
    session_factory: sessionmaker[Session],
    idempotency_key: str,
) -> PaperJobRecord:
    """Get the original job for one exact caller idempotency key."""
    validated_key = validate_paper_job_idempotency_key(idempotency_key)
    with session_factory() as session:
        mapping = SqlAlchemyPaperJobSubmissionKeyRepository(
            session=session
        ).get_by_key(idempotency_key=validated_key)
        job = (
            None
            if mapping is None
            else SqlAlchemyPaperJobRepository(session=session).get(
                job_id=mapping.job_id
            )
        )
    if job is None:
        raise PaperJobNotFoundError()
    return job


def list_paper_jobs(
    *,
    session_factory: sessionmaker[Session],
    status: str | None = None,
    limit: int | None = None,
) -> tuple[PaperJobRecord, ...]:
    """List durable jobs deterministically without executing them."""
    with session_factory() as session:
        return SqlAlchemyPaperJobRepository(session=session).list(
            status=status,
            limit=limit,
        )


def _status_view(
    *,
    session: Session,
    job: PaperJobRecord,
) -> PaperJobStatusView:
    attempts = SqlAlchemyPaperJobAttemptRepository(session=session).list_for_job(
        job_id=job.job_id
    )
    reference = SqlAlchemyPaperJobResultReferenceRepository(
        session=session
    ).get_by_job_id(job_id=job.job_id)
    return PaperJobStatusView(
        job=job,
        attempt_count=len(attempts),
        latest_attempt=None if not attempts else attempts[-1],
        result_available=reference is not None,
    )


def get_paper_job_status_view(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> PaperJobStatusView:
    """Read compact job, attempt, and reference metadata from SQLite only."""
    validated_job_id = _validate_job_id(job_id)
    with session_factory() as session:
        job = SqlAlchemyPaperJobRepository(session=session).get(
            job_id=validated_job_id
        )
        if job is None:
            raise PaperJobNotFoundError()
        return _status_view(session=session, job=job)


def list_paper_job_status_views(
    *,
    session_factory: sessionmaker[Session],
    status: str | None = None,
    limit: int = 50,
) -> tuple[PaperJobStatusView, ...]:
    """Read a bounded deterministic compact job list from SQLite only."""
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    with session_factory() as session:
        jobs = SqlAlchemyPaperJobRepository(session=session).list(
            status=status,
            limit=limit,
        )
        return tuple(_status_view(session=session, job=job) for job in jobs)


def get_paper_job_result_reference(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> PaperJobResultReference | None:
    """Read only the optional compact product result pointer from SQLite."""
    validated_job_id = _validate_job_id(job_id)
    with session_factory() as session:
        return SqlAlchemyPaperJobResultReferenceRepository(
            session=session
        ).get_by_job_id(job_id=validated_job_id)


def list_paper_job_attempts(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
) -> tuple[PaperJobAttemptRecord, ...]:
    """List one exact job's compact attempt audit by attempt number."""
    validated_job_id = _validate_job_id(job_id)
    with session_factory() as session:
        if SqlAlchemyPaperJobRepository(session=session).get(
            job_id=validated_job_id
        ) is None:
            raise PaperJobNotFoundError()
        return SqlAlchemyPaperJobAttemptRepository(session=session).list_for_job(
            job_id=validated_job_id
        )


def _path_exists(path: Path) -> bool:
    try:
        path.stat()
    except FileNotFoundError:
        return False
    return True


def _inspect_recovery_outputs(
    *,
    job: PaperJobRecord,
    run_dir: Path,
) -> tuple[
    PaperJobRecoveryOutcome,
    PaperJobStatus,
    PaperJobAttemptStatus,
    PaperJobErrorCode | None,
]:
    paths = create_configured_paper_run_output_paths(run_dir=run_dir)
    artifact_exists = _path_exists(paths.paper_run_artifact_path)
    summary_exists = _path_exists(paths.paper_run_result_summary_path)
    if not artifact_exists and not summary_exists:
        return "requeued", "queued", "interrupted", "interrupted_without_output"
    if artifact_exists != summary_exists:
        return "failed", "failed", "failed", "partial_output_detected"
    try:
        artifact = read_paper_trading_artifact_file(paths.paper_run_artifact_path)
        summary = read_paper_run_result_summary_file(
            paths.paper_run_result_summary_path
        )
        validate_paper_run_recovery_consistency(
            request=job.request,
            artifact_payload=artifact,
            summary=summary,
            expected_artifact_path=paths.paper_run_artifact_path,
        )
    except ValueError as exc:
        if not _path_exists(paths.paper_run_artifact_path) or not _path_exists(
            paths.paper_run_result_summary_path
        ):
            raise OSError("paper job recovery outputs changed during inspection") from exc
        return "failed", "failed", "failed", "invalid_output_detected"
    return "succeeded", "succeeded", "succeeded", None


def _finalize_recovery(
    *,
    session_factory: sessionmaker[Session],
    observed_job: PaperJobRecord,
    outcome: PaperJobRecoveryOutcome,
    job_status: PaperJobStatus,
    attempt_status: PaperJobAttemptStatus,
    error_code: PaperJobErrorCode | None,
    result_reference_factory: ResultReferenceFactory | None,
) -> PaperJobRecoveryResult:
    timestamp = _utc_now()
    with session_factory.begin() as session:
        jobs = SqlAlchemyPaperJobRepository(session=session)
        job = jobs.transition_status(
            job_id=observed_job.job_id,
            expected_status="running",
            target_status=job_status,
            updated_timestamp=timestamp,
            expected_updated_timestamp=observed_job.updated_timestamp,
        )
        if job is None:
            _raise_transition_conflict(repository=jobs, job_id=observed_job.job_id)
        attempts = SqlAlchemyPaperJobAttemptRepository(session=session)
        existing_attempts = attempts.list_for_job(job_id=observed_job.job_id)
        running_attempts = tuple(
            attempt for attempt in existing_attempts if attempt.status == "running"
        )
        if len(running_attempts) == 1:
            running_attempt = running_attempts[0]
        elif not existing_attempts:
            running_attempt = attempts.start_attempt(
                attempt=create_running_paper_job_attempt(
                    attempt_id=_new_attempt_id(),
                    job_id=observed_job.job_id,
                    attempt_number=attempts.next_attempt_number(
                        job_id=observed_job.job_id
                    ),
                    started_timestamp=observed_job.updated_timestamp,
                )
            )
        else:
            raise PaperJobStateConflictError()
        completed_attempt = attempts.complete_attempt(
            attempt_id=running_attempt.attempt_id,
            status=attempt_status,
            completed_timestamp=timestamp,
            error_code=error_code,
        )
        if completed_attempt is None:
            raise PaperJobStateConflictError()
        if outcome == "succeeded" and result_reference_factory is not None:
            SqlAlchemyPaperJobResultReferenceRepository(session=session).add(
                reference=result_reference_factory(timestamp)
            )
        return PaperJobRecoveryResult(
            outcome=outcome,
            job=job,
            attempt=completed_attempt,
        )


def _recover_interrupted_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
    stale_before: datetime,
    result_reference_factory: ResultReferenceFactory | None,
) -> PaperJobRecoveryResult:
    """Explicitly reconcile one operator-asserted interrupted running job."""
    validated_job_id = _validate_job_id(job_id)
    validated_run_dir = _validate_run_dir(run_dir)
    validated_stale_before = _validate_utc_timestamp(
        stale_before,
        field_name="stale_before",
    )
    with session_factory() as session:
        observed_job = SqlAlchemyPaperJobRepository(session=session).get(
            job_id=validated_job_id
        )
    if observed_job is None:
        raise PaperJobNotFoundError()
    if (
        observed_job.status != "running"
        or observed_job.updated_timestamp > validated_stale_before
    ):
        raise PaperJobStateConflictError()
    try:
        outcome, job_status, attempt_status, error_code = _inspect_recovery_outputs(
            job=observed_job,
            run_dir=validated_run_dir,
        )
    except OSError as exc:
        raise PaperJobRecoveryError() from exc
    return _finalize_recovery(
        session_factory=session_factory,
        observed_job=observed_job,
        outcome=outcome,
        job_status=job_status,
        attempt_status=attempt_status,
        error_code=error_code,
        result_reference_factory=result_reference_factory,
    )


def recover_interrupted_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
    stale_before: datetime,
) -> PaperJobRecoveryResult:
    """Recover one manual operator-owned job without product registration."""
    return _recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=job_id,
        run_dir=run_dir,
        stale_before=stale_before,
        result_reference_factory=None,
    )


def recover_product_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    paper_artifact_root: str | Path,
    stale_before: datetime,
) -> PaperJobRecoveryResult:
    """Recover one API-owned job and atomically register valid outputs."""
    validated_job_id = _validate_job_id(job_id)
    observed = get_paper_job(
        session_factory=session_factory,
        job_id=validated_job_id,
    )
    validated_stale_before = _validate_utc_timestamp(
        stale_before,
        field_name="stale_before",
    )
    if (
        observed.status != "running"
        or observed.updated_timestamp > validated_stale_before
    ):
        raise PaperJobStateConflictError()
    run_dir = _product_paper_job_run_dir(
        paper_artifact_root=paper_artifact_root,
        job_id=validated_job_id,
        create=False,
    )
    return _recover_interrupted_paper_job(
        session_factory=session_factory,
        job_id=validated_job_id,
        run_dir=run_dir,
        stale_before=validated_stale_before,
        result_reference_factory=lambda timestamp: create_paper_job_result_reference(
            job_id=validated_job_id,
            created_timestamp=timestamp,
        ),
    )


def retry_failed_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
) -> PaperJobRecord:
    """Explicitly requeue one failed job after clean-output preflight."""
    validated_run_dir = _preflight_run_dir(run_dir)
    del validated_run_dir
    return _transition_job(
        session_factory=session_factory,
        job_id=_validate_job_id(job_id),
        expected_status="failed",
        target_status="queued",
    )


def retry_product_paper_job(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    paper_artifact_root: str | Path,
) -> PaperJobRecord:
    """Retry one API-owned failed job using its fixed server-owned directory."""
    validated_job_id = _validate_job_id(job_id)
    if get_paper_job(
        session_factory=session_factory,
        job_id=validated_job_id,
    ).status != "failed":
        raise PaperJobStateConflictError()
    run_dir = _product_paper_job_run_dir(
        paper_artifact_root=paper_artifact_root,
        job_id=validated_job_id,
        create=False,
    )
    return retry_failed_paper_job(
        session_factory=session_factory,
        job_id=validated_job_id,
        run_dir=run_dir,
    )


def _resolve_result_file(*, root: Path, relative_path: str) -> Path:
    try:
        candidate = root.joinpath(*relative_path.split("/"))
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file() or candidate.is_symlink():
            raise ValueError("paper job result file is unavailable")
        return resolved
    except (OSError, RuntimeError, ValueError) as exc:
        raise PaperJobResultInvalidError() from exc


def _reference_view(
    reference: PaperJobResultReference,
) -> PaperJobResultReferenceView:
    return PaperJobResultReferenceView(
        record_schema_version=reference.record_schema_version,
        root_type=reference.root_type,
        artifact_schema_version=reference.artifact_schema_version,
        result_summary_schema_version=reference.result_summary_schema_version,
        created_timestamp=reference.created_timestamp,
    )


def read_paper_job_result(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    paper_artifact_root: str | Path,
) -> PaperJobResultView:
    """Read referenced authoritative files only after closing the DB session."""
    validated_job_id = _validate_job_id(job_id)
    root = _validate_paper_artifact_root(paper_artifact_root)
    try:
        with session_factory() as session:
            job = SqlAlchemyPaperJobRepository(session=session).get(
                job_id=validated_job_id
            )
            reference = SqlAlchemyPaperJobResultReferenceRepository(
                session=session
            ).get_by_job_id(job_id=validated_job_id)
    except ValueError as exc:
        raise PaperJobResultInvalidError() from exc
    if job is None:
        raise PaperJobNotFoundError()
    if job.status != "succeeded" or reference is None:
        raise PaperJobResultUnavailableError()

    artifact_path = _resolve_result_file(
        root=root,
        relative_path=reference.artifact_relative_path,
    )
    summary_path = _resolve_result_file(
        root=root,
        relative_path=reference.result_summary_relative_path,
    )
    try:
        artifact_payload = read_paper_trading_artifact_file(artifact_path)
        summary = read_paper_run_result_summary_file(summary_path)
        validate_paper_run_recovery_consistency(
            request=job.request,
            artifact_payload=artifact_payload,
            summary=summary,
            expected_artifact_path=artifact_path,
        )
        artifact_view = paper_trading_artifact_view_from_payload(artifact_payload)
    except (OSError, ValueError) as exc:
        raise PaperJobResultInvalidError() from exc
    audit = summary.audit_summary
    return PaperJobResultView(
        job_id=job.job_id,
        run_id=job.run_id,
        result_reference=_reference_view(reference),
        artifact=artifact_view,
        result_summary=PaperJobResultSummaryView(
            schema_version=summary.schema_version,
            run_id=summary.run_id,
            request_schema_version=summary.request_schema_version,
            request_created_timestamp=summary.request_created_timestamp,
            artifact_schema_version=summary.artifact_schema_version,
            artifact_created_timestamp=summary.artifact_created_timestamp,
            audit=PaperJobResultAuditView(
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
