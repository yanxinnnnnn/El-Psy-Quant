"""Path-free response contract for the installed Founder Demo Workspace."""

from typing import Literal

from pydantic import BaseModel

from el_psy_quant.api.lifecycle_command_schemas import (
    LifecycleTransitionProposalCommandRequest,
    LifecycleTransitionReviewCommandRequest,
)
from el_psy_quant.api.paper_run_schemas import PaperRunCommandRequest


class DemoResearchRunReferenceResponse(BaseModel):
    experiment_slug: str
    run_id: str


class DemoEvidenceManifestReferenceResponse(BaseModel):
    manifest_type: Literal[
        "strategy_decision_manifest",
        "report_artifact_manifest",
        "strategy_review_workflow_manifest",
    ]
    artifact_key: str


class DemoPaperJobReferenceResponse(BaseModel):
    job_id: str
    run_id: str


class DemoPaperJobSubmissionExampleResponse(BaseModel):
    idempotency_key: str
    request: PaperRunCommandRequest


class DemoWorkspaceDescriptorResponse(BaseModel):
    schema_version: Literal[1]
    dataset_id: str
    dataset_version: int
    display_name: str
    warning: str
    canonical_strategy_name: str
    research_run: DemoResearchRunReferenceResponse
    evidence_manifests: list[DemoEvidenceManifestReferenceResponse]
    paper_jobs: list[DemoPaperJobReferenceResponse]
    comparison_candidate_job_ids: list[str]
    lifecycle_proposal_example: LifecycleTransitionProposalCommandRequest
    lifecycle_review_example: LifecycleTransitionReviewCommandRequest
    paper_job_submission_example: DemoPaperJobSubmissionExampleResponse
