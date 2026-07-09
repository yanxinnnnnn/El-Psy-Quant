"""Strategy decision input contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.decision_governance.evidence_references import (
    DecisionEvidenceReference,
)

STRATEGY_DECISION_INPUT_SCHEMA_VERSION = 1


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


def _normalize_evidence_references(
    evidence_references: Sequence[DecisionEvidenceReference],
) -> tuple[DecisionEvidenceReference, ...]:
    if isinstance(evidence_references, DecisionEvidenceReference):
        raise ValueError(
            "evidence_references must be a non-empty sequence of "
            "DecisionEvidenceReference objects"
        )
    if isinstance(evidence_references, str) or not isinstance(
        evidence_references,
        Sequence,
    ):
        raise ValueError(
            "evidence_references must be a non-empty sequence of "
            "DecisionEvidenceReference objects"
        )

    normalized = tuple(evidence_references)
    if not normalized:
        raise ValueError("evidence_references must not be empty")

    for evidence_reference in normalized:
        if not isinstance(evidence_reference, DecisionEvidenceReference):
            raise ValueError(
                "evidence_references must contain only "
                "DecisionEvidenceReference objects"
            )
    return normalized


@dataclass(frozen=True)
class StrategyDecisionInput:
    """Immutable explicit input set for a future strategy-level decision."""

    input_id: str
    evidence_references: Sequence[DecisionEvidenceReference]
    decision_purpose: str
    strategy_id: str | None = None
    review_context: str | None = None
    created_by: str | None = None
    created_timestamp: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "input_id",
            _normalize_required_string(self.input_id, "input_id"),
        )
        object.__setattr__(
            self,
            "evidence_references",
            _normalize_evidence_references(self.evidence_references),
        )
        object.__setattr__(
            self,
            "decision_purpose",
            _normalize_required_string(
                self.decision_purpose,
                "decision_purpose",
            ),
        )
        object.__setattr__(
            self,
            "strategy_id",
            _normalize_optional_string(self.strategy_id, "strategy_id"),
        )
        object.__setattr__(
            self,
            "review_context",
            _normalize_optional_string(self.review_context, "review_context"),
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
        """Return a deterministic JSON-compatible strategy decision input export."""
        return {
            "schema_version": STRATEGY_DECISION_INPUT_SCHEMA_VERSION,
            "input_id": self.input_id,
            "evidence_references": [
                reference.to_dict() for reference in self.evidence_references
            ],
            "decision_purpose": self.decision_purpose,
            "strategy_id": self.strategy_id,
            "review_context": self.review_context,
            "created_by": self.created_by,
            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),
        }


def create_strategy_decision_input(
    *,
    input_id: str,
    evidence_references: Sequence[DecisionEvidenceReference],
    decision_purpose: str,
    strategy_id: str | None = None,
    review_context: str | None = None,
    created_by: str | None = None,
    created_timestamp: object | None = None,
) -> StrategyDecisionInput:
    """Create and validate one explicit strategy decision input."""
    return StrategyDecisionInput(
        input_id=input_id,
        evidence_references=evidence_references,
        decision_purpose=decision_purpose,
        strategy_id=strategy_id,
        review_context=review_context,
        created_by=created_by,
        created_timestamp=created_timestamp,
    )
