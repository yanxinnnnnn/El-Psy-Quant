"""Focused caller-owned repository for paper-job execution attempts."""

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from el_psy_quant.persistence.paper_job_attempt_model import PaperJobAttemptRow
from el_psy_quant.persistence.paper_job_attempts import (
    PaperJobAttemptRecord,
    PaperJobAttemptStatus,
    PaperJobErrorCode,
    complete_paper_job_attempt,
)
from el_psy_quant.persistence.paper_jobs import _job_id, _utc_timestamp


class PaperJobAttemptRepository(Protocol):
    """Caller-owned persistence operations for execution attempts."""

    def next_attempt_number(self, *, job_id: str) -> int: ...

    def start_attempt(self, *, attempt: PaperJobAttemptRecord) -> PaperJobAttemptRecord: ...

    def get_running_for_job(self, *, job_id: str) -> PaperJobAttemptRecord | None: ...

    def complete_attempt(
        self,
        *,
        attempt_id: str,
        status: PaperJobAttemptStatus,
        completed_timestamp: datetime,
        error_code: PaperJobErrorCode | None = None,
    ) -> PaperJobAttemptRecord | None: ...

    def list_for_job(self, *, job_id: str) -> tuple[PaperJobAttemptRecord, ...]: ...


def _timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _attempt_from_row(row: PaperJobAttemptRow) -> PaperJobAttemptRecord:
    return PaperJobAttemptRecord(
        record_schema_version=row.record_schema_version,  # type: ignore[arg-type]
        attempt_id=row.attempt_id,
        job_id=row.job_id,
        attempt_number=row.attempt_number,
        status=row.status,  # type: ignore[arg-type]
        started_timestamp=_timestamp(row.started_timestamp),
        completed_timestamp=(
            None
            if row.completed_timestamp is None
            else _timestamp(row.completed_timestamp)
        ),
        error_code=row.error_code,  # type: ignore[arg-type]
    )


class SqlAlchemyPaperJobAttemptRepository:
    """SQLAlchemy repository that never owns the caller's transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def next_attempt_number(self, *, job_id: str) -> int:
        """Return the next positive attempt number for one exact job."""
        maximum = self._session.scalar(
            select(func.max(PaperJobAttemptRow.attempt_number)).where(
                PaperJobAttemptRow.job_id == _job_id(job_id)
            )
        )
        return 1 if maximum is None else maximum + 1

    def start_attempt(
        self,
        *,
        attempt: PaperJobAttemptRecord,
    ) -> PaperJobAttemptRecord:
        """Add and flush one running attempt."""
        if type(attempt) is not PaperJobAttemptRecord or attempt.status != "running":
            raise ValueError("attempt must be a running PaperJobAttemptRecord")
        self._session.add(
            PaperJobAttemptRow(
                record_schema_version=attempt.record_schema_version,
                attempt_id=attempt.attempt_id,
                job_id=attempt.job_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status,
                started_timestamp=attempt.started_timestamp,
                completed_timestamp=None,
                error_code=None,
            )
        )
        self._session.flush()
        return attempt

    def get_running_for_job(self, *, job_id: str) -> PaperJobAttemptRecord | None:
        """Return the one active attempt for a job, if present."""
        row = self._session.scalar(
            select(PaperJobAttemptRow).where(
                PaperJobAttemptRow.job_id == _job_id(job_id),
                PaperJobAttemptRow.status == "running",
            )
        )
        return None if row is None else _attempt_from_row(row)

    def complete_attempt(
        self,
        *,
        attempt_id: str,
        status: PaperJobAttemptStatus,
        completed_timestamp: datetime,
        error_code: PaperJobErrorCode | None = None,
    ) -> PaperJobAttemptRecord | None:
        """Conditionally complete an attempt that is still running."""
        validated_attempt_id = _job_id(attempt_id)
        completed = _utc_timestamp(
            completed_timestamp,
            field_name="completed_timestamp",
        )
        current = self._session.scalar(
            select(PaperJobAttemptRow).where(
                PaperJobAttemptRow.attempt_id == validated_attempt_id,
                PaperJobAttemptRow.status == "running",
            )
        )
        if current is None:
            return None
        completed_record = complete_paper_job_attempt(
            attempt=_attempt_from_row(current),
            status=status,
            completed_timestamp=completed,
            error_code=error_code,
        )
        row = self._session.scalar(
            update(PaperJobAttemptRow)
            .where(
                PaperJobAttemptRow.attempt_id == validated_attempt_id,
                PaperJobAttemptRow.status == "running",
            )
            .values(
                status=completed_record.status,
                completed_timestamp=completed_record.completed_timestamp,
                error_code=completed_record.error_code,
            )
            .returning(PaperJobAttemptRow)
            .execution_options(synchronize_session=False)
        )
        if row is None:
            return None
        self._session.flush()
        self._session.expire(row)
        return _attempt_from_row(row)

    def list_for_job(self, *, job_id: str) -> tuple[PaperJobAttemptRecord, ...]:
        """List one job's attempts deterministically by attempt number."""
        rows = self._session.scalars(
            select(PaperJobAttemptRow)
            .where(PaperJobAttemptRow.job_id == _job_id(job_id))
            .order_by(PaperJobAttemptRow.attempt_number)
        ).all()
        return tuple(_attempt_from_row(row) for row in rows)
