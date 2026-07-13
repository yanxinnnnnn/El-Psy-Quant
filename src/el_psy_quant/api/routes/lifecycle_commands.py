"""Versioned synchronous in-memory lifecycle command routes."""

from http import HTTPStatus

from fastapi import APIRouter

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.lifecycle_command_schemas import (
    LifecycleTransitionProposalCommandRequest,
    LifecycleTransitionProposalCommandResponse,
    LifecycleTransitionReviewCommandRequest,
    LifecycleTransitionReviewCommandResponse,
    StrategyLifecycleStateSnapshotCommandRequest,
    StrategyLifecycleStateSnapshotResponse,
    StrategyLifecycleTransitionProposalResponse,
    StrategyLifecycleTransitionRecordResponse,
    StrategyReviewEvidenceReferenceCommandRequest,
    StrategyReviewEvidenceReferenceResponse,
)
from el_psy_quant.application import (
    LifecycleTransitionProposalCommand,
    LifecycleTransitionProposalCommandResult,
    LifecycleTransitionProposalInvalidError,
    LifecycleTransitionRecordInvalidError,
    LifecycleTransitionReviewCommand,
    LifecycleTransitionReviewCommandResult,
    StrategyLifecycleStateSnapshotCommandInput,
    StrategyLifecycleStateSnapshotView,
    StrategyLifecycleTransitionProposalView,
    StrategyLifecycleTransitionRecordView,
    StrategyReviewEvidenceReferenceCommandInput,
    StrategyReviewEvidenceReferenceView,
    create_lifecycle_transition_proposal,
    record_lifecycle_transition_review,
)

router = APIRouter()


def _evidence_command(
    request: StrategyReviewEvidenceReferenceCommandRequest,
) -> StrategyReviewEvidenceReferenceCommandInput:
    return StrategyReviewEvidenceReferenceCommandInput(
        reference_type=request.reference_type,
        reference_id=request.reference_id,
        label=request.label,
        description=request.description,
    )


def _snapshot_command(
    request: StrategyLifecycleStateSnapshotCommandRequest,
) -> StrategyLifecycleStateSnapshotCommandInput:
    return StrategyLifecycleStateSnapshotCommandInput(
        snapshot_id=request.snapshot_id,
        strategy_id=request.strategy_id,
        lifecycle_state=request.lifecycle_state,
        rationale=request.rationale,
        declared_by=request.declared_by,
        declared_timestamp=request.declared_timestamp,
        notes=tuple(request.notes),
        warnings=tuple(request.warnings),
    )


def _proposal_command(
    request: LifecycleTransitionProposalCommandRequest,
) -> LifecycleTransitionProposalCommand:
    return LifecycleTransitionProposalCommand(
        proposal_id=request.proposal_id,
        source_snapshot=_snapshot_command(request.source_snapshot),
        target_state=request.target_state,
        rationale=request.rationale,
        evidence_references=tuple(
            _evidence_command(reference) for reference in request.evidence_references
        ),
        requested_by=request.requested_by,
        requested_timestamp=request.requested_timestamp,
        notes=tuple(request.notes),
        warnings=tuple(request.warnings),
    )


def _evidence_response(
    reference: StrategyReviewEvidenceReferenceView,
) -> StrategyReviewEvidenceReferenceResponse:
    return StrategyReviewEvidenceReferenceResponse(
        schema_version=reference.schema_version,
        reference_type=reference.reference_type,
        reference_id=reference.reference_id,
        label=reference.label,
        description=reference.description,
    )


def _snapshot_response(
    snapshot: StrategyLifecycleStateSnapshotView,
) -> StrategyLifecycleStateSnapshotResponse:
    return StrategyLifecycleStateSnapshotResponse(
        schema_version=snapshot.schema_version,
        snapshot_id=snapshot.snapshot_id,
        strategy_id=snapshot.strategy_id,
        lifecycle_state=snapshot.lifecycle_state,
        rationale=snapshot.rationale,
        declared_by=snapshot.declared_by,
        declared_timestamp=snapshot.declared_timestamp,
        notes=list(snapshot.notes),
        warnings=list(snapshot.warnings),
    )


