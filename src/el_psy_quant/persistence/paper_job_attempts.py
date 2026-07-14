"""Immutable execution-attempt and sanitized error-audit contracts."""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal, TypeAlias, cast

from el_psy_quant.persistence.paper_jobs import _job_id, _utc_timestamp

PAPER_JOB_ATTEMPT_RECORD_SCHEMA_VERSION = 1

PaperJobAttemptStatus: TypeAlias = Literal[
    "running",
    "succeeded",
    "failed",
    "interrupted",
]
PaperJobErrorCode: TypeAlias = Literal[
    "workflow_validation_failed",
    "output_conflict",
    "filesystem_io_failed",
    "interrupted_without_output",
    "partial_output_detected",
    "invalid_output_detected",
]
SUPPORTED_PAPER_JOB_ATTEMPT_STATUSES: tuple[PaperJobAttemptStatus, ...] = (
    "running",
    "succeeded",
    "failed",
    "interrupted",
)
SUPPORTED_PAPER_JOB_ERROR_CODES: tuple[PaperJobErrorCode, ...] = (
    "workflow_validation_failed",
    "output_conflict",
    "filesystem_io_failed",
    "interrupted_without_output",
    "partial_output_detected",
    "invalid_output_detected",
)


def _attempt_status(value: object) -> PaperJobAttemptStatus:
    if type(value) is not str or value not in SUPPORTED_PAPER_JOB_ATTEMPT_STATUSES:
        raise ValueError("paper job attempt status is unsupported")
    return cast(PaperJobAttemptStatus, value)


def _error_code(value: object) -> PaperJobErrorCode:
    if type(value) is not str or value not in SUPPORTED_PAPER_JOB_ERROR_CODES:
        raise ValueError("paper job error code is unsupported")
    return cast(PaperJobErrorCode, value)


def _attempt_number(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("attempt_number must be a positive integer")
    return value


@dataclass(frozen=True)
class PaperJobAttemptRecord:
    """Compact immutable operational audit for one execution attempt."""

    record_schema_version: Literal[1]
    attempt_id: str
    job_id: str
    attempt_number: int
    status: PaperJobAttemptStatus
    started_timestamp: datetime
    completed_timestamp: datetime | None
    error_code: PaperJobErrorCode | None

    def __post_init__(self) -> None:
        if self.record_schema_version != PAPER_JOB_ATTEMPT_RECORD_SCHEMA_VERSION:
            raise ValueError("record_schema_version must be 1")
        object.__setattr__(self, "attempt_id", _job_id(self.attempt_id))
        object.__setattr__(self, "job_id", _job_id(self.job_id))
        object.__setattr__(self, "attempt_number", _attempt_number(self.attempt_number))
        status = _attempt_status(self.status)
        object.__setattr__(self, "status", status)
        started = _utc_timestamp(
            self.started_timestamp,
            field_name="started_timestamp",
        )
        object.__setattr__(self, "started_timestamp", started)
        completed = self.completed_timestamp
        if completed is not None:
            completed = _utc_timestamp(completed, field_name="completed_timestamp")
            if completed < started:
                raise ValueError("completed_timestamp must not precede started_timestamp")
            object.__setattr__(self, "completed_timestamp", completed)

        if status == "running":
            if completed is not None or self.error_code is not None:
                raise ValueError("running attempt cannot be completed or have an error")
        elif status == "succeeded":
            if completed is None or self.error_code is not None:
                raise ValueError("succeeded attempt requires completion without an error")
        else:
            if completed is None or self.error_code is None:
                raise ValueError("failed or interrupted attempt requires an error code")
            object.__setattr__(self, "error_code", _error_code(self.error_code))


def create_running_paper_job_attempt(
    *,
    attempt_id: str,
    job_id: str,
    attempt_number: int,
    started_timestamp: datetime,
) -> PaperJobAttemptRecord:
    """Create one active running attempt."""
    return PaperJobAttemptRecord(
        record_schema_version=1,
        attempt_id=attempt_id,
        job_id=job_id,
        attempt_number=attempt_number,
        status="running",
        started_timestamp=started_timestamp,
        completed_timestamp=None,
        error_code=None,
    )


def complete_paper_job_attempt(
    *,
    attempt: PaperJobAttemptRecord,
    status: PaperJobAttemptStatus,
    completed_timestamp: datetime,
    error_code: PaperJobErrorCode | None = None,
) -> PaperJobAttemptRecord:
    """Complete one running attempt exactly once."""
    if type(attempt) is not PaperJobAttemptRecord:
        raise ValueError("attempt must be a PaperJobAttemptRecord")
    if attempt.status != "running":
        raise ValueError("only a running attempt may be completed")
    target = _attempt_status(status)
    if target == "running":
        raise ValueError("attempt completion status must be terminal")
    return replace(
        attempt,
        status=target,
        completed_timestamp=completed_timestamp,
        error_code=error_code,
    )
