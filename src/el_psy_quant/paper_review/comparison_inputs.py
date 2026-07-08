"""Paper run comparison input contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.paper_review.references import PaperRunReference

PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION = 1


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


def _normalize_optional_timestamp(created_timestamp: object | None) -> pd.Timestamp | None:
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


def _normalize_paper_run_references(
    paper_run_references: Sequence[PaperRunReference],
) -> tuple[PaperRunReference, ...]:
    if isinstance(paper_run_references, PaperRunReference):
        raise ValueError(
            "paper_run_references must be a non-empty sequence of "
            "PaperRunReference objects"
        )
    if isinstance(paper_run_references, str) or not isinstance(
        paper_run_references,
        Sequence,
    ):
        raise ValueError(
            "paper_run_references must be a non-empty sequence of "
            "PaperRunReference objects"
        )

    normalized = tuple(paper_run_references)
    if not normalized:
        raise ValueError("paper_run_references must not be empty")

    for paper_run_reference in normalized:
        if not isinstance(paper_run_reference, PaperRunReference):
            raise ValueError(
                "paper_run_references must contain only PaperRunReference objects"
            )
    return normalized


@dataclass(frozen=True)
class PaperRunComparisonInput:
    """Immutable explicit input set for paper run comparison review."""

    comparison_id: str
    paper_run_references: Sequence[PaperRunReference]
    purpose: str
    review_context: str | None = None
    requested_by: str | None = None
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "comparison_id",
            _normalize_required_string(self.comparison_id, "comparison_id"),
        )
        object.__setattr__(
            self,
            "paper_run_references",
            _normalize_paper_run_references(self.paper_run_references),
        )
        object.__setattr__(
            self,
            "purpose",
            _normalize_required_string(self.purpose, "purpose"),
        )
        object.__setattr__(
            self,
            "review_context",
            _normalize_optional_string(self.review_context, "review_context"),
        )
        object.__setattr__(
            self,
            "requested_by",
            _normalize_optional_string(self.requested_by, "requested_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible comparison input export."""
        return {
            "schema_version": PAPER_RUN_COMPARISON_INPUT_SCHEMA_VERSION,
            "comparison_id": self.comparison_id,
            "paper_run_references": [
                reference.to_dict() for reference in self.paper_run_references
            ],
            "purpose": self.purpose,
            "review_context": self.review_context,
            "requested_by": self.requested_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
        }


def create_paper_run_comparison_input(
    *,
    comparison_id: str,
    paper_run_references: Sequence[PaperRunReference],
    purpose: str,
    review_context: str | None = None,
    requested_by: str | None = None,
    created_timestamp: object | None = None,
) -> PaperRunComparisonInput:
    """Create and validate one explicit paper run comparison input."""
    return PaperRunComparisonInput(
        comparison_id=comparison_id,
        paper_run_references=paper_run_references,
        purpose=purpose,
        review_context=review_context,
        requested_by=requested_by,
        created_timestamp=created_timestamp,
    )
