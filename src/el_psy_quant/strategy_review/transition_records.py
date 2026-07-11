"""Human-controlled lifecycle transition record contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.strategy_review.state_snapshots import (
    StrategyLifecycleStateSnapshot,
)
from el_psy_quant.strategy_review.transition_proposals import (
    StrategyLifecycleTransitionProposal,
)

STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION = 1
SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES = (
    "approved",
    "rejected",
    "deferred",
)


def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string when provided")
    return value.strip() or None


def _timestamp(value: object | None) -> pd.Timestamp | None:
    if value is None:
        return None
    try:
        result = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "reviewed_timestamp must be convertible to a pandas Timestamp"
        ) from exc
    if pd.isna(result):
        raise ValueError("reviewed_timestamp must be valid")
    return result


def _strings(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of non-empty strings")
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must contain only non-empty strings")
        result.append(value.strip())
    return tuple(result)


def _outcome(value: str) -> str:
    normalized = _required(value, "review_outcome")
    if normalized not in SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES:
        supported = ", ".join(SUPPORTED_STRATEGY_LIFECYCLE_TRANSITION_RECORD_OUTCOMES)
        raise ValueError(f"unsupported review_outcome: {value}; supported: {supported}")
    return normalized


@dataclass(frozen=True)
class StrategyLifecycleTransitionRecord:
    """Immutable caller-supplied record of an explicit human review outcome."""

    transition_record_id: str
    proposal: StrategyLifecycleTransitionProposal
    review_outcome: str
    rationale: str
    resulting_snapshot: StrategyLifecycleStateSnapshot | None = None
    reviewed_by: str | None = None
    reviewed_timestamp: object | None = None
    notes: Sequence[str] = ()
    warnings: Sequence[str] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.proposal, StrategyLifecycleTransitionProposal):
            raise ValueError("proposal must be a StrategyLifecycleTransitionProposal")
        outcome = _outcome(self.review_outcome)
        snapshot = self.resulting_snapshot
        if outcome == "approved":
            if not isinstance(snapshot, StrategyLifecycleStateSnapshot):
                raise ValueError(
                    "approved records require resulting_snapshot to be a "
                    "StrategyLifecycleStateSnapshot"
                )
            if snapshot.strategy_id != self.proposal.source_snapshot.strategy_id:
                raise ValueError(
                    "resulting_snapshot strategy_id must match the proposal strategy"
                )
            if snapshot.lifecycle_state != self.proposal.target_state:
                raise ValueError(
                    "resulting_snapshot lifecycle_state must match proposal target_state"
                )
        elif snapshot is not None:
            raise ValueError(
                "rejected and deferred records must not include resulting_snapshot"
            )

        object.__setattr__(
            self,
            "transition_record_id",
            _required(self.transition_record_id, "transition_record_id"),
        )
        object.__setattr__(self, "review_outcome", outcome)
        object.__setattr__(self, "rationale", _required(self.rationale, "rationale"))
        object.__setattr__(
            self, "reviewed_by", _optional(self.reviewed_by, "reviewed_by")
        )
        object.__setattr__(
            self, "reviewed_timestamp", _timestamp(self.reviewed_timestamp)
        )
        object.__setattr__(self, "notes", _strings(self.notes, "notes"))
        object.__setattr__(self, "warnings", _strings(self.warnings, "warnings"))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible transition record."""
        return {
            "schema_version": STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION,
            "transition_record_id": self.transition_record_id,
            "proposal": self.proposal.to_dict(),
            "review_outcome": self.review_outcome,
            "rationale": self.rationale,
            "resulting_snapshot": None
            if self.resulting_snapshot is None
            else self.resulting_snapshot.to_dict(),
            "reviewed_by": self.reviewed_by,
            "reviewed_timestamp": None
            if self.reviewed_timestamp is None
            else self.reviewed_timestamp.isoformat(),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def create_strategy_lifecycle_transition_record(
    *,
    transition_record_id: str,
    proposal: StrategyLifecycleTransitionProposal,
    review_outcome: str,
    rationale: str,
    resulting_snapshot: StrategyLifecycleStateSnapshot | None = None,
    reviewed_by: str | None = None,
    reviewed_timestamp: object | None = None,
    notes: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> StrategyLifecycleTransitionRecord:
    """Create one non-executing human lifecycle review record."""
    return StrategyLifecycleTransitionRecord(
        transition_record_id=transition_record_id,
        proposal=proposal,
        review_outcome=review_outcome,
        rationale=rationale,
        resulting_snapshot=resulting_snapshot,
        reviewed_by=reviewed_by,
        reviewed_timestamp=reviewed_timestamp,
        notes=notes,
        warnings=warnings,
    )
