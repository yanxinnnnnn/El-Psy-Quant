"""Synchronous in-memory strategy lifecycle application commands."""

from dataclasses import dataclass
from typing import Literal

from el_psy_quant.strategy_review import (
    STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION,
    STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION,
    STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION,
    STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
    StrategyLifecycleStateSnapshot,
    StrategyLifecycleTransitionProposal,
    StrategyLifecycleTransitionRecord,
    StrategyReviewEvidenceReference,
    create_strategy_lifecycle_state_snapshot,
    create_strategy_lifecycle_transition_proposal,
    create_strategy_lifecycle_transition_record,
    create_strategy_review_evidence_reference,
)

_INVALID_PROPOSAL_MESSAGE = "lifecycle transition proposal is invalid"
_INVALID_RECORD_MESSAGE = "lifecycle transition record is invalid"


def _immutable_tuple(values: object) -> object:
    if isinstance(values, (list, tuple)):
        return tuple(values)
    return values


class LifecycleTransitionProposalInvalidError(Exception):
    """Sanitized failure for one invalid lifecycle proposal command."""

    def __init__(self) -> None:
        super().__init__(_INVALID_PROPOSAL_MESSAGE)


class LifecycleTransitionRecordInvalidError(Exception):
    """Sanitized failure for one invalid lifecycle review command."""

    def __init__(self) -> None:
        super().__init__(_INVALID_RECORD_MESSAGE)


@dataclass(frozen=True)
class StrategyReviewEvidenceReferenceCommandInput:
    """Transport values for one unresolved evidence pointer."""

    reference_type: object
    reference_id: object
    label: object | None = None
    description: object | None = None


@dataclass(frozen=True)
class StrategyLifecycleStateSnapshotCommandInput:
    """Transport values for one caller-supplied lifecycle snapshot."""

    snapshot_id: object
    strategy_id: object
    lifecycle_state: object
    rationale: object
    declared_by: object | None = None
    declared_timestamp: object | None = None
    notes: tuple[object, ...] = ()
    warnings: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", _immutable_tuple(self.notes))
        object.__setattr__(self, "warnings", _immutable_tuple(self.warnings))


@dataclass(frozen=True)
class LifecycleTransitionProposalCommand:
    """Explicit non-executing request for one lifecycle transition."""

    proposal_id: object
    source_snapshot: StrategyLifecycleStateSnapshotCommandInput
    target_state: object
    rationale: object
    evidence_references: tuple[StrategyReviewEvidenceReferenceCommandInput, ...]
    requested_by: object | None = None
    requested_timestamp: object | None = None
    notes: tuple[object, ...] = ()
    warnings: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_references",
            _immutable_tuple(self.evidence_references),
        )
        object.__setattr__(self, "notes", _immutable_tuple(self.notes))
        object.__setattr__(self, "warnings", _immutable_tuple(self.warnings))


@dataclass(frozen=True)
class LifecycleTransitionReviewCommand:
    """Explicit human review of one complete caller-supplied proposal."""

    transition_record_id: object
    proposal: LifecycleTransitionProposalCommand
    review_outcome: object
    rationale: object
    resulting_snapshot: StrategyLifecycleStateSnapshotCommandInput | None = None
    reviewed_by: object | None = None
    reviewed_timestamp: object | None = None
    notes: tuple[object, ...] = ()
    warnings: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", _immutable_tuple(self.notes))
        object.__setattr__(self, "warnings", _immutable_tuple(self.warnings))


@dataclass(frozen=True)
class StrategyReviewEvidenceReferenceView:
    schema_version: Literal[1]
    reference_type: str
    reference_id: str
    label: str | None
    description: str | None


@dataclass(frozen=True)
class StrategyLifecycleStateSnapshotView:
    schema_version: Literal[1]
    snapshot_id: str
    strategy_id: str
    lifecycle_state: str
    rationale: str
    declared_by: str | None
    declared_timestamp: str | None
    notes: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class StrategyLifecycleTransitionProposalView:
    schema_version: Literal[1]
    proposal_id: str
    source_snapshot: StrategyLifecycleStateSnapshotView
    target_state: str
    rationale: str
    evidence_references: tuple[StrategyReviewEvidenceReferenceView, ...]
    requested_by: str | None
    requested_timestamp: str | None
    notes: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class StrategyLifecycleTransitionRecordView:
    schema_version: Literal[1]
    transition_record_id: str
    proposal: StrategyLifecycleTransitionProposalView
    review_outcome: str
    rationale: str
    resulting_snapshot: StrategyLifecycleStateSnapshotView | None
    reviewed_by: str | None
    reviewed_timestamp: str | None
    notes: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LifecycleTransitionProposalCommandResult:
    proposal: StrategyLifecycleTransitionProposalView


