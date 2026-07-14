"""Focused caller-owned repository for paper-job submission keys."""

from datetime import timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from el_psy_quant.persistence.paper_job_submission_key_model import (
    PaperJobSubmissionKeyRow,
)
from el_psy_quant.persistence.paper_job_submission_keys import (
    PaperJobSubmissionKeyRecord,
    validate_paper_job_idempotency_key,
)
from el_psy_quant.persistence.paper_jobs import _job_id


class PaperJobSubmissionKeyRepository(Protocol):
    """Caller-owned persistence operations for submission-key mappings."""

    def add(self, *, record: PaperJobSubmissionKeyRecord) -> PaperJobSubmissionKeyRecord: ...

    def get_by_key(self, *, idempotency_key: str) -> PaperJobSubmissionKeyRecord | None: ...

    def get_by_job_id(self, *, job_id: str) -> PaperJobSubmissionKeyRecord | None: ...


def _record_from_row(row: PaperJobSubmissionKeyRow) -> PaperJobSubmissionKeyRecord:
    created = row.created_timestamp
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return PaperJobSubmissionKeyRecord(
        record_schema_version=row.record_schema_version,  # type: ignore[arg-type]
        idempotency_key=row.idempotency_key,
        job_id=row.job_id,
        request_schema_version=row.request_schema_version,  # type: ignore[arg-type]
        request_digest=row.request_digest,
        created_timestamp=created.astimezone(timezone.utc),
    )


class SqlAlchemyPaperJobSubmissionKeyRepository:
    """SQLAlchemy repository that never owns the caller's transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def add(self, *, record: PaperJobSubmissionKeyRecord) -> PaperJobSubmissionKeyRecord:
        """Add and flush one exact key mapping."""
        if type(record) is not PaperJobSubmissionKeyRecord:
            raise ValueError("record must be a PaperJobSubmissionKeyRecord")
        self._session.add(
            PaperJobSubmissionKeyRow(
                record_schema_version=record.record_schema_version,
                idempotency_key=record.idempotency_key,
                job_id=record.job_id,
                request_schema_version=record.request_schema_version,
                request_digest=record.request_digest,
                created_timestamp=record.created_timestamp,
            )
        )
        self._session.flush()
        return record

    def get_by_key(
        self,
        *,
        idempotency_key: str,
    ) -> PaperJobSubmissionKeyRecord | None:
        """Get one exact mapping by caller key."""
        row = self._session.get(
            PaperJobSubmissionKeyRow,
            validate_paper_job_idempotency_key(idempotency_key),
        )
        return None if row is None else _record_from_row(row)

    def get_by_job_id(self, *, job_id: str) -> PaperJobSubmissionKeyRecord | None:
        """Get the optional unique mapping for one job."""
        row = self._session.scalar(
            select(PaperJobSubmissionKeyRow).where(
                PaperJobSubmissionKeyRow.job_id == _job_id(job_id)
            )
        )
        return None if row is None else _record_from_row(row)
