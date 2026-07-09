"""Strategy decision manifest and reference contracts."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.decision_governance.decision_records import (
    StrategyDecisionRecord,
)
from el_psy_quant.decision_governance.decision_summaries import (
    StrategyDecisionSummary,
)

STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION = 1
STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION = 1

SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES = (
    "strategy_decision_summary",
    "strategy_decision_record",
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


def _normalize_reference_type(reference_type: str) -> str:
    normalized = _normalize_required_string(reference_type, "reference_type")
    if normalized not in SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_STRATEGY_DECISION_REFERENCE_TYPES)
        raise ValueError(
            f"unsupported reference_type: {reference_type}; supported: {supported}"
        )
    return normalized


@dataclass(frozen=True)
class StrategyDecisionReference:
    """Immutable local reference to a strategy decision summary or record."""

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
        """Return a deterministic JSON-compatible strategy decision reference."""
        return {
            "schema_version": STRATEGY_DECISION_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def _normalize_reference_sequence(
    references: Sequence[StrategyDecisionReference],
    field_name: str,
    expected_reference_type: str,
) -> tuple[StrategyDecisionReference, ...]:
    if isinstance(references, StrategyDecisionReference):
        raise ValueError(f"{field_name} must be a sequence of references")
    if isinstance(references, str) or not isinstance(references, Sequence):
        raise ValueError(f"{field_name} must be a sequence of references")

    normalized = tuple(references)
    for reference in normalized:
        if not isinstance(reference, StrategyDecisionReference):
            raise ValueError(
                f"{field_name} must contain only StrategyDecisionReference objects"
            )
        if reference.reference_type != expected_reference_type:
            raise ValueError(
                f"{field_name} must contain only {expected_reference_type} references"
            )
    return normalized


@dataclass(frozen=True)
class StrategyDecisionManifest:
    """Immutable local manifest of strategy decision summaries and records."""

    manifest_id: str
    summary_references: Sequence[StrategyDecisionReference] = ()
    record_references: Sequence[StrategyDecisionReference] = ()
    created_by: str | None = None
    created_timestamp: object | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_id",
            _normalize_required_string(self.manifest_id, "manifest_id"),
        )
        summary_references = _normalize_reference_sequence(
            self.summary_references,
            "summary_references",
            "strategy_decision_summary",
        )
        record_references = _normalize_reference_sequence(
            self.record_references,
            "record_references",
            "strategy_decision_record",
        )
        if not summary_references and not record_references:
            raise ValueError(
                "manifest must include at least one summary or record reference"
            )
        object.__setattr__(self, "summary_references", summary_references)
        object.__setattr__(self, "record_references", record_references)
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
        """Return a deterministic JSON-compatible strategy decision manifest."""
        return {
            "schema_version": STRATEGY_DECISION_MANIFEST_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "summary_references": [
                reference.to_dict() for reference in self.summary_references
            ],
            "record_references": [
                reference.to_dict() for reference in self.record_references
            ],
            "created_by": self.created_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
            "description": self.description,
        }


def create_strategy_decision_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> StrategyDecisionReference:
    """Create and validate one strategy decision reference."""
    return StrategyDecisionReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )


def create_strategy_decision_manifest(
    *,
    manifest_id: str,
    summary_references: Sequence[StrategyDecisionReference] = (),
    record_references: Sequence[StrategyDecisionReference] = (),
    created_by: str | None = None,
    created_timestamp: object | None = None,
    description: str | None = None,
) -> StrategyDecisionManifest:
    """Create and validate one local strategy decision manifest."""
    return StrategyDecisionManifest(
        manifest_id=manifest_id,
        summary_references=summary_references,
        record_references=record_references,
        created_by=created_by,
        created_timestamp=created_timestamp,
        description=description,
    )


def create_strategy_decision_reference_from_summary(
    summary: StrategyDecisionSummary,
    *,
    label: str | None = None,
    description: str | None = None,
) -> StrategyDecisionReference:
    """Create a strategy decision summary reference from a summary object."""
    if not isinstance(summary, StrategyDecisionSummary):
        raise ValueError("summary must be a StrategyDecisionSummary")
    return create_strategy_decision_reference(
        reference_type="strategy_decision_summary",
        reference_id=summary.summary_id,
        label=label,
        description=description,
    )


def create_strategy_decision_reference_from_record(
    record: StrategyDecisionRecord,
    *,
    label: str | None = None,
    description: str | None = None,
) -> StrategyDecisionReference:
    """Create a strategy decision record reference from a record object."""
    if not isinstance(record, StrategyDecisionRecord):
        raise ValueError("record must be a StrategyDecisionRecord")
    return create_strategy_decision_reference(
        reference_type="strategy_decision_record",
        reference_id=record.decision_id,
        label=label,
        description=description,
    )
