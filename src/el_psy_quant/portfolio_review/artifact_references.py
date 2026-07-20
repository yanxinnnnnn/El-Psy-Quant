"""Immutable digest-bearing references to portfolio-review artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from el_psy_quant.portfolio_review.analysis_artifacts import (
    PortfolioReviewAnalysisArtifact,
)
from el_psy_quant.portfolio_review.decision_artifacts import (
    PortfolioReviewDecisionArtifact,
)
from el_psy_quant.portfolio_review.sources import PortfolioReviewSource

PORTFOLIO_REVIEW_ARTIFACT_REFERENCE_SCHEMA_VERSION = 1

SUPPORTED_PORTFOLIO_REVIEW_ARTIFACT_TYPES = (
    "portfolio_review_source",
    "portfolio_review_analysis",
    "portfolio_review_decision",
)

PortfolioReviewArtifactType = Literal[
    "portfolio_review_source",
    "portfolio_review_analysis",
    "portfolio_review_decision",
]


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_optional_string(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    normalized = value.strip()
    return normalized or None


def _normalize_artifact_type(value: str) -> PortfolioReviewArtifactType:
    normalized = _normalize_required_string(value, "artifact_type")
    if normalized not in SUPPORTED_PORTFOLIO_REVIEW_ARTIFACT_TYPES:
        supported = ", ".join(SUPPORTED_PORTFOLIO_REVIEW_ARTIFACT_TYPES)
        raise ValueError(
            f"unsupported artifact_type: {value}; supported: {supported}"
        )
    return normalized  # type: ignore[return-value]


def _normalize_digest(value: str) -> str:
    normalized = _normalize_required_string(value, "artifact_digest")
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(
            "artifact_digest must be a lowercase SHA-256 digest"
        )
    return normalized


@dataclass(frozen=True)
class PortfolioReviewArtifactReference:
    """Immutable ID-and-digest pointer to one portfolio-review artifact."""

    artifact_type: PortfolioReviewArtifactType
    artifact_id: str
    artifact_digest: str
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "artifact_type",
            _normalize_artifact_type(self.artifact_type),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _normalize_required_string(self.artifact_id, "artifact_id"),
        )
        object.__setattr__(
            self,
            "artifact_digest",
            _normalize_digest(self.artifact_digest),
        )
        object.__setattr__(
            self,
            "label",
            _normalize_optional_string(self.label, "label"),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_string(self.description, "description"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic strictly JSON-compatible reference."""
        return {
            "schema_version": (
                PORTFOLIO_REVIEW_ARTIFACT_REFERENCE_SCHEMA_VERSION
            ),
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "artifact_digest": self.artifact_digest,
            "label": self.label,
            "description": self.description,
        }


def create_portfolio_review_artifact_reference(
    *,
    artifact_type: str,
    artifact_id: str,
    artifact_digest: str,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewArtifactReference:
    """Create one validated portfolio-review artifact reference."""
    return PortfolioReviewArtifactReference(
        artifact_type=_normalize_artifact_type(artifact_type),
        artifact_id=artifact_id,
        artifact_digest=artifact_digest,
        label=label,
        description=description,
    )


def create_portfolio_review_artifact_reference_from_source(
    source: PortfolioReviewSource,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewArtifactReference:
    """Reference one exact Sprint 170 source by ID and digest."""
    if type(source) is not PortfolioReviewSource:
        raise ValueError("source must be a PortfolioReviewSource")
    return create_portfolio_review_artifact_reference(
        artifact_type="portfolio_review_source",
        artifact_id=source.source_id,
        artifact_digest=source.source_digest,
        label=label,
        description=description,
    )


def create_portfolio_review_artifact_reference_from_analysis(
    analysis: PortfolioReviewAnalysisArtifact,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewArtifactReference:
    """Reference one exact Sprint 173 analysis by review ID and digest."""
    if type(analysis) is not PortfolioReviewAnalysisArtifact:
        raise ValueError(
            "analysis must be a PortfolioReviewAnalysisArtifact"
        )
    return create_portfolio_review_artifact_reference(
        artifact_type="portfolio_review_analysis",
        artifact_id=analysis.review_id,
        artifact_digest=analysis.analysis_digest,
        label=label,
        description=description,
    )


def create_portfolio_review_artifact_reference_from_decision(
    decision: PortfolioReviewDecisionArtifact,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PortfolioReviewArtifactReference:
    """Reference one exact Sprint 173 decision by ID and digest."""
    if type(decision) is not PortfolioReviewDecisionArtifact:
        raise ValueError(
            "decision must be a PortfolioReviewDecisionArtifact"
        )
    return create_portfolio_review_artifact_reference(
        artifact_type="portfolio_review_decision",
        artifact_id=decision.decision_id,
        artifact_digest=decision.decision_digest,
        label=label,
        description=description,
    )
