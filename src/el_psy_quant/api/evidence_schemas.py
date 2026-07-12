"""Explicit evidence-manifest inspection response schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

EvidenceManifestType = Literal[
    "strategy_decision_manifest",
    "report_artifact_manifest",
    "strategy_review_workflow_manifest",
]


class EvidenceManifestReferenceResponse(BaseModel):
    schema_version: Literal[1]
    reference_type: str
    reference_id: str
    label: str | None
    description: str | None


class EvidenceManifestSummaryResponse(BaseModel):
    manifest_type: EvidenceManifestType
    artifact_key: str
    manifest_id: str
    reference_count: int
    created_by: str | None
    created_timestamp: str | None
    label: str | None
    description: str | None


class EvidenceManifestListResponse(BaseModel):
    manifests: list[EvidenceManifestSummaryResponse]


class StrategyDecisionManifestDetailResponse(BaseModel):
    manifest_type: Literal["strategy_decision_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    summary_references: list[EvidenceManifestReferenceResponse]
    record_references: list[EvidenceManifestReferenceResponse]
    created_by: str | None
    created_timestamp: str | None
    description: str | None


class ReportArtifactManifestDetailResponse(BaseModel):
    manifest_type: Literal["report_artifact_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    references: list[EvidenceManifestReferenceResponse]
    label: str | None
    description: str | None
    created_by: str | None
    created_timestamp: str | None
    notes: str | None


class StrategyReviewWorkflowManifestDetailResponse(BaseModel):
    manifest_type: Literal["strategy_review_workflow_manifest"]
    artifact_key: str
    schema_version: Literal[1]
    manifest_id: str
    state_snapshot_references: list[EvidenceManifestReferenceResponse]
    transition_proposal_references: list[EvidenceManifestReferenceResponse]
    transition_record_references: list[EvidenceManifestReferenceResponse]
    created_by: str | None
    created_timestamp: str | None
    description: str | None


EvidenceManifestDetailResponse = Annotated[
    StrategyDecisionManifestDetailResponse
    | ReportArtifactManifestDetailResponse
    | StrategyReviewWorkflowManifestDetailResponse,
    Field(discriminator="manifest_type"),
]
