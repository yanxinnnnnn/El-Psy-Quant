"""Strategy review workflow compact reference and manifest contracts."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from el_psy_quant.strategy_review.state_snapshots import (
    StrategyLifecycleStateSnapshot,
)
from el_psy_quant.strategy_review.transition_proposals import (
    StrategyLifecycleTransitionProposal,
)
from el_psy_quant.strategy_review.transition_records import (
    StrategyLifecycleTransitionRecord,
)

STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION = 1
STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION = 1

SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES = (
    "strategy_lifecycle_state_snapshot",
    "strategy_lifecycle_transition_proposal",
    "strategy_lifecycle_transition_record",
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
            "created_timestamp must be convertible to a pandas Timestamp"
        ) from exc
    if pd.isna(result):
        raise ValueError("created_timestamp must be valid")
    return result


def _reference_type(value: str) -> str:
    normalized = _required(value, "reference_type")
    if normalized not in SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES:
        supported = ", ".join(SUPPORTED_STRATEGY_REVIEW_WORKFLOW_REFERENCE_TYPES)
        raise ValueError(f"unsupported reference_type: {value}; supported: {supported}")
    return normalized


@dataclass(frozen=True)
class StrategyReviewWorkflowReference:
    """Immutable compact pointer to one Milestone 24 lifecycle artifact."""

    reference_type: str
    reference_id: str
    label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference_type", _reference_type(self.reference_type))
        object.__setattr__(
            self, "reference_id", _required(self.reference_id, "reference_id")
        )
        object.__setattr__(self, "label", _optional(self.label, "label"))
        object.__setattr__(
            self, "description", _optional(self.description, "description")
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible compact reference."""
        return {
            "schema_version": STRATEGY_REVIEW_WORKFLOW_REFERENCE_SCHEMA_VERSION,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "label": self.label,
            "description": self.description,
        }


def _references(
    values: Sequence[StrategyReviewWorkflowReference],
    name: str,
    expected_type: str,
) -> tuple[StrategyReviewWorkflowReference, ...]:
    if isinstance(values, StrategyReviewWorkflowReference):
        raise ValueError(f"{name} must be a sequence of references")
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of references")
    result = tuple(values)
    for reference in result:
        if not isinstance(reference, StrategyReviewWorkflowReference):
            raise ValueError(
                f"{name} must contain only StrategyReviewWorkflowReference objects"
            )
        if reference.reference_type != expected_type:
            raise ValueError(f"{name} must contain only {expected_type} references")
    return result


@dataclass(frozen=True)
class StrategyReviewWorkflowManifest:
    """Immutable local index of explicit lifecycle artifact references."""

    manifest_id: str
    state_snapshot_references: Sequence[StrategyReviewWorkflowReference] = ()
    transition_proposal_references: Sequence[StrategyReviewWorkflowReference] = ()
    transition_record_references: Sequence[StrategyReviewWorkflowReference] = ()
    created_by: str | None = None
    created_timestamp: object | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        snapshots = _references(
            self.state_snapshot_references,
            "state_snapshot_references",
            "strategy_lifecycle_state_snapshot",
        )
        proposals = _references(
            self.transition_proposal_references,
            "transition_proposal_references",
            "strategy_lifecycle_transition_proposal",
        )
        records = _references(
            self.transition_record_references,
            "transition_record_references",
            "strategy_lifecycle_transition_record",
        )
        if not snapshots and not proposals and not records:
            raise ValueError("manifest must include at least one workflow reference")
        object.__setattr__(
            self, "manifest_id", _required(self.manifest_id, "manifest_id")
        )
        object.__setattr__(self, "state_snapshot_references", snapshots)
        object.__setattr__(self, "transition_proposal_references", proposals)
        object.__setattr__(self, "transition_record_references", records)
        object.__setattr__(self, "created_by", _optional(self.created_by, "created_by"))
        object.__setattr__(
            self, "created_timestamp", _timestamp(self.created_timestamp)
        )
        object.__setattr__(
            self, "description", _optional(self.description, "description")
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible workflow manifest."""
        return {
            "schema_version": STRATEGY_REVIEW_WORKFLOW_MANIFEST_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "state_snapshot_references": [
                reference.to_dict() for reference in self.state_snapshot_references
            ],
            "transition_proposal_references": [
                reference.to_dict() for reference in self.transition_proposal_references
            ],
            "transition_record_references": [
                reference.to_dict() for reference in self.transition_record_references
            ],
            "created_by": self.created_by,
            "created_timestamp": None
            if self.created_timestamp is None
            else self.created_timestamp.isoformat(),
            "description": self.description,
        }


def create_strategy_review_workflow_reference(
    *,
    reference_type: str,
    reference_id: str,
    label: str | None = None,
    description: str | None = None,
) -> StrategyReviewWorkflowReference:
    """Create and validate one compact lifecycle artifact reference."""
    return StrategyReviewWorkflowReference(
        reference_type=reference_type,
        reference_id=reference_id,
        label=label,
        description=description,
    )


def create_strategy_review_workflow_manifest(
    *,
    manifest_id: str,
    state_snapshot_references: Sequence[StrategyReviewWorkflowReference] = (),
    transition_proposal_references: Sequence[StrategyReviewWorkflowReference] = (),
    transition_record_references: Sequence[StrategyReviewWorkflowReference] = (),
    created_by: str | None = None,
    created_timestamp: object | None = None,
    description: str | None = None,
) -> StrategyReviewWorkflowManifest:
    """Create and validate one local workflow reference manifest."""
    return StrategyReviewWorkflowManifest(
        manifest_id=manifest_id,
        state_snapshot_references=state_snapshot_references,
        transition_proposal_references=transition_proposal_references,
        transition_record_references=transition_record_references,
        created_by=created_by,
        created_timestamp=created_timestamp,
        description=description,
    )


def create_strategy_review_workflow_reference_from_state_snapshot(
    *,
    snapshot: StrategyLifecycleStateSnapshot,
    label: str | None = None,
    description: str | None = None,
) -> StrategyReviewWorkflowReference:
    """Reference an existing state snapshot by its stable ID only."""
    if not isinstance(snapshot, StrategyLifecycleStateSnapshot):
        raise ValueError("snapshot must be a StrategyLifecycleStateSnapshot")
    return create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_state_snapshot",
        reference_id=snapshot.snapshot_id,
        label=label,
        description=description,
    )


def create_strategy_review_workflow_reference_from_transition_proposal(
    *,
    proposal: StrategyLifecycleTransitionProposal,
    label: str | None = None,
    description: str | None = None,
) -> StrategyReviewWorkflowReference:
    """Reference an existing transition proposal by its stable ID only."""
    if not isinstance(proposal, StrategyLifecycleTransitionProposal):
        raise ValueError("proposal must be a StrategyLifecycleTransitionProposal")
    return create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_transition_proposal",
        reference_id=proposal.proposal_id,
        label=label,
        description=description,
    )


def create_strategy_review_workflow_reference_from_transition_record(
    *,
    record: StrategyLifecycleTransitionRecord,
    label: str | None = None,
    description: str | None = None,
) -> StrategyReviewWorkflowReference:
    """Reference an existing transition record by its stable ID only."""
    if not isinstance(record, StrategyLifecycleTransitionRecord):
        raise ValueError("record must be a StrategyLifecycleTransitionRecord")
    return create_strategy_review_workflow_reference(
        reference_type="strategy_lifecycle_transition_record",
        reference_id=record.transition_record_id,
        label=label,
        description=description,
    )
