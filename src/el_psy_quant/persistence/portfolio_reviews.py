"""Immutable compact durable portfolio-review records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from el_psy_quant.portfolio_review import (
    PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION,
    PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION,
)
from el_psy_quant.portfolio_review.artifact_files import (
    portfolio_review_analysis_relative_path,
    portfolio_review_decision_relative_path,
    portfolio_review_source_relative_path,
)

PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION = 1
SUPPORTED_PORTFOLIO_REVIEW_STATUSES = (
    "awaiting_decision",
    "approved",
    "rejected",
    "deferred",
)
PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM = 200

PortfolioReviewStatus = Literal[
    "awaiting_decision",
    "approved",
    "rejected",
    "deferred",
]
PortfolioReviewDecisionOutcome = Literal["approved", "rejected", "deferred"]

_IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def validate_portfolio_review_idempotency_key(value: object) -> str:
    """Validate one explicit caller key without normalization."""
    if type(value) is not str or _IDEMPOTENCY_KEY_PATTERN.fullmatch(value) is None:
        raise ValueError("idempotency_key is invalid")
    return value


def _required_string(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _digest(value: object, field_name: str) -> str:
    normalized = _required_string(value, field_name)
    if _SHA256_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return normalized


def _utc_timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc
    if offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _status(value: object) -> PortfolioReviewStatus:
    normalized = _required_string(value, "status")
    if normalized not in SUPPORTED_PORTFOLIO_REVIEW_STATUSES:
        raise ValueError("status is unsupported")
    return normalized  # type: ignore[return-value]


def digest_portfolio_review_command(payload: dict[str, object]) -> str:
    """Hash one normalized validated command payload."""
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PortfolioReviewRecord:
    """Compact SQLite-owned workflow and idempotency authority."""

    record_schema_version: Literal[1]
    review_id: str
    status: PortfolioReviewStatus
    source_schema_version: Literal[1]
    source_id: str
    source_digest: str
    source_relative_path: str
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    proposed_component_id: str
    analysis_schema_version: Literal[1]
    analysis_digest: str
    analysis_relative_path: str
    create_idempotency_key: str
    create_command_digest: str
    created_by: str
    created_timestamp: datetime
    decision_schema_version: Literal[1] | None
    decision_id: str | None
    decision_digest: str | None
    decision_relative_path: str | None
    decision_idempotency_key: str | None
    decision_command_digest: str | None
    outcome: PortfolioReviewDecisionOutcome | None
    reviewed_by: str | None
    reviewed_timestamp: datetime | None
    version: int
    updated_timestamp: datetime

    def __post_init__(self) -> None:
        if (
            type(self.record_schema_version) is not int
            or self.record_schema_version
            != PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION
        ):
            raise ValueError("record_schema_version must be 1")
        review_id = _required_string(self.review_id, "review_id")
        status = _status(self.status)
        if (
            type(self.source_schema_version) is not int
            or self.source_schema_version
            != PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION
        ):
            raise ValueError("source_schema_version is unsupported")
        source_id = _required_string(self.source_id, "source_id")
        if (
            type(self.analysis_schema_version) is not int
            or self.analysis_schema_version
            != PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION
        ):
            raise ValueError("analysis_schema_version is unsupported")
        object.__setattr__(self, "review_id", review_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(
            self, "source_digest", _digest(self.source_digest, "source_digest")
        )
        object.__setattr__(
            self,
            "source_relative_path",
            _required_string(self.source_relative_path, "source_relative_path"),
        )
        object.__setattr__(
            self,
            "baseline_scenario_id",
            _required_string(self.baseline_scenario_id, "baseline_scenario_id"),
        )
        object.__setattr__(
            self,
            "baseline_scenario_digest",
            _digest(
                self.baseline_scenario_digest,
                "baseline_scenario_digest",
            ),
        )
        object.__setattr__(
            self,
            "proposed_scenario_id",
            _required_string(self.proposed_scenario_id, "proposed_scenario_id"),
        )
        object.__setattr__(
            self,
            "proposed_scenario_digest",
            _digest(
                self.proposed_scenario_digest,
                "proposed_scenario_digest",
            ),
        )
        object.__setattr__(
            self,
            "proposed_component_id",
            _required_string(self.proposed_component_id, "proposed_component_id"),
        )
        object.__setattr__(
            self,
            "analysis_digest",
            _digest(self.analysis_digest, "analysis_digest"),
        )
        object.__setattr__(
            self,
            "analysis_relative_path",
            _required_string(
                self.analysis_relative_path,
                "analysis_relative_path",
            ),
        )
        object.__setattr__(
            self,
            "create_idempotency_key",
            validate_portfolio_review_idempotency_key(
                self.create_idempotency_key
            ),
        )
        object.__setattr__(
            self,
            "create_command_digest",
            _digest(self.create_command_digest, "create_command_digest"),
        )
        object.__setattr__(
            self, "created_by", _required_string(self.created_by, "created_by")
        )
        created = _utc_timestamp(self.created_timestamp, "created_timestamp")
        updated = _utc_timestamp(self.updated_timestamp, "updated_timestamp")
        object.__setattr__(self, "created_timestamp", created)
        object.__setattr__(self, "updated_timestamp", updated)

        if self.source_relative_path != portfolio_review_source_relative_path(
            source_id
        ) or self.analysis_relative_path != portfolio_review_analysis_relative_path(
            review_id
        ):
            raise ValueError("portfolio review relative paths are invalid")

        decision_values = (
            self.decision_schema_version,
            self.decision_id,
            self.decision_digest,
            self.decision_relative_path,
            self.decision_idempotency_key,
            self.decision_command_digest,
            self.outcome,
            self.reviewed_by,
            self.reviewed_timestamp,
        )
        if status == "awaiting_decision":
            if (
                any(value is not None for value in decision_values)
                or type(self.version) is not int
                or self.version != 1
                or updated != created
            ):
                raise ValueError("awaiting_decision record is inconsistent")
            return

        if any(value is None for value in decision_values):
            raise ValueError("settled record decision fields must all be present")
        if (
            type(self.decision_schema_version) is not int
            or self.decision_schema_version
            != PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION
            or self.outcome != status
            or type(self.version) is not int
            or self.version != 2
        ):
            raise ValueError("settled record is inconsistent")
        reviewed = _utc_timestamp(self.reviewed_timestamp, "reviewed_timestamp")
        if reviewed < created or updated != reviewed:
            raise ValueError("settled timestamps are inconsistent")
        object.__setattr__(self, "decision_id", _required_string(self.decision_id, "decision_id"))
        object.__setattr__(
            self,
            "decision_digest",
            _digest(self.decision_digest, "decision_digest"),
        )
        object.__setattr__(
            self,
            "decision_idempotency_key",
            validate_portfolio_review_idempotency_key(
                self.decision_idempotency_key
            ),
        )
        object.__setattr__(
            self,
            "decision_command_digest",
            _digest(
                self.decision_command_digest,
                "decision_command_digest",
            ),
        )
        object.__setattr__(
            self,
            "reviewed_by",
            _required_string(self.reviewed_by, "reviewed_by"),
        )
        object.__setattr__(self, "reviewed_timestamp", reviewed)
        if self.decision_relative_path != portfolio_review_decision_relative_path(
            review_id
        ):
            raise ValueError("decision_relative_path is invalid")


def create_awaiting_portfolio_review_record(
    *,
    review_id: str,
    source_id: str,
    source_digest: str,
    baseline_scenario_id: str,
    baseline_scenario_digest: str,
    proposed_scenario_id: str,
    proposed_scenario_digest: str,
    proposed_component_id: str,
    analysis_digest: str,
    create_idempotency_key: str,
    create_command_digest: str,
    created_by: str,
    created_timestamp: datetime,
) -> PortfolioReviewRecord:
    """Create one valid initial compact review record."""
    return PortfolioReviewRecord(
        record_schema_version=1,
        review_id=review_id,
        status="awaiting_decision",
        source_schema_version=PORTFOLIO_REVIEW_SOURCE_SCHEMA_VERSION,
        source_id=source_id,
        source_digest=source_digest,
        source_relative_path=portfolio_review_source_relative_path(source_id),
        baseline_scenario_id=baseline_scenario_id,
        baseline_scenario_digest=baseline_scenario_digest,
        proposed_scenario_id=proposed_scenario_id,
        proposed_scenario_digest=proposed_scenario_digest,
        proposed_component_id=proposed_component_id,
        analysis_schema_version=PORTFOLIO_REVIEW_ANALYSIS_ARTIFACT_SCHEMA_VERSION,
        analysis_digest=analysis_digest,
        analysis_relative_path=portfolio_review_analysis_relative_path(review_id),
        create_idempotency_key=create_idempotency_key,
        create_command_digest=create_command_digest,
        created_by=created_by,
        created_timestamp=created_timestamp,
        decision_schema_version=None,
        decision_id=None,
        decision_digest=None,
        decision_relative_path=None,
        decision_idempotency_key=None,
        decision_command_digest=None,
        outcome=None,
        reviewed_by=None,
        reviewed_timestamp=None,
        version=1,
        updated_timestamp=created_timestamp,
    )


__all__ = [
    "PORTFOLIO_REVIEW_LIST_LIMIT_MAXIMUM",
    "PORTFOLIO_REVIEW_RECORD_SCHEMA_VERSION",
    "PortfolioReviewDecisionOutcome",
    "PortfolioReviewRecord",
    "PortfolioReviewStatus",
    "SUPPORTED_PORTFOLIO_REVIEW_STATUSES",
    "create_awaiting_portfolio_review_record",
    "digest_portfolio_review_command",
    "validate_portfolio_review_idempotency_key",
]