@dataclass(frozen=True)
class LifecycleTransitionReviewCommandResult:
    transition_record: StrategyLifecycleTransitionRecordView


def _require_proposal_nested_types(
    command: LifecycleTransitionProposalCommand,
    error_type: type[
        LifecycleTransitionProposalInvalidError
        | LifecycleTransitionRecordInvalidError
    ],
) -> None:
    if type(command.source_snapshot) is not StrategyLifecycleStateSnapshotCommandInput:
        raise error_type()
    if type(command.evidence_references) is not tuple:
        raise error_type()
    if any(
        type(reference) is not StrategyReviewEvidenceReferenceCommandInput
        for reference in command.evidence_references
    ):
        raise error_type()


def _snapshot(
    command: StrategyLifecycleStateSnapshotCommandInput,
) -> StrategyLifecycleStateSnapshot:
    return create_strategy_lifecycle_state_snapshot(
        snapshot_id=command.snapshot_id,  # type: ignore[arg-type]
        strategy_id=command.strategy_id,  # type: ignore[arg-type]
        lifecycle_state=command.lifecycle_state,  # type: ignore[arg-type]
        rationale=command.rationale,  # type: ignore[arg-type]
        declared_by=command.declared_by,  # type: ignore[arg-type]
        declared_timestamp=command.declared_timestamp,
        notes=command.notes,  # type: ignore[arg-type]
        warnings=command.warnings,  # type: ignore[arg-type]
    )


def _evidence_reference(
    command: StrategyReviewEvidenceReferenceCommandInput,
) -> StrategyReviewEvidenceReference:
    return create_strategy_review_evidence_reference(
        reference_type=command.reference_type,  # type: ignore[arg-type]
        reference_id=command.reference_id,  # type: ignore[arg-type]
        label=command.label,  # type: ignore[arg-type]
        description=command.description,  # type: ignore[arg-type]
    )


def _proposal(
    command: LifecycleTransitionProposalCommand,
) -> StrategyLifecycleTransitionProposal:
    source_snapshot = _snapshot(command.source_snapshot)
    evidence_references = tuple(
        _evidence_reference(reference) for reference in command.evidence_references
    )
    return create_strategy_lifecycle_transition_proposal(
        proposal_id=command.proposal_id,  # type: ignore[arg-type]
        source_snapshot=source_snapshot,
        target_state=command.target_state,  # type: ignore[arg-type]
        rationale=command.rationale,  # type: ignore[arg-type]
        evidence_references=evidence_references,
        requested_by=command.requested_by,  # type: ignore[arg-type]
        requested_timestamp=command.requested_timestamp,
        notes=command.notes,  # type: ignore[arg-type]
        warnings=command.warnings,  # type: ignore[arg-type]
    )


def _evidence_view(
    reference: StrategyReviewEvidenceReference,
) -> StrategyReviewEvidenceReferenceView:
    return StrategyReviewEvidenceReferenceView(
        schema_version=STRATEGY_REVIEW_EVIDENCE_REFERENCE_SCHEMA_VERSION,
        reference_type=reference.reference_type,
        reference_id=reference.reference_id,
        label=reference.label,
        description=reference.description,
    )


def _snapshot_view(
    snapshot: StrategyLifecycleStateSnapshot,
) -> StrategyLifecycleStateSnapshotView:
    return StrategyLifecycleStateSnapshotView(
        schema_version=STRATEGY_LIFECYCLE_STATE_SNAPSHOT_SCHEMA_VERSION,
        snapshot_id=snapshot.snapshot_id,
        strategy_id=snapshot.strategy_id,
        lifecycle_state=snapshot.lifecycle_state,
        rationale=snapshot.rationale,
        declared_by=snapshot.declared_by,
        declared_timestamp=(
            None
            if snapshot.declared_timestamp is None
            else snapshot.declared_timestamp.isoformat()
        ),
        notes=snapshot.notes,
        warnings=snapshot.warnings,
    )


