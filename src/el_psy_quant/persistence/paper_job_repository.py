"""Focused caller-owned repository for durable paper-job records."""

from __future__ import annotations

from datetime import timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from el_psy_quant.paper import PAPER_RUN_REQUEST_SCHEMA_VERSION
from el_psy_quant.persistence.paper_job_model import PaperJobRow
from el_psy_quant.persistence.paper_jobs import (
    PaperJobRecord,
    _job_id,
    _run_id,
    _status,
    deserialize_paper_run_request,
)


class PaperJobRepository(Protocol):
    """Caller-owned persistence operations for paper jobs."""

    def add(
        self,
        *,
        job: PaperJobRecord,
        request_payload: str,
    ) -> PaperJobRecord: ...

    def get(self, *, job_id: str) -> PaperJobRecord | None: ...

    def get_by_run_id(self, *, run_id: str) -> PaperJobRecord | None: ...

    def list(self, *, status: str | None = None) -> tuple[PaperJobRecord, ...]: ...


def _job_from_row(row: PaperJobRow) -> PaperJobRecord:
    if row.request_schema_version != PAPER_RUN_REQUEST_SCHEMA_VERSION:
        raise ValueError("persisted paper job request schema is unsupported")
    submitted = row.submitted_timestamp
    updated = row.updated_timestamp
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone.utc)
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return PaperJobRecord(
        record_schema_version=row.record_schema_version,  # type: ignore[arg-type]
        job_id=row.job_id,
        run_id=row.run_id,
        status=row.status,  # type: ignore[arg-type]
        request=deserialize_paper_run_request(row.request_payload),
        submitted_timestamp=submitted.astimezone(timezone.utc),
        updated_timestamp=updated.astimezone(timezone.utc),
    )


def _row_from_job(*, job: PaperJobRecord, request_payload: str) -> PaperJobRow:
    return PaperJobRow(
        record_schema_version=job.record_schema_version,
        job_id=job.job_id,
        run_id=job.run_id,
        status=job.status,
        request_schema_version=PAPER_RUN_REQUEST_SCHEMA_VERSION,
        request_payload=request_payload,
        submitted_timestamp=job.submitted_timestamp,
        updated_timestamp=job.updated_timestamp,
    )


class SqlAlchemyPaperJobRepository:
    """SQLAlchemy repository that never owns the caller's transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def add(
        self,
        *,
        job: PaperJobRecord,
        request_payload: str,
    ) -> PaperJobRecord:
        """Add and flush one queued job using its caller-prepared payload."""
        if type(job) is not PaperJobRecord:
            raise ValueError("job must be a PaperJobRecord")
        if job.status != "queued":
            raise ValueError("only queued paper jobs may be added")
        if type(request_payload) is not str:
            raise ValueError("request payload must be a canonical JSON string")
        self._session.add(_row_from_job(job=job, request_payload=request_payload))
        self._session.flush()
        return job

    def get(self, *, job_id: str) -> PaperJobRecord | None:
        """Get one exact job by canonical product identity."""
        row = self._session.get(PaperJobRow, _job_id(job_id))
        return None if row is None else _job_from_row(row)

    def get_by_run_id(self, *, run_id: str) -> PaperJobRecord | None:
        """Get one exact job by its unique normalized paper-run identity."""
        row = self._session.scalar(
            select(PaperJobRow).where(PaperJobRow.run_id == _run_id(run_id))
        )
        return None if row is None else _job_from_row(row)

    def list(self, *, status: str | None = None) -> tuple[PaperJobRecord, ...]:
        """List jobs deterministically by submission time then job identity."""
        statement = select(PaperJobRow)
        if status is not None:
            statement = statement.where(PaperJobRow.status == _status(status))
        statement = statement.order_by(
            PaperJobRow.submitted_timestamp,
            PaperJobRow.job_id,
        )
        return tuple(
            _job_from_row(row) for row in self._session.scalars(statement).all()
        )
