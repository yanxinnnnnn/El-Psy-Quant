"""Explicit durable queued-paper-job submission and database-only reads."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.application.paper_runs import (
    PaperRunCommand,
    create_paper_run_request_from_command,
)
from el_psy_quant.persistence import (
    PaperJobRecord,
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


def _new_job_id() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
