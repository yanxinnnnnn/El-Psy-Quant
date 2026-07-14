"""Immutable durable submission-idempotency mappings."""

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Literal

from el_psy_quant.paper import PAPER_RUN_REQUEST_SCHEMA_VERSION
from el_psy_quant.persistence.paper_jobs import _job_id, _utc_timestamp

PAPER_JOB_SUBMISSION_KEY_RECORD_SCHEMA_VERSION = 1
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def validate_paper_job_idempotency_key(value: object) -> str:
    """Validate one explicit caller idempotency key without normalization."""
    if type(value) is not str or _IDEMPOTENCY_KEY_PATTERN.fullmatch(value) is None:
        raise ValueError("idempotency_key is invalid")
    return value


def _request_digest(value: object) -> str:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError("request_digest must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class PaperJobSubmissionKeyRecord:
    """Compact durable mapping from one caller key to one paper job."""

    record_schema_version: Literal[1]
    idempotency_key: str
    job_id: str
    request_schema_version: Literal[1]
    request_digest: str
    created_timestamp: datetime

    def __post_init__(self) -> None:
        if self.record_schema_version != PAPER_JOB_SUBMISSION_KEY_RECORD_SCHEMA_VERSION:
            raise ValueError("record_schema_version must be 1")
        object.__setattr__(
            self,
            "idempotency_key",
            validate_paper_job_idempotency_key(self.idempotency_key),
        )
        object.__setattr__(self, "job_id", _job_id(self.job_id))
        if self.request_schema_version != PAPER_RUN_REQUEST_SCHEMA_VERSION:
            raise ValueError("request_schema_version must be 1")
        object.__setattr__(self, "request_digest", _request_digest(self.request_digest))
        object.__setattr__(
            self,
            "created_timestamp",
            _utc_timestamp(self.created_timestamp, field_name="created_timestamp"),
        )


def create_paper_job_submission_key_record(
    *,
    idempotency_key: str,
    job_id: str,
    request_digest: str,
    created_timestamp: datetime,
) -> PaperJobSubmissionKeyRecord:
    """Create one validated submission-key mapping."""
    return PaperJobSubmissionKeyRecord(
        record_schema_version=1,
        idempotency_key=idempotency_key,
        job_id=job_id,
        request_schema_version=1,
        request_digest=request_digest,
        created_timestamp=created_timestamp,
    )
