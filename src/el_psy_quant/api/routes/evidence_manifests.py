"""Versioned configured evidence-manifest inspection routes."""

from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Request

from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.evidence_schemas import (
    EvidenceManifestDetailResponse,
    EvidenceManifestListResponse,
    EvidenceManifestReferenceResponse,
    EvidenceManifestSummaryResponse,
    ReportArtifactManifestDetailResponse,
    StrategyDecisionManifestDetailResponse,
    StrategyReviewWorkflowManifestDetailResponse,
)
from el_psy_quant.application import (
    EvidenceArtifactInvalidError,
    EvidenceArtifactRootUnavailableError,
    EvidenceManifestDetail,
    EvidenceManifestNotFoundError,
    EvidenceManifestReference,
    EvidenceManifestSummary,
    ReportArtifactManifestDetail,
    StrategyDecisionManifestDetail,
    StrategyReviewWorkflowManifestDetail,
    get_evidence_manifest_detail,
    list_evidence_manifests,
)

router = APIRouter(prefix="/evidence-manifests")


def _public_error(error: Exception) -> PublicApiError:
    if isinstance(error, EvidenceArtifactRootUnavailableError):
        return PublicApiError(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            code="evidence_artifact_root_unavailable",
            message="Evidence artifact root is unavailable",
        )
    if isinstance(error, EvidenceManifestNotFoundError):
        return PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="evidence_manifest_not_found",
            message="Evidence manifest not found",
        )
    return PublicApiError(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="evidence_artifact_invalid",
        message="Evidence artifact is invalid",
    )


def _artifact_root(request: Request) -> Path:
    root = request.app.state.evidence_artifact_root
    if root is None:
        raise _public_error(
            EvidenceArtifactRootUnavailableError("evidence artifact root unavailable")
        )
    return root


def _reference_response(
    reference: EvidenceManifestReference,
) -> EvidenceManifestReferenceResponse:
    return EvidenceManifestReferenceResponse(
        schema_version=reference.schema_version,
        reference_type=reference.reference_type,
        reference_id=reference.reference_id,
        label=reference.label,
        description=reference.description,
    )


def _summary_response(
    summary: EvidenceManifestSummary,
) -> EvidenceManifestSummaryResponse:
    return EvidenceManifestSummaryResponse(
        manifest_type=summary.manifest_type,
        artifact_key=summary.artifact_key,
        manifest_id=summary.manifest_id,
        reference_count=summary.reference_count,
        created_by=summary.created_by,
        created_timestamp=summary.created_timestamp,
        label=summary.label,
        description=summary.description,
    )


def _detail_response(detail: EvidenceManifestDetail) -> EvidenceManifestDetailResponse:
    if isinstance(detail, StrategyDecisionManifestDetail):
        return StrategyDecisionManifestDetailResponse(
            manifest_type=detail.manifest_type,
            artifact_key=detail.artifact_key,
            schema_version=detail.schema_version,
            manifest_id=detail.manifest_id,
            summary_references=[
                _reference_response(reference)
                for reference in detail.summary_references
            ],
            record_references=[
                _reference_response(reference) for reference in detail.record_references
            ],
            created_by=detail.created_by,
            created_timestamp=detail.created_timestamp,
            description=detail.description,
        )
    if isinstance(detail, ReportArtifactManifestDetail):
        return ReportArtifactManifestDetailResponse(
            manifest_type=detail.manifest_type,
            artifact_key=detail.artifact_key,
            schema_version=detail.schema_version,
            manifest_id=detail.manifest_id,
            references=[
                _reference_response(reference) for reference in detail.references
            ],
            label=detail.label,
            description=detail.description,
            created_by=detail.created_by,
            created_timestamp=detail.created_timestamp,
            notes=detail.notes,
        )
    if isinstance(detail, StrategyReviewWorkflowManifestDetail):
        return StrategyReviewWorkflowManifestDetailResponse(
            manifest_type=detail.manifest_type,
            artifact_key=detail.artifact_key,
            schema_version=detail.schema_version,
            manifest_id=detail.manifest_id,
            state_snapshot_references=[
                _reference_response(reference)
                for reference in detail.state_snapshot_references
            ],
            transition_proposal_references=[
                _reference_response(reference)
                for reference in detail.transition_proposal_references
            ],
            transition_record_references=[
                _reference_response(reference)
                for reference in detail.transition_record_references
            ],
            created_by=detail.created_by,
            created_timestamp=detail.created_timestamp,
            description=detail.description,
        )
    raise TypeError("unsupported evidence manifest detail")


@router.get("", response_model=EvidenceManifestListResponse)
async def get_evidence_manifests(request: Request) -> EvidenceManifestListResponse:
    """List direct validated evidence manifests in fixed category order."""
    try:
        manifests = list_evidence_manifests(artifact_root=_artifact_root(request))
    except (
        EvidenceArtifactRootUnavailableError,
        EvidenceArtifactInvalidError,
    ) as exc:
        raise _public_error(exc) from exc
    return EvidenceManifestListResponse(
        manifests=[_summary_response(summary) for summary in manifests]
    )


@router.get(
    "/{manifest_type}/{artifact_key}",
    response_model=EvidenceManifestDetailResponse,
)
async def get_evidence_manifest(
    request: Request,
    manifest_type: str,
    artifact_key: str,
) -> EvidenceManifestDetailResponse:
    """Read one exact evidence manifest without resolving its references."""
    try:
        detail = get_evidence_manifest_detail(
            artifact_root=_artifact_root(request),
            manifest_type=manifest_type,
            artifact_key=artifact_key,
        )
    except (
        EvidenceArtifactRootUnavailableError,
        EvidenceManifestNotFoundError,
        EvidenceArtifactInvalidError,
    ) as exc:
        raise _public_error(exc) from exc
    return _detail_response(detail)
