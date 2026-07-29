"""Path-free response contract for the installed Founder Demo Workspace."""

from typing import Literal

from pydantic import BaseModel

from el_psy_quant.api.lifecycle_command_schemas import (
    LifecycleTransitionProposalCommandRequest,
    LifecycleTransitionReviewCommandRequest,
)
from el_psy_quant.api.paper_run_schemas import PaperRunCommandRequest
from el_psy_quant.api.portfolio_review_schemas import PortfolioReviewCreateRequest


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


class DemoPortfolioReviewExampleResponse(BaseModel):
    create_idempotency_key: str
    request: PortfolioReviewCreateRequest


class DemoPaperAccountReferenceResponse(BaseModel):
    account_id: str
    head_version: int
    event_types: list[
        Literal[
            "account_created",
            "cash_movement_posted",
            "position_adjustment_posted",
            "account_frozen",
            "account_reactivated",
        ]
    ]
    snapshot_id: str
    reconciliation_id: str


class DemoMarketTimeCheckpointResponse(BaseModel):
    status: Literal["paused"]
    position: int
    last_event_id: str
    current_time: str


class DemoMarketTimeRecoveryResponse(BaseModel):
    remaining_event_ids: list[str]
    final_status: Literal["completed"]
    final_position: int
    last_event_id: str
    current_time: str


class DemoMarketTimeReferenceResponse(BaseModel):
    calendar_id: str
    session_ids: list[str]
    replay_id: str
    event_count: int
    event_stream_digest: str
    checkpoint: DemoMarketTimeCheckpointResponse
    recovery: DemoMarketTimeRecoveryResponse


class DemoWorkspaceDescriptorResponse(BaseModel):
    schema_version: Literal[4]
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
    portfolio_review_example: DemoPortfolioReviewExampleResponse
    paper_account: DemoPaperAccountReferenceResponse
    market_time: DemoMarketTimeReferenceResponse
