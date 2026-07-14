"""Focused caller-owned repository for durable paper-job records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from el_psy_quant.paper import PAPER_RUN_REQUEST_SCHEMA_VERSION
from el_psy_quant.persistence.paper_job_model import PaperJobRow
from el_psy_quant.persistence.paper_jobs import (
    PaperJobRecord,
    PaperJobStatus,
    PreparedPaperRunRequest,
    _job_id,
    _prepared_payload_for_request,
    _run_id,
    _status,
    _utc_timestamp,
    _validate_paper_job_status_transition,
    deserialize_paper_run_request,
    transition_paper_job_record,
)


class PaperJobRepository(Protocol):
    """Caller-owned persistence operations for paper jobs."""

    def add(
        self,
        *,
        job: PaperJobRecord,
        prepared_request: PreparedPaperRunRequest,
    ) -> PaperJobRecord: ...

    def get(self, *, job_id: str) -> PaperJobRecord | None: ...

    def get_by_run_id(self, *, run_id: str) -> PaperJobRecord | None: ...

    def list(self, *, status: str | None = None) -> tuple[PaperJobRecord, ...]: ...

    def transition_status(
        self,
        *,
        job_id: str,
        expected_status: PaperJobStatus,
        target_status: PaperJobStatus,
        updated_timestamp: datetime,
        expected_updated_timestamp: datetime | None = None,
    ) -> PaperJobRecord | None: ...


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


def _row_from_job(
    *,
    job: PaperJobRecord,
    prepared_request: PreparedPaperRunRequest,
) -> PaperJobRow:
    return PaperJobRow(
        record_schema_version=job.record_schema_version,
        job_id=job.job_id,
        run_id=job.run_id,
        status=job.status,
        request_schema_version=PAPER_RUN_REQUEST_SCHEMA_VERSION,
        request_payload=_prepared_payload_for_request(
            prepared_request,
            request=job.request,
        ),
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
        prepared_request: PreparedPaperRunRequest,
    ) -> PaperJobRecord:
        """Add and flush one queued job using its codec-prepared request."""
        if type(job) is not PaperJobRecord:
            raise ValueError("job must be a PaperJobRecord")
        if job.status != "queued":
            raise ValueError("only queued paper jobs may be added")
        self._session.add(
            _row_from_job(job=job, prepared_request=prepared_request)
        )
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

    def transition_status(
        self,
        *,
        job_id: str,
        expected_status: PaperJobStatus,
        target_status: PaperJobStatus,
        updated_timestamp: datetime,
        expected_updated_timestamp: datetime | None = None,
    ) -> PaperJobRecord | None:
        """Conditionally apply one approved status transition and flush it."""
        validated_job_id = _job_id(job_id)
        validated_expected = _status(expected_status)
        validated_target = _status(target_status)
        _validate_paper_job_status_transition(
            validated_expected,
            validated_target,
        )
        validated_timestamp = _utc_timestamp(
            updated_timestamp,
            field_name="updated_timestamp",
        )
        validated_expected_timestamp = (
            None
            if expected_updated_timestamp is None
            else _utc_timestamp(
                expected_updated_timestamp,
                field_name="expected_updated_timestamp",
            )
        )
        conditions = [
            PaperJobRow.job_id == validated_job_id,
            PaperJobRow.status == validated_expected,
            PaperJobRow.updated_timestamp <= validated_timestamp,
        ]
        if validated_expected_timestamp is not None:
            conditions.append(
                PaperJobRow.updated_timestamp == validated_expected_timestamp
            )
        row = self._session.scalar(
            update(PaperJobRow)
            .where(*conditions)
            .values(
                status=validated_target,
                updated_timestamp=validated_timestamp,
            )
            .returning(PaperJobRow)
            .execution_options(synchronize_session=False)
        )
        if row is None:
            current = self.get(job_id=validated_job_id)
            if current is not None and current.status == validated_expected:
                transition_paper_job_record(
                    job=current,
                    target_status=validated_target,
                    updated_timestamp=validated_timestamp,
                )
            return None
        self._session.flush()
        return _job_from_row(row)
