"""Strategy decision summary contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.decision_governance.decision_inputs import (
    StrategyDecisionInput,
)

STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION = 1


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


def _normalize_string_sequence(
    values: Sequence[str],
    field_name: str,
    *,
    allow_empty: bool,
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

    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _validate_decision_input(
    decision_input: StrategyDecisionInput,
) -> StrategyDecisionInput:
    if not isinstance(decision_input, StrategyDecisionInput):
        raise ValueError("decision_input must be a StrategyDecisionInput")
    return decision_input


@dataclass(frozen=True)
class StrategyDecisionSummary:
    """Immutable caller-supplied descriptive summary for a strategy decision."""

    summary_id: str
    decision_input: StrategyDecisionInput
    decision_facts: Sequence[str]
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
            "decision_input",
            _validate_decision_input(self.decision_input),
        )
        object.__setattr__(
            self,
            "decision_facts",
            _normalize_string_sequence(
                self.decision_facts,
                "decision_facts",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _normalize_string_sequence(
                self.assumptions,
                "assumptions",
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalize_string_sequence(
                self.warnings,
                "warnings",
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "missing_evidence",
            _normalize_string_sequence(
                self.missing_evidence,
                "missing_evidence",
                allow_empty=True,
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
        """Return a deterministic JSON-compatible strategy decision summary."""
        return {
            "schema_version": STRATEGY_DECISION_SUMMARY_SCHEMA_VERSION,
            "summary_id": self.summary_id,
            "decision_input": self.decision_input.to_dict(),
            "decision_facts": list(self.decision_facts),
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


def create_strategy_decision_summary(
    *,
    summary_id: str,
    decision_input: StrategyDecisionInput,
    decision_facts: Sequence[str],
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
    missing_evidence: Sequence[str] = (),
    created_by: str | None = None,
    created_timestamp: object | None = None,
) -> StrategyDecisionSummary:
    """Create and validate one caller-supplied strategy decision summary."""
    return StrategyDecisionSummary(
        summary_id=summary_id,
        decision_input=decision_input,
        decision_facts=decision_facts,
        assumptions=assumptions,
        warnings=warnings,
        missing_evidence=missing_evidence,
        created_by=created_by,
        created_timestamp=created_timestamp,
    )
