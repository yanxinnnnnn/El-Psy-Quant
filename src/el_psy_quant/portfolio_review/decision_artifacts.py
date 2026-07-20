"""Immutable human-governance decisions for portfolio reviews."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from el_psy_quant.portfolio_review.analysis_artifacts import (
    PortfolioReviewAnalysisArtifact,
)

PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION = 1
PORTFOLIO_REVIEW_DECISION_SCOPE = "portfolio_review_governance_only"

SUPPORTED_PORTFOLIO_REVIEW_DECISION_OUTCOMES = (
    "approved",
    "rejected",
    "deferred",
)

PortfolioReviewDecisionOutcome = Literal[
    "approved",
    "rejected",
    "deferred",
]

_CONSTRUCTOR_MESSAGE = (
    "portfolio-review decision artifacts are created by "
    "create_portfolio_review_decision_artifact"
)


def _reject_public_construction(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise TypeError(_CONSTRUCTOR_MESSAGE)


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_string_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of non-empty strings")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            f"{field_name} must be a sequence of non-empty strings"
        ) from exc
    return tuple(
        _normalize_required_string(value, f"{field_name} item")
        for value in normalized
    )


def _normalize_utc_timestamp(value: object, field_name: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field_name} must be timezone-aware") from exc


def _normalize_outcome(value: str) -> PortfolioReviewDecisionOutcome:
    normalized = _normalize_required_string(value, "outcome")
    if normalized not in SUPPORTED_PORTFOLIO_REVIEW_DECISION_OUTCOMES:
        supported = ", ".join(SUPPORTED_PORTFOLIO_REVIEW_DECISION_OUTCOMES)
        raise ValueError(
            f"unsupported outcome: {value}; supported: {supported}"
        )
    return normalized  # type: ignore[return-value]


def _canonical_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, init=False)
class PortfolioReviewDecisionArtifact:
    """One immutable governance-only human decision linked to an analysis."""

    decision_id: str
    decision_scope: str
    review_id: str
    analysis_digest: str
    source_id: str
    source_digest: str
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    outcome: PortfolioReviewDecisionOutcome
    rationale: str
    reviewed_by: str
    reviewed_timestamp: pd.Timestamp
    notes: tuple[str, ...]
    warnings: tuple[str, ...]
    decision_digest: str

    __init__ = _reject_public_construction

    def _payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_DECISION_ARTIFACT_SCHEMA_VERSION
            ),
            "decision_id": self.decision_id,
            "decision_scope": self.decision_scope,
            "review_id": self.review_id,
            "analysis_digest": self.analysis_digest,
            "source_id": self.source_id,
            "source_digest": self.source_digest,
            "baseline_scenario_id": self.baseline_scenario_id,
            "baseline_scenario_digest": self.baseline_scenario_digest,
            "proposed_scenario_id": self.proposed_scenario_id,
            "proposed_scenario_digest": self.proposed_scenario_digest,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "reviewed_by": self.reviewed_by,
            "reviewed_timestamp": self.reviewed_timestamp.isoformat(),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the normalized decision payload and canonical digest."""
        payload = self._payload_without_digest()
        payload["decision_digest"] = self.decision_digest
        return payload


def _new_decision_artifact(
    **values: object,
) -> PortfolioReviewDecisionArtifact:
    result = object.__new__(PortfolioReviewDecisionArtifact)
    for field_name, value in values.items():
        object.__setattr__(result, field_name, value)
    object.__setattr__(
        result,
        "decision_digest",
        _canonical_digest(result._payload_without_digest()),
    )
    return result


def create_portfolio_review_decision_artifact(
    *,
    decision_id: str,
    analysis: PortfolioReviewAnalysisArtifact,
    outcome: str,
    rationale: str,
    reviewed_by: str,
    reviewed_timestamp: object,
    notes: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> PortfolioReviewDecisionArtifact:
    """Create governance-only evidence linked to one exact analysis digest."""
    if type(analysis) is not PortfolioReviewAnalysisArtifact:
        raise ValueError(
            "analysis must be a PortfolioReviewAnalysisArtifact"
        )
    return _new_decision_artifact(
        decision_id=_normalize_required_string(decision_id, "decision_id"),
        decision_scope=PORTFOLIO_REVIEW_DECISION_SCOPE,
        review_id=analysis.review_id,
        analysis_digest=analysis.analysis_digest,
        source_id=analysis.source_id,
        source_digest=analysis.source_digest,
        baseline_scenario_id=analysis.baseline_scenario_id,
        baseline_scenario_digest=analysis.baseline_scenario_digest,
        proposed_scenario_id=analysis.proposed_scenario_id,
        proposed_scenario_digest=analysis.proposed_scenario_digest,
        outcome=_normalize_outcome(outcome),
        rationale=_normalize_required_string(rationale, "rationale"),
        reviewed_by=_normalize_required_string(reviewed_by, "reviewed_by"),
        reviewed_timestamp=_normalize_utc_timestamp(
            reviewed_timestamp,
            "reviewed_timestamp",
        ),
        notes=_normalize_string_sequence(notes, "notes"),
        warnings=_normalize_string_sequence(warnings, "warnings"),
    )