def _proposal_response(
    proposal: StrategyLifecycleTransitionProposalView,
) -> StrategyLifecycleTransitionProposalResponse:
    return StrategyLifecycleTransitionProposalResponse(
        schema_version=proposal.schema_version,
        proposal_id=proposal.proposal_id,
        source_snapshot=_snapshot_response(proposal.source_snapshot),
        target_state=proposal.target_state,
        rationale=proposal.rationale,
        evidence_references=[
            _evidence_response(reference)
            for reference in proposal.evidence_references
        ],
        requested_by=proposal.requested_by,
        requested_timestamp=proposal.requested_timestamp,
        notes=list(proposal.notes),
        warnings=list(proposal.warnings),
    )


def _record_response(
    record: StrategyLifecycleTransitionRecordView,
) -> StrategyLifecycleTransitionRecordResponse:
    return StrategyLifecycleTransitionRecordResponse(
        schema_version=record.schema_version,
        transition_record_id=record.transition_record_id,
        proposal=_proposal_response(record.proposal),
        review_outcome=record.review_outcome,
        rationale=record.rationale,
        resulting_snapshot=(
            None
            if record.resulting_snapshot is None
            else _snapshot_response(record.resulting_snapshot)
        ),
        reviewed_by=record.reviewed_by,
        reviewed_timestamp=record.reviewed_timestamp,
        notes=list(record.notes),
        warnings=list(record.warnings),
    )


def _proposal_result_response(
    result: LifecycleTransitionProposalCommandResult,
) -> LifecycleTransitionProposalCommandResponse:
    return LifecycleTransitionProposalCommandResponse(
        proposal=_proposal_response(result.proposal)
    )


def _review_result_response(
    result: LifecycleTransitionReviewCommandResult,
) -> LifecycleTransitionReviewCommandResponse:
    return LifecycleTransitionReviewCommandResponse(
        transition_record=_record_response(result.transition_record)
    )


@router.post(
    "/lifecycle-transition-proposals",
    response_model=LifecycleTransitionProposalCommandResponse,
)
async def post_lifecycle_transition_proposal(
    request: LifecycleTransitionProposalCommandRequest,
) -> LifecycleTransitionProposalCommandResponse:
    """Create one normalized, non-executing lifecycle proposal in memory."""
    try:
        result = create_lifecycle_transition_proposal(
            command=_proposal_command(request)
        )
    except LifecycleTransitionProposalInvalidError as exc:
        raise PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="lifecycle_transition_proposal_invalid",
            message="Lifecycle transition proposal is invalid",
        ) from exc
    return _proposal_result_response(result)


@router.post(
    "/lifecycle-transition-records",
    response_model=LifecycleTransitionReviewCommandResponse,
)
async def post_lifecycle_transition_record(
    request: LifecycleTransitionReviewCommandRequest,
) -> LifecycleTransitionReviewCommandResponse:
    """Record one human review outcome as non-executing governance evidence."""
    command = LifecycleTransitionReviewCommand(
        transition_record_id=request.transition_record_id,
        proposal=_proposal_command(request.proposal),
        review_outcome=request.review_outcome,
        rationale=request.rationale,
        resulting_snapshot=(
            None
            if request.resulting_snapshot is None
            else _snapshot_command(request.resulting_snapshot)
        ),
        reviewed_by=request.reviewed_by,
        reviewed_timestamp=request.reviewed_timestamp,
        notes=tuple(request.notes),
        warnings=tuple(request.warnings),
    )
    try:
        result = record_lifecycle_transition_review(command=command)
    except LifecycleTransitionRecordInvalidError as exc:
        raise PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="lifecycle_transition_record_invalid",
            message="Lifecycle transition record is invalid",
        ) from exc
    return _review_result_response(result)
