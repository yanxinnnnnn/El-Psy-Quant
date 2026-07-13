"""Explicit lifecycle proposal and human-review API schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr


class _LifecycleCommandRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrategyReviewEvidenceReferenceCommandRequest(
    _LifecycleCommandRequestModel
):
    reference_type: StrictStr
    reference_id: StrictStr
    label: StrictStr | None = None
    description: StrictStr | None = None


class StrategyLifecycleStateSnapshotCommandRequest(
    _LifecycleCommandRequestModel
):
    snapshot_id: StrictStr
    strategy_id: StrictStr
    lifecycle_state: StrictStr
    rationale: StrictStr
    declared_by: StrictStr | None = None
    declared_timestamp: StrictStr | None = None
    notes: list[StrictStr]
    warnings: list[StrictStr]


class LifecycleTransitionProposalCommandRequest(_LifecycleCommandRequestModel):
    proposal_id: StrictStr
    source_snapshot: StrategyLifecycleStateSnapshotCommandRequest
    target_state: StrictStr
    rationale: StrictStr
    evidence_references: list[StrategyReviewEvidenceReferenceCommandRequest]
    requested_by: StrictStr | None = None
    requested_timestamp: StrictStr | None = None
    notes: list[StrictStr]
    warnings: list[StrictStr]


class LifecycleTransitionReviewCommandRequest(_LifecycleCommandRequestModel):
    transition_record_id: StrictStr
    proposal: LifecycleTransitionProposalCommandRequest
    review_outcome: StrictStr
    rationale: StrictStr
    resulting_snapshot: StrategyLifecycleStateSnapshotCommandRequest | None = None
    reviewed_by: StrictStr | None = None
    reviewed_timestamp: StrictStr | None = None
    notes: list[StrictStr]
    warnings: list[StrictStr]


class StrategyReviewEvidenceReferenceResponse(BaseModel):
    schema_version: Literal[1]
    reference_type: str
    reference_id: str
    label: str | None
    description: str | None


class StrategyLifecycleStateSnapshotResponse(BaseModel):
    schema_version: Literal[1]
    snapshot_id: str
    strategy_id: str
    lifecycle_state: str
    rationale: str
    declared_by: str | None
    declared_timestamp: str | None
    notes: list[str]
    warnings: list[str]


class StrategyLifecycleTransitionProposalResponse(BaseModel):
    schema_version: Literal[1]
    proposal_id: str
    source_snapshot: StrategyLifecycleStateSnapshotResponse
    target_state: str
    rationale: str
    evidence_references: list[StrategyReviewEvidenceReferenceResponse]
    requested_by: str | None
    requested_timestamp: str | None
    notes: list[str]
    warnings: list[str]


class StrategyLifecycleTransitionRecordResponse(BaseModel):
    schema_version: Literal[1]
    transition_record_id: str
    proposal: StrategyLifecycleTransitionProposalResponse
    review_outcome: str
    rationale: str
    resulting_snapshot: StrategyLifecycleStateSnapshotResponse | None
    reviewed_by: str | None
    reviewed_timestamp: str | None
    notes: list[str]
    warnings: list[str]


class LifecycleTransitionProposalCommandResponse(BaseModel):
    proposal: StrategyLifecycleTransitionProposalResponse


class LifecycleTransitionReviewCommandResponse(BaseModel):
    transition_record: StrategyLifecycleTransitionRecordResponse
