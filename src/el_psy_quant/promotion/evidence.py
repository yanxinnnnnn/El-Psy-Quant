"""Promotion evidence summary contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.promotion.candidates import PaperPromotionCandidate

PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION = 1


def _normalize_required_string_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence of non-empty strings")

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must contain only non-empty strings"
            )
        normalized.append(value.strip())

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _normalize_optional_string_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence of non-empty strings")

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must contain only non-empty strings"
            )
        normalized.append(value.strip())
    return tuple(normalized)


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


def _validate_candidate(candidate: PaperPromotionCandidate) -> PaperPromotionCandidate:
    if not isinstance(candidate, PaperPromotionCandidate):
        raise ValueError("candidate must be a PaperPromotionCandidate")
    return candidate


@dataclass(frozen=True)
class PromotionEvidenceSummary:
    """Immutable descriptive evidence summary for a promotion candidate."""

    candidate: PaperPromotionCandidate
    source_facts: Sequence[str]
    assumptions: Sequence[str] = ()
    warnings: Sequence[str] = ()
    missing_evidence: Sequence[str] = ()
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate", _validate_candidate(self.candidate))
        object.__setattr__(
            self,
            "source_facts",
            _normalize_required_string_sequence(
                self.source_facts,
                "source_facts",
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _normalize_optional_string_sequence(
                self.assumptions,
                "assumptions",
            ),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalize_optional_string_sequence(
                self.warnings,
                "warnings",
            ),
        )
        object.__setattr__(
            self,
            "missing_evidence",
            _normalize_optional_string_sequence(
                self.missing_evidence,
                "missing_evidence",
            ),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible evidence summary export."""
        return {
            "schema_version": PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION,
            "candidate": self.candidate.to_dict(),
            "source_facts": list(self.source_facts),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "missing_evidence": list(self.missing_evidence),
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
        }


def create_promotion_evidence_summary(
    *,
    candidate: PaperPromotionCandidate,
    source_facts: Sequence[str],
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
    missing_evidence: Sequence[str] = (),
    created_timestamp: object | None = None,
) -> PromotionEvidenceSummary:
    """Create and validate one descriptive promotion evidence summary."""
    return PromotionEvidenceSummary(
        candidate=candidate,
        source_facts=source_facts,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
        created_timestamp=created_timestamp,
    )