def _proposal_view(
    proposal: StrategyLifecycleTransitionProposal,
) -> StrategyLifecycleTransitionProposalView:
    return StrategyLifecycleTransitionProposalView(
        schema_version=STRATEGY_LIFECYCLE_TRANSITION_PROPOSAL_SCHEMA_VERSION,
        proposal_id=proposal.proposal_id,
        source_snapshot=_snapshot_view(proposal.source_snapshot),
        target_state=proposal.target_state,
        rationale=proposal.rationale,
        evidence_references=tuple(
            _evidence_view(reference) for reference in proposal.evidence_references
        ),
        requested_by=proposal.requested_by,
        requested_timestamp=(
            None
            if proposal.requested_timestamp is None
            else proposal.requested_timestamp.isoformat()
        ),
        notes=proposal.notes,
        warnings=proposal.warnings,
    )


def _record_view(
    record: StrategyLifecycleTransitionRecord,
) -> StrategyLifecycleTransitionRecordView:
    return StrategyLifecycleTransitionRecordView(
        schema_version=STRATEGY_LIFECYCLE_TRANSITION_RECORD_SCHEMA_VERSION,
        transition_record_id=record.transition_record_id,
        proposal=_proposal_view(record.proposal),
        review_outcome=record.review_outcome,
        rationale=record.rationale,
        resulting_snapshot=(
            None
            if record.resulting_snapshot is None
            else _snapshot_view(record.resulting_snapshot)
        ),
        reviewed_by=record.reviewed_by,
        reviewed_timestamp=(
            None
            if record.reviewed_timestamp is None
            else record.reviewed_timestamp.isoformat()
        ),
        notes=record.notes,
        warnings=record.warnings,
    )


def create_lifecycle_transition_proposal(
    *,
    command: LifecycleTransitionProposalCommand,
) -> LifecycleTransitionProposalCommandResult:
    """Create one normalized non-executing proposal only in memory."""
    if type(command) is not LifecycleTransitionProposalCommand:
        raise LifecycleTransitionProposalInvalidError()
    _require_proposal_nested_types(command, LifecycleTransitionProposalInvalidError)
    try:
        proposal = _proposal(command)
    except ValueError as exc:
        raise LifecycleTransitionProposalInvalidError() from exc
    return LifecycleTransitionProposalCommandResult(
        proposal=_proposal_view(proposal)
    )


def record_lifecycle_transition_review(
    *,
    command: LifecycleTransitionReviewCommand,
) -> LifecycleTransitionReviewCommandResult:
    """Record one explicit human review outcome only in memory."""
    if type(command) is not LifecycleTransitionReviewCommand:
        raise LifecycleTransitionRecordInvalidError()
    if type(command.proposal) is not LifecycleTransitionProposalCommand:
        raise LifecycleTransitionRecordInvalidError()
    _require_proposal_nested_types(command.proposal, LifecycleTransitionRecordInvalidError)
    if (
        command.resulting_snapshot is not None
        and type(command.resulting_snapshot)
        is not StrategyLifecycleStateSnapshotCommandInput
    ):
        raise LifecycleTransitionRecordInvalidError()
    try:
        proposal = _proposal(command.proposal)
        resulting_snapshot = (
            None
            if command.resulting_snapshot is None
            else _snapshot(command.resulting_snapshot)
        )
        record = create_strategy_lifecycle_transition_record(
            transition_record_id=command.transition_record_id,  # type: ignore[arg-type]
            proposal=proposal,
            review_outcome=command.review_outcome,  # type: ignore[arg-type]
            rationale=command.rationale,  # type: ignore[arg-type]
            resulting_snapshot=resulting_snapshot,
            reviewed_by=command.reviewed_by,  # type: ignore[arg-type]
            reviewed_timestamp=command.reviewed_timestamp,
            notes=command.notes,  # type: ignore[arg-type]
            warnings=command.warnings,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        raise LifecycleTransitionRecordInvalidError() from exc
    return LifecycleTransitionReviewCommandResult(
        transition_record=_record_view(record)
    )
