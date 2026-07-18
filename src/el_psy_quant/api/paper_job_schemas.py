"""Explicit durable paper-job HTTP request and response schemas."""

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from el_psy_quant.api.paper_run_schemas import PaperTradingArtifactResponse

PaperJobStatus = Literal["queued", "running", "succeeded", "failed", "canceled"]
PaperJobAttemptStatus = Literal["running", "succeeded", "failed", "interrupted"]
PaperJobErrorCode = Literal[
    "workflow_validation_failed",
    "output_conflict",
    "filesystem_io_failed",
    "interrupted_without_output",
    "partial_output_detected",
    "invalid_output_detected",
]


class PaperJobAttemptResponse(BaseModel):
    attempt_id: str
    attempt_number: int
    status: PaperJobAttemptStatus
    started_timestamp: datetime
    completed_timestamp: datetime | None
    error_code: PaperJobErrorCode | None


class PaperJobResponse(BaseModel):
    job_id: str
    run_id: str
    status: PaperJobStatus
    submitted_timestamp: datetime
    updated_timestamp: datetime
    attempt_count: int
    latest_attempt: PaperJobAttemptResponse | None
    result_available: bool
    result_url: str | None


class PaperJobSubmissionResponse(BaseModel):
    submission_outcome: Literal["created", "replayed"]
    job: PaperJobResponse


class PaperJobRecoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stale_before: datetime

    @field_validator("stale_before")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("stale_before must be timezone-aware UTC")
        return value


class PaperJobRecoveryResponse(BaseModel):
    recovery_outcome: Literal["requeued", "succeeded", "failed"]
    job: PaperJobResponse


class PaperJobResultReferenceResponse(BaseModel):
    record_schema_version: Literal[1]
    root_type: Literal["paper"]
    artifact_schema_version: Literal[1]
    result_summary_schema_version: Literal[1]
    created_timestamp: datetime


class PaperJobResultAuditResponse(BaseModel):
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


class PaperJobResultSummaryResponse(BaseModel):
    schema_version: Literal[1]
    run_id: str
    request_schema_version: Literal[1]
    request_created_timestamp: str
    artifact_schema_version: Literal[1]
    artifact_created_timestamp: str
    audit: PaperJobResultAuditResponse


class PaperJobResultResponse(BaseModel):
    job_id: str
    run_id: str
    result_reference: PaperJobResultReferenceResponse
    artifact: PaperTradingArtifactResponse
    result_summary: PaperJobResultSummaryResponse
