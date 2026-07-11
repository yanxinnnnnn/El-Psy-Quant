"""Lifecycle transition proposal contract."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.strategy_review.evidence_references import (
    StrategyReviewEvidenceReference,
)
from el_psy_quant.strategy_review.state_snapshots import (
    SUPPORTED_STRATEGY_LIFECYCLE_STATES,
    StrategyLifecycleStateSnapshot,
)

STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION = 1
PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS = (
    ("research_review", "paper_review"),
    ("research_review", "watchlist"),
    ("research_review", "on_hold"),
    ("research_review", "rejected"),
    ("paper_review", "research_review"),
    ("paper_review", "watchlist"),
    ("paper_review", "on_hold"),
    ("paper_review", "rejected"),
    ("watchlist", "research_review"),
    ("watchlist", "paper_review"),
    ("watchlist", "on_hold"),
    ("watchlist", "rejected"),
    ("on_hold", "research_review"),
    ("on_hold", "paper_review"),
    ("on_hold", "watchlist"),
    ("on_hold", "rejected"),
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
            "requested_timestamp must be convertible to a pandas Timestamp"
        ) from exc
    if pd.isna(result):
        raise ValueError("requested_timestamp must be valid")
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


def _evidence(
    values: Sequence[StrategyReviewEvidenceReference],
) -> tuple[StrategyReviewEvidenceReference, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(
            "evidence_references must be a sequence of StrategyReviewEvidenceReference objects"
        )
    result = tuple(values)
    if not result or any(
        not isinstance(item, StrategyReviewEvidenceReference) for item in result
    ):
        raise ValueError(
            "evidence_references must contain only StrategyReviewEvidenceReference objects"
        )
    types = {item.reference_type for item in result}
    if "strategy_decision_record" not in types:
        raise ValueError("evidence_references must include a strategy_decision_record")
    return result


@dataclass(frozen=True)
class StrategyLifecycleTransitionProposal:
    """Immutable caller-supplied, non-executing lifecycle transition request."""

    proposal_id: str
    source_snapshot: StrategyLifecycleStateSnapshot
    target_state: str
    rationale: str
    evidence_references: Sequence[StrategyReviewEvidenceReference]
    requested_by: str | None = None
    requested_timestamp: object | None = None
    notes: Sequence[str] = ()
    warnings: Sequence[str] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_snapshot, StrategyLifecycleStateSnapshot):
            raise ValueError("source_snapshot must be a StrategyLifecycleStateSnapshot")
        target = _required(self.target_state, "target_state")
        if target not in SUPPORTED_STRATEGY_LIFECYCLE_STATES:
            raise ValueError(f"unsupported target_state: {self.target_state}")
        if (
            self.source_snapshot.lifecycle_state,
            target,
        ) not in PERMITTED_STRATEGY_LIFECYCLE_TRANSITIONS:
            raise ValueError("source and target states must be a permitted transition")
        evidence = _evidence(self.evidence_references)
        if target == "paper_review" and not any(
            item.reference_type == "promotion_record" for item in evidence
        ):
            raise ValueError("paper_review proposals must include a promotion_record")
        object.__setattr__(
            self, "proposal_id", _required(self.proposal_id, "proposal_id")
        )
        object.__setattr__(self, "target_state", target)
        object.__setattr__(self, "rationale", _required(self.rationale, "rationale"))
        object.__setattr__(self, "evidence_references", evidence)
        object.__setattr__(
            self, "requested_by", _optional(self.requested_by, "requested_by")
        )
        object.__setattr__(
            self, "requested_timestamp", _timestamp(self.requested_timestamp)
        )
        object.__setattr__(self, "notes", _strings(self.notes, "notes"))
        object.__setattr__(self, "warnings", _strings(self.warnings, "warnings"))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION,
            "proposal_id": self.proposal_id,
            "source_snapshot": self.source_snapshot.to_dict(),
            "target_state": self.target_state,
            "rationale": self.rationale,
            "evidence_references": [
                item.to_dict() for item in self.evidence_references
            ],
            "requested_by": self.requested_by,
            "requested_timestamp": None
            if self.requested_timestamp is None
            else self.requested_timestamp.isoformat(),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def create_strategy_lifecycle_transition_proposal(
    *,
    proposal_id: str,
    source_snapshot: StrategyLifecycleStateSnapshot,
    target_state: str,
    rationale: str,
    evidence_references: Sequence[StrategyReviewEvidenceReference],
    requested_by: str | None = None,
    requested_timestamp: object | None = None,
    notes: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> StrategyLifecycleTransitionProposal:
    """Create and validate one non-executing lifecycle transition proposal."""
    return StrategyLifecycleTransitionProposal(
        proposal_id=proposal_id,
        source_snapshot=source_snapshot,
        target_state=target_state,
        rationale=rationale,
        evidence_references=evidence_references,
        requested_by=requested_by,
        requested_timestamp=requested_timestamp,
        notes=notes,
        warnings=warnings,
    )
