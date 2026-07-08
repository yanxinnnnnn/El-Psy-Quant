"""Paper review manifest and compact reference contracts."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.paper_review.comparison_summaries import PaperRunComparisonSummary
from el_psy_quant.paper_review.review_decisions import PaperRunReviewDecision

PAPER_REVIEW_REFERENCE_SCHEMA_VERSION = 1
PAPER_REVIEW_MANIFEST_SCHEMA_VERSION = 1

SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES = (
    "comparison_summary",
    "review_decision",
)


def _normalize_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_optional_string(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    normalized = value.strip()
    return normalized or None


def _normalize_reference_type(reference_type: str) -> str:
    if not isinstance(reference_type, str):
        raise ValueError("reference_type must be a string")
    normalized = reference_type.strip()
    if normalized not in SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_PAPER_REVIEW_REFERENCE_TYPES)
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


def _normalize_optional_timestamp(
    created_timestamp: object | None,
) -> pd.Timestamp | None:
    if created_timestamp is None:
        return None
    try:
        normalized = pd.Timestamp(created_timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "created_timestamp must be convertible to a pandas Timestamp"
        ) from exc

    if pd.isna(normalized):
        raise ValueError("created_timestamp must be valid")
    return normalized


@dataclass(frozen=True)
class PaperReviewReference:
    """Immutable compact reference to a paper review-layer record."""

    reference_type: str
    reference_id: str
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_type",
            _normalize_reference_type(self.reference_type),
        )
        object.__setattr__(
            self,
            "reference_id",
            _normalize_required_string(self.reference_id, "reference_id"),
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
        """Return a deterministic JSON-compatible review reference export."""
        return {
            "schema_version": PAPER_REVIEW_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def _normalize_reference_sequence(
    references: Sequence[PaperReviewReference],
    field_name: str,
    expected_reference_type: str,
) -> tuple[PaperReviewReference, ...]:
    if isinstance(references, PaperReviewReference):
        raise ValueError(
            f"{field_name} must be a sequence of PaperReviewReference objects"
        )
    if isinstance(references, str) or not isinstance(references, Sequence):
        raise ValueError(
            f"{field_name} must be a sequence of PaperReviewReference objects"
        )

    normalized = tuple(references)
    for reference in normalized:
        if not isinstance(reference, PaperReviewReference):
            raise ValueError(
                f"{field_name} must contain only PaperReviewReference objects"
            )
        if reference.reference_type != expected_reference_type:
            raise ValueError(
                f"{field_name} must contain only {expected_reference_type} references"
            )
    return normalized


@dataclass(frozen=True)
class PaperReviewManifest:
    """Immutable local manifest of paper review references."""

    manifest_id: str
    comparison_references: Sequence[PaperReviewReference] = ()
    decision_references: Sequence[PaperReviewReference] = ()
    created_by: str | None = None
    created_timestamp: object | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        comparison_references = _normalize_reference_sequence(
            self.comparison_references,
            "comparison_references",
            "comparison_summary",
        )
        decision_references = _normalize_reference_sequence(
            self.decision_references,
            "decision_references",
            "review_decision",
        )
        if not comparison_references and not decision_references:
            raise ValueError(
                "manifest must contain at least one comparison or decision reference"
            )

        object.__setattr__(
            self,
            "manifest_id",
            _normalize_required_string(self.manifest_id, "manifest_id"),
        )
        object.__setattr__(self, "comparison_references", comparison_references)
        object.__setattr__(self, "decision_references", decision_references)
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by, "created_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )
        object.__setattr__(
            self,
            "description",
            _normalize_optional_string(self.description, "description"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible review manifest export."""
        return {
            "schema_version": PAPER_REVIEW_MANIFEST_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "comparison_references": [
                reference.to_dict() for reference in self.comparison_references
            ],
            "decision_references": [
                reference.to_dict() for reference in self.decision_references
            ],
            "created_by": self.created_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
            "description": self.description,
        }


def create_paper_review_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> PaperReviewReference:
    """Create and validate one compact paper review reference."""
    return PaperReviewReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )


def create_paper_review_manifest(
    *,
    manifest_id: str,
    comparison_references: Sequence[PaperReviewReference] = (),
    decision_references: Sequence[PaperReviewReference] = (),
    created_by: str | None = None,
    created_timestamp: object | None = None,
    description: str | None = None,
) -> PaperReviewManifest:
    """Create and validate one local paper review manifest."""
    return PaperReviewManifest(
        manifest_id=manifest_id,
        comparison_references=comparison_references,
        decision_references=decision_references,
        created_by=created_by,
        created_timestamp=created_timestamp,
        description=description,
    )


def create_paper_review_reference_from_summary(
    summary: PaperRunComparisonSummary,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PaperReviewReference:
    """Create a compact review reference from an existing comparison summary."""
    if not isinstance(summary, PaperRunComparisonSummary):
        raise ValueError("summary must be a PaperRunComparisonSummary")
    return create_paper_review_reference(
        reference_type="comparison_summary",
        reference_id=summary.summary_id,
        label=label,
        description=description,
    )


def create_paper_review_reference_from_decision(
    decision: PaperRunReviewDecision,
    *,
    label: str | None = None,
    description: str | None = None,
) -> PaperReviewReference:
    """Create a compact review reference from an existing review decision."""
    if not isinstance(decision, PaperRunReviewDecision):
        raise ValueError("decision must be a PaperRunReviewDecision")
    return create_paper_review_reference(
        reference_type="review_decision",
        reference_id=decision.decision_id,
        label=label,
        description=description,
    )
