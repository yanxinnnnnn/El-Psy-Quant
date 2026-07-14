"""Immutable compact references to authoritative paper-job output files."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal

from el_psy_quant.paper import (
    PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
    PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
)
from el_psy_quant.persistence.paper_jobs import _job_id, _utc_timestamp

PAPER_JOB_RESULT_REFERENCE_RECORD_SCHEMA_VERSION = 1
PAPER_JOB_RESULT_ROOT_TYPE = "paper"
PAPER_JOB_ARTIFACT_FILE_NAME = "paper_run_artifact.json"
PAPER_JOB_RESULT_SUMMARY_FILE_NAME = "paper_run_result_summary.json"


def _relative_path(value: object, *, job_id: str, filename: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError("paper job result path must be normalized")
    if "\\" in value or ":" in value:
        raise ValueError("paper job result path must use relative POSIX form")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("paper job result path must use relative POSIX form")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError("paper job result path must use relative POSIX form")
    expected = PurePosixPath("jobs", job_id, "paper", filename)
    if path != expected:
        raise ValueError("paper job result path must use the job-owned layout")
    return path.as_posix()


@dataclass(frozen=True)
class PaperJobResultReference:
    """One immutable product pointer to two authoritative output files."""

    record_schema_version: Literal[1]
    job_id: str
    root_type: Literal["paper"]
    artifact_schema_version: Literal[1]
    result_summary_schema_version: Literal[1]
    artifact_relative_path: str
    result_summary_relative_path: str
    created_timestamp: datetime

    def __post_init__(self) -> None:
        if (
            type(self.record_schema_version) is not int
            or self.record_schema_version
            != PAPER_JOB_RESULT_REFERENCE_RECORD_SCHEMA_VERSION
        ):
            raise ValueError("record_schema_version must be 1")
        validated_job_id = _job_id(self.job_id)
        object.__setattr__(self, "job_id", validated_job_id)
        if type(self.root_type) is not str or self.root_type != PAPER_JOB_RESULT_ROOT_TYPE:
            raise ValueError("root_type must be paper")
        if (
            type(self.artifact_schema_version) is not int
            or self.artifact_schema_version != PAPER_TRADING_ARTIFACT_SCHEMA_VERSION
        ):
            raise ValueError("artifact_schema_version must be 1")
        if (
            type(self.result_summary_schema_version) is not int
            or self.result_summary_schema_version
            != PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION
        ):
            raise ValueError("result_summary_schema_version must be 1")
        object.__setattr__(
            self,
            "artifact_relative_path",
            _relative_path(
                self.artifact_relative_path,
                job_id=validated_job_id,
                filename=PAPER_JOB_ARTIFACT_FILE_NAME,
            ),
        )
        object.__setattr__(
            self,
            "result_summary_relative_path",
            _relative_path(
                self.result_summary_relative_path,
                job_id=validated_job_id,
                filename=PAPER_JOB_RESULT_SUMMARY_FILE_NAME,
            ),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _utc_timestamp(self.created_timestamp, field_name="created_timestamp"),
        )


def create_paper_job_result_reference(
    *,
    job_id: str,
    created_timestamp: datetime,
) -> PaperJobResultReference:
    """Create the exact compact reference for one API-owned paper job."""
    validated_job_id = _job_id(job_id)
    directory = PurePosixPath("jobs", validated_job_id, "paper")
    return PaperJobResultReference(
        record_schema_version=1,
        job_id=validated_job_id,
        root_type="paper",
        artifact_schema_version=PAPER_TRADING_ARTIFACT_SCHEMA_VERSION,
        result_summary_schema_version=PAPER_RUN_RESULT_SUMMARY_SCHEMA_VERSION,
        artifact_relative_path=(directory / PAPER_JOB_ARTIFACT_FILE_NAME).as_posix(),
        result_summary_relative_path=(
            directory / PAPER_JOB_RESULT_SUMMARY_FILE_NAME
        ).as_posix(),
        created_timestamp=created_timestamp,
    )
