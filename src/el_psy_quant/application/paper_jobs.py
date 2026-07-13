"""Explicit durable paper-job submission, reads, execution, and control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.paper_runs import (
    PaperRunCommand,
    create_paper_run_request_from_command,
)
from el_psy_quant.configured_paper import (
    PaperWorkflowRunResult,
    run_paper_workflow_request,
)
from el_psy_quant.outputs import create_configured_paper_run_output_paths
from el_psy_quant.persistence import (
    PaperJobRecord,
    PaperJobStatus,
    SqlAlchemyPaperJobRepository,
    create_queued_paper_job_record,
    prepare_paper_run_request_for_persistence,
)


class PaperJobConflictError(Exception):
    """Sanitized conflict for a duplicate durable job or run identity."""

    def __init__(self) -> None:
        super().__init__("paper job conflicts with an existing identity")


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


@dataclass(frozen=True)
class PaperJobRunResult:
    """Succeeded durable job and its authoritative file workflow result."""

    job: PaperJobRecord
    workflow: PaperWorkflowRunResult


def _new_job_id() -> str:
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


def _preflight_run_dir(run_dir: str | Path) -> Path:
    if isinstance(run_dir, str) and not run_dir.strip():
        raise ValueError("run_dir must be a non-empty path")
    if not isinstance(run_dir, (str, Path)):
        raise ValueError("run_dir must be a string or Path")
    path = Path(run_dir)
    if not path.exists():
        raise ValueError("run_dir must already exist")
    if not path.is_dir():
        raise ValueError("run_dir must be a directory")
    paths = create_configured_paper_run_output_paths(run_dir=path)
    if (
        paths.paper_run_artifact_path.exists()
        or paths.paper_run_result_summary_path.exists()
    ):
        raise PaperJobOutputConflictError()
    return path


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
        if transitioned is not None:
            return transitioned
        current = repository.get(job_id=job_id)
        if current is None:
            raise PaperJobNotFoundError()
        raise PaperJobStateConflictError()


def run_paper_job_once(
    *,
    session_factory: sessionmaker[Session],
    job_id: str,
    run_dir: str | Path,
) -> PaperJobRunResult:
    """Claim and execute one explicitly selected queued paper job once."""
    validated_job_id = _validate_job_id(job_id)
    validated_run_dir = _preflight_run_dir(run_dir)
    running_job = _transition_job(
        session_factory=session_factory,
        job_id=validated_job_id,
        expected_status="queued",
        target_status="running",
    )

    try:
        workflow = run_paper_workflow_request(
            request=running_job.request,
            run_dir=validated_run_dir,
        )
    except (ValueError, OSError) as exc:
        _transition_job(
            session_factory=session_factory,
            job_id=validated_job_id,
            expected_status="running",
            target_status="failed",
        )
        raise PaperJobExecutionError() from exc

    succeeded_job = _transition_job(
        session_factory=session_factory,
        job_id=validated_job_id,
        expected_status="running",
        target_status="succeeded",
    )
    return PaperJobRunResult(job=succeeded_job, workflow=workflow)


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


def submit_paper_job(
    *,
    session_factory: sessionmaker[Session],
    command: PaperRunCommand,
) -> PaperJobRecord:
    """Validate and durably enqueue one job without executing it."""
    request = create_paper_run_request_from_command(command=command)
    prepared_request = prepare_paper_run_request_for_persistence(request)
    job = create_queued_paper_job_record(
        job_id=_new_job_id(),
        request=request,
        submitted_timestamp=_utc_now(),
    )
    try:
        with session_factory.begin() as session:
            return SqlAlchemyPaperJobRepository(session=session).add(
                job=job,
                prepared_request=prepared_request,
            )
    except IntegrityError as exc:
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


def list_paper_jobs(
    *,
    session_factory: sessionmaker[Session],
    status: str | None = None,
) -> tuple[PaperJobRecord, ...]:
    """List durable jobs deterministically without executing them."""
    with session_factory() as session:
        return SqlAlchemyPaperJobRepository(session=session).list(status=status)
