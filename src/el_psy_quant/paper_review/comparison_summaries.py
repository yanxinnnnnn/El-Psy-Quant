"""Paper run comparison summary contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.paper_review.comparison_inputs import PaperRunComparisonInput

PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION = 1


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


def _validate_comparison_input(
    comparison_input: PaperRunComparisonInput,
) -> PaperRunComparisonInput:
    if not isinstance(comparison_input, PaperRunComparisonInput):
        raise ValueError("comparison_input must be a PaperRunComparisonInput")
    return comparison_input


@dataclass(frozen=True)
class PaperRunComparisonSummary:
    """Immutable descriptive summary for a paper run comparison input."""

    summary_id: str
    comparison_input: PaperRunComparisonInput
    comparison_facts: Sequence[str]
    assumptions: Sequence[str] = ()
    warnings: Sequence[str] = ()
    missing_evidence: Sequence[str] = ()
    created_by: str | None = None
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "summary_id",
            _normalize_required_string(self.summary_id, "summary_id"),
        )
        object.__setattr__(
            self,
            "comparison_input",
            _validate_comparison_input(self.comparison_input),
        )
        object.__setattr__(
            self,
            "comparison_facts",
            _normalize_required_string_sequence(
                self.comparison_facts,
                "comparison_facts",
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
            "created_by",
            _normalize_optional_string(self.created_by, "created_by"),
        )
        object.__setattr__(
            self,
            "created_timestamp",
            _normalize_optional_timestamp(self.created_timestamp),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible comparison summary export."""
        return {
            "schema_version": PAPER_RUN_COMPARISON_SUMMARY_SCHEMA_VERSION,
            "summary_id": self.summary_id,
            "comparison_input": self.comparison_input.to_dict(),
            "comparison_facts": list(self.comparison_facts),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "missing_evidence": list(self.missing_evidence),
            "created_by": self.created_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
        }


def create_paper_run_comparison_summary(
    *,
    summary_id: str,
    comparison_input: PaperRunComparisonInput,
    comparison_facts: Sequence[str],
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
    missing_evidence: Sequence[str] = (),
    created_by: str | None = None,
    created_timestamp: object | None = None,
) -> PaperRunComparisonSummary:
    """Create and validate one descriptive paper run comparison summary."""
    return PaperRunComparisonSummary(
        summary_id=summary_id,
        comparison_input=comparison_input,
        comparison_facts=comparison_facts,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
        created_by=created_by,
        created_timestamp=created_timestamp,
    )
