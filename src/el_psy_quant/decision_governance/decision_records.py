"""Strategy decision record contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.decision_governance.decision_summaries import (
    StrategyDecisionSummary,
)

STRATEGY_DECISION_RECORD_SCHEMA_VERSION = 1

SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES = (
    "needs_more_evidence",
    "approved_for_continued_paper_review",
    "rejected_for_now",
    "put_on_hold",
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


def _normalize_optional_timestamp(
    reviewed_timestamp: object | None,
) -> pd.Timestamp | None:
    if reviewed_timestamp is None:
        return None
    try:
        normalized = pd.Timestamp(reviewed_timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "reviewed_timestamp must be convertible to a pandas Timestamp"
        ) from exc

    if pd.isna(normalized):
        raise ValueError("reviewed_timestamp must be valid")
    return normalized


def _normalize_decision_status(decision_status: str) -> str:
    normalized = _normalize_required_string(decision_status, "decision_status")
    if normalized not in SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES:
        supported = ", ".join(SUPPORTED_STRATEGY_DECISION_RECORD_STATUSES)
        raise ValueError(
            f"unsupported decision_status: {decision_status}; supported: {supported}"
        )
    return normalized


def _normalize_string_sequence(
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


def _validate_decision_summary(
    decision_summary: StrategyDecisionSummary,
) -> StrategyDecisionSummary:
    if not isinstance(decision_summary, StrategyDecisionSummary):
        raise ValueError("decision_summary must be a StrategyDecisionSummary")
    return decision_summary


@dataclass(frozen=True)
class StrategyDecisionRecord:
    """Immutable human-controlled strategy decision record."""

    decision_id: str
    decision_summary: StrategyDecisionSummary
    decision_status: str
    rationale: str
    reviewed_by: str | None = None
    reviewed_timestamp: object | None = None
    notes: Sequence[str] = ()
    warnings: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decision_id",
            _normalize_required_string(self.decision_id, "decision_id"),
        )
        object.__setattr__(
            self,
            "decision_summary",
            _validate_decision_summary(self.decision_summary),
        )
        object.__setattr__(
            self,
            "decision_status",
            _normalize_decision_status(self.decision_status),
        )
        object.__setattr__(
            self,
            "rationale",
            _normalize_required_string(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "reviewed_by",
            _normalize_optional_string(self.reviewed_by, "reviewed_by"),
        )
        object.__setattr__(
            self,
            "reviewed_timestamp",
            _normalize_optional_timestamp(self.reviewed_timestamp),
        )
        object.__setattr__(
            self,
            "notes",
            _normalize_string_sequence(self.notes, "notes"),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalize_string_sequence(self.warnings, "warnings"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible strategy decision record."""
        return {
            "schema_version": STRATEGY_DECISION_RECORD_SCHEMA_VERSION,
            "decision_id": self.decision_id,
            "decision_summary": self.decision_summary.to_dict(),
            "decision_status": self.decision_status,
            "rationale": self.rationale,
            "reviewed_by": self.reviewed_by,
            "reviewed_timestamp": (
                None
                if self.reviewed_timestamp is None
                else self.reviewed_timestamp.isoformat()
            ),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def create_strategy_decision_record(
    *,
    decision_id: str,
    decision_summary: StrategyDecisionSummary,
    decision_status: str,
    rationale: str,
    reviewed_by: str | None = None,
    reviewed_timestamp: object | None = None,
    notes: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> StrategyDecisionRecord:
    """Create and validate one human-controlled strategy decision record."""
    return StrategyDecisionRecord(
        decision_id=decision_id,
        decision_summary=decision_summary,
        decision_status=decision_status,
        rationale=rationale,
        reviewed_by=reviewed_by,
        reviewed_timestamp=reviewed_timestamp,
        notes=notes,
        warnings=warnings,
    )
