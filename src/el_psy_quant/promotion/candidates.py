"""Paper promotion candidate contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.promotion.source_references import PromotionSourceReference

PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION = 1


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


def _normalize_source_references(
    source_references: Sequence[PromotionSourceReference],
) -> tuple[PromotionSourceReference, ...]:
    if isinstance(source_references, PromotionSourceReference):
        raise ValueError(
            "source_references must be a non-empty sequence of "
            "PromotionSourceReference objects"
        )
    if isinstance(source_references, str) or not isinstance(
        source_references,
        Sequence,
    ):
        raise ValueError(
            "source_references must be a non-empty sequence of "
            "PromotionSourceReference objects"
        )

    normalized = tuple(source_references)
    if not normalized:
        raise ValueError("source_references must not be empty")

    for source_reference in normalized:
        if not isinstance(source_reference, PromotionSourceReference):
            raise ValueError(
                "source_references must contain only PromotionSourceReference "
                "objects"
            )
    return normalized


@dataclass(frozen=True)
class PaperPromotionCandidate:
    """Immutable explicit paper promotion candidate for manual review."""

    candidate_id: str
    source_references: Sequence[PromotionSourceReference]
    title: str
    rationale: str | None = None
    proposed_by: str | None = None
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_id",
            _normalize_required_string(self.candidate_id, "candidate_id"),
        )
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(
            self,
            "title",
            _normalize_required_string(self.title, "title"),
        )
        object.__setattr__(
            self,
            "rationale",
            _normalize_optional_string(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "proposed_by",
            _normalize_optional_string(self.proposed_by, "proposed_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible candidate export."""
        return {
            "schema_version": PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION,
            "candidate_id": self.candidate_id,
            "title": self.title,
            "rationale": self.rationale,
            "proposed_by": self.proposed_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
            "source_references": [
                source_reference.to_dict()
                for source_reference in self.source_references
            ],
        }


def create_paper_promotion_candidate(
    *,
    candidate_id: str,
    source_references: Sequence[PromotionSourceReference],
    title: str,
    rationale: str | None = None,
    proposed_by: str | None = None,
    created_timestamp: object | None = None,
) -> PaperPromotionCandidate:
    """Create and validate one explicit paper promotion candidate."""
    return PaperPromotionCandidate(
        candidate_id=candidate_id,
        source_references=source_references,
        title=title,
        rationale=rationale,
        proposed_by=proposed_by,
        created_timestamp=created_timestamp,
    )
