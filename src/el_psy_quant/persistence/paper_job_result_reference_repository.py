"""Caller-owned repository for compact paper-job result references."""

from datetime import timezone
from typing import Protocol

from sqlalchemy.orm import Session

from el_psy_quant.persistence.paper_job_result_reference_model import (
    PaperJobResultReferenceRow,
)
from el_psy_quant.persistence.paper_job_result_references import (
    PaperJobResultReference,
)
from el_psy_quant.persistence.paper_jobs import _job_id


class PaperJobResultReferenceRepository(Protocol):
    def add(
        self, *, reference: PaperJobResultReference
    ) -> PaperJobResultReference: ...

    def get_by_job_id(self, *, job_id: str) -> PaperJobResultReference | None: ...


def _reference_from_row(row: PaperJobResultReferenceRow) -> PaperJobResultReference:
    created = row.created_timestamp
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return PaperJobResultReference(
        record_schema_version=row.record_schema_version,  # type: ignore[arg-type]
        job_id=row.job_id,
        root_type=row.root_type,  # type: ignore[arg-type]
        artifact_schema_version=row.artifact_schema_version,  # type: ignore[arg-type]
        result_summary_schema_version=row.result_summary_schema_version,  # type: ignore[arg-type]
        artifact_relative_path=row.artifact_relative_path,
        result_summary_relative_path=row.result_summary_relative_path,
        created_timestamp=created.astimezone(timezone.utc),
    )


class SqlAlchemyPaperJobResultReferenceRepository:
    """Focused SQLAlchemy repository that never owns the transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def add(
        self, *, reference: PaperJobResultReference
    ) -> PaperJobResultReference:
        """Add and flush one immutable reference."""
        if type(reference) is not PaperJobResultReference:
            raise ValueError("reference must be a PaperJobResultReference")
        self._session.add(
            PaperJobResultReferenceRow(
                record_schema_version=reference.record_schema_version,
                job_id=reference.job_id,
                root_type=reference.root_type,
                artifact_schema_version=reference.artifact_schema_version,
                result_summary_schema_version=reference.result_summary_schema_version,
                artifact_relative_path=reference.artifact_relative_path,
                result_summary_relative_path=reference.result_summary_relative_path,
                created_timestamp=reference.created_timestamp,
            )
        )
        self._session.flush()
        return reference

    def get_by_job_id(self, *, job_id: str) -> PaperJobResultReference | None:
        """Read the optional reference for one exact job."""
        row = self._session.get(PaperJobResultReferenceRow, _job_id(job_id))
        return None if row is None else _reference_from_row(row)
