"""Explicit request and response contracts for durable portfolio reviews."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


def _reject_boolean_numbers(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric value")
    return value


class PortfolioReviewEvidenceReferenceRequest(_StrictModel):
    reference_type: str
    reference_id: str
    label: str | None = None
    description: str | None = None


class PortfolioReviewComponentRequest(_StrictModel):
    component_id: str
    strategy_id: str
    evidence_references: list[PortfolioReviewEvidenceReferenceRequest]
    symbols: list[str] | None = None
    label: str | None = None
    description: str | None = None


class PortfolioReviewReturnObservationRequest(_StrictModel):
    timestamp: datetime
    component_returns: list[float]

    @field_validator("component_returns", mode="before")
    @classmethod
    def reject_boolean_returns(cls, value: object) -> object:
        if isinstance(value, list) and any(isinstance(item, bool) for item in value):
            raise ValueError("component returns must not be boolean")
        return value


class PortfolioReviewSourceRequest(_StrictModel):
    source_id: str
    components: list[PortfolioReviewComponentRequest]
    return_observations: list[PortfolioReviewReturnObservationRequest]
    evaluation_frequency: str
    periods_per_year: float | None = None
    created_by: str
    created_timestamp: datetime
    assumptions: list[str] = []
    warnings: list[str] = []
    missing_evidence: list[str] = []

    @field_validator("periods_per_year", mode="before")
    @classmethod
    def reject_boolean_periods(cls, value: object) -> object:
        return _reject_boolean_numbers(value)


class PortfolioReviewBaselineScenarioRequest(_StrictModel):
    scenario_id: str
    weights: dict[str, float]
    rationale: str
    assumptions: list[str] = []
    warnings: list[str] = []

    @field_validator("weights", mode="before")
    @classmethod
    def reject_boolean_weights(cls, value: object) -> object:
        if isinstance(value, dict) and any(
            isinstance(item, bool) for item in value.values()
        ):
            raise ValueError("weights must not be boolean")
        return value


class PortfolioReviewProposedScenarioRequest(
    PortfolioReviewBaselineScenarioRequest
):
    proposed_component_id: str


class PortfolioReviewAnalysisAuditRequest(_StrictModel):
    created_by: str
    created_timestamp: datetime
    assumptions: list[str] = []
    warnings: list[str] = []
    missing_evidence: list[str] = []


class PortfolioReviewCreateRequest(_StrictModel):
    review_id: str
    source: PortfolioReviewSourceRequest
    baseline_scenario: PortfolioReviewBaselineScenarioRequest
    proposed_scenario: PortfolioReviewProposedScenarioRequest
    analysis: PortfolioReviewAnalysisAuditRequest


class PortfolioReviewDecisionRequest(_StrictModel):
    decision_id: str
    outcome: Literal["approved", "rejected", "deferred"]
    rationale: str
    reviewed_by: str
    reviewed_timestamp: datetime
    notes: list[str] = []
    warnings: list[str] = []


class PortfolioReviewEvidenceReferenceResponse(_StrictModel):
    schema_version: Literal[1]
    reference_type: str
    reference_id: str
    label: str | None
    description: str | None


class PortfolioReviewComponentResponse(_StrictModel):
    schema_version: Literal[1]
    component_id: str
    strategy_id: str
    evidence_references: list[PortfolioReviewEvidenceReferenceResponse]
    symbols: list[str] | None
    label: str | None
    description: str | None


class PortfolioReviewReturnObservationResponse(_StrictModel):
    schema_version: Literal[1]
    timestamp: str
    component_returns: list[float]


class PortfolioReviewSourceResponse(_StrictModel):
    schema_version: Literal[1]
    source_id: str
    components: list[PortfolioReviewComponentResponse]
    return_observations: list[PortfolioReviewReturnObservationResponse]
    evaluation_frequency: str
    periods_per_year: float | None
    created_by: str
    created_timestamp: str
    assumptions: list[str]
    warnings: list[str]
    missing_evidence: list[str]
    source_digest: str


class PortfolioReviewComponentWeightResponse(_StrictModel):
    component_id: str
    weight: float


class PortfolioReviewBaselineScenarioResponse(_StrictModel):
    schema_version: Literal[1]
    scenario_id: str
    source_id: str
    source_digest: str
    component_weights: list[PortfolioReviewComponentWeightResponse]
    rationale: str
    assumptions: list[str]
    warnings: list[str]
    scenario_digest: str


class PortfolioReviewProposedScenarioResponse(
    PortfolioReviewBaselineScenarioResponse
):
    proposed_component_id: str


class PortfolioReviewScenarioConcentrationResponse(_StrictModel):
    schema_version: Literal[1]
    scenario_id: str
    scenario_digest: str
    largest_component_id: str
    largest_component_weight: float
    top_3_weight: float
    herfindahl_hirschman_index: float
    effective_component_count: float


class PortfolioReviewComponentExposureResponse(_StrictModel):
    schema_version: Literal[1]
    component_id: str
    strategy_id: str
    baseline_weight: float
    proposed_weight: float
    weight_delta: float
    change_type: Literal[
        "added", "removed", "increased", "decreased", "unchanged"
    ]
    baseline_active: bool
    proposed_active: bool
    symbols: list[str] | None
    symbol_evidence_status: Literal["available", "missing"]


class PortfolioReviewScenarioUniverseCoverageResponse(_StrictModel):
    schema_version: Literal[1]
    scenario_id: str
    scenario_digest: str
    components_with_symbol_evidence: list[str]
    components_missing_symbol_evidence: list[str]
    active_component_ids: list[str]
    active_components_with_symbol_evidence: list[str]
    active_components_missing_symbol_evidence: list[str]
    source_component_count: int
    components_with_symbol_evidence_count: int
    components_missing_symbol_evidence_count: int
    active_component_count: int
    active_components_with_symbol_evidence_count: int
    active_components_missing_symbol_evidence_count: int
    active_coverage_complete: bool


class PortfolioReviewConcentrationExposureAnalysisResponse(_StrictModel):
    schema_version: Literal[1]
    source_id: str
    source_digest: str
    component_ids: list[str]
    baseline_concentration: PortfolioReviewScenarioConcentrationResponse
    proposed_concentration: PortfolioReviewScenarioConcentrationResponse
    component_exposures: list[PortfolioReviewComponentExposureResponse]
    baseline_universe_coverage: PortfolioReviewScenarioUniverseCoverageResponse
    proposed_universe_coverage: PortfolioReviewScenarioUniverseCoverageResponse


class PortfolioReviewSymbolOverlapResponse(_StrictModel):
    schema_version: Literal[1]
    left_component_id: str
    right_component_id: str
    status: Literal["available", "unavailable"]
    unavailable_reason: Literal["missing_symbol_evidence"] | None
    missing_symbol_component_ids: list[str]
    shared_symbols: list[str] | None
    shared_symbol_count: int | None
    union_symbol_count: int | None
    jaccard_overlap: float | None


class PortfolioReviewPairwiseCorrelationResponse(_StrictModel):
    schema_version: Literal[1]
    left_component_id: str
    right_component_id: str
    status: Literal["available", "unavailable"]
    unavailable_reason: Literal["zero_variance"] | None
    zero_variance_series: list[str]
    correlation: float | None
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str


class PortfolioReviewCandidateBaselineCorrelationResponse(_StrictModel):
    schema_version: Literal[1]
    candidate_component_id: str
    candidate_baseline_weight: float
    baseline_scenario_id: str
    baseline_scenario_digest: str
    status: Literal["available", "unavailable"]
    unavailable_reason: Literal["zero_variance"] | None
    zero_variance_series: list[str]
    correlation: float | None
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str


class PortfolioReviewWorstDrawdownResponse(_StrictModel):
    schema_version: Literal[1]
    max_drawdown: float
    peak_date: str
    trough_date: str
    recovery_date: str | None
    recovered: bool
    duration_periods: int
    time_to_trough_periods: int
    time_to_recovery_periods: int | None


class PortfolioReviewComponentContributionResponse(_StrictModel):
    schema_version: Literal[1]
    component_id: str
    strategy_id: str
    weight: float
    total_contribution: float
    mean_contribution: float
    positive_periods: int
    negative_periods: int
    zero_periods: int


class PortfolioReviewScenarioBehaviorResponse(_StrictModel):
    schema_version: Literal[1]
    scenario_id: str
    scenario_digest: str
    observation_count: int
    evaluation_start_timestamp: str
    evaluation_end_timestamp: str
    periods_per_year: float | None
    mean_return: float
    sample_volatility: float
    annualized_volatility: float | None
    min_return: float
    max_return: float
    positive_periods: int
    negative_periods: int
    zero_periods: int
    loss_rate: float
    ending_equity: float
    cumulative_return: float
    worst_drawdown: PortfolioReviewWorstDrawdownResponse
    component_contributions: list[PortfolioReviewComponentContributionResponse]


class PortfolioReviewProposedImpactResponse(_StrictModel):
    schema_version: Literal[1]
    mean_return_delta: float
    sample_volatility_delta: float
    annualized_volatility_delta: float | None
    min_return_delta: float
    max_return_delta: float
    positive_periods_delta: int
    negative_periods_delta: int
    zero_periods_delta: int
    loss_rate_delta: float
    ending_equity_delta: float
    cumulative_return_delta: float
    max_drawdown_delta: float


class PortfolioReviewComponentContributionImpactResponse(_StrictModel):
    schema_version: Literal[1]
    component_id: str
    strategy_id: str
    baseline_weight: float
    proposed_weight: float
    total_contribution_delta: float
    mean_contribution_delta: float
    positive_periods_delta: int
    negative_periods_delta: int
    zero_periods_delta: int


class PortfolioReviewInteractionImpactAnalysisResponse(_StrictModel):
    schema_version: Literal[1]
    source_id: str
    source_digest: str
    component_ids: list[str]
    proposed_component_id: str
    symbol_overlaps: list[PortfolioReviewSymbolOverlapResponse]
    pairwise_correlations: list[PortfolioReviewPairwiseCorrelationResponse]
    candidate_baseline_correlation: (
        PortfolioReviewCandidateBaselineCorrelationResponse
    )
    baseline_behavior: PortfolioReviewScenarioBehaviorResponse
    proposed_behavior: PortfolioReviewScenarioBehaviorResponse
    proposed_impact: PortfolioReviewProposedImpactResponse
    component_contribution_impacts: list[
        PortfolioReviewComponentContributionImpactResponse
    ]


class PortfolioReviewAnalysisResponse(_StrictModel):
    schema_version: Literal[1]
    review_id: str
    analysis_evidence_scope: Literal["historical_scenario_evidence"]
    source_id: str
    source_digest: str
    component_ids: list[str]
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    proposed_component_id: str
    baseline_scenario: PortfolioReviewBaselineScenarioResponse
    proposed_scenario: PortfolioReviewProposedScenarioResponse
    concentration_exposure_analysis: (
        PortfolioReviewConcentrationExposureAnalysisResponse
    )
    interaction_impact_analysis: PortfolioReviewInteractionImpactAnalysisResponse
    assumptions: list[str]
    warnings: list[str]
    missing_evidence: list[str]
    created_by: str
    created_timestamp: str
    analysis_digest: str


class PortfolioReviewDecisionResponse(_StrictModel):
    schema_version: Literal[1]
    decision_id: str
    decision_scope: Literal["portfolio_review_governance_only"]
    review_id: str
    analysis_digest: str
    source_id: str
    source_digest: str
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    outcome: Literal["approved", "rejected", "deferred"]
    rationale: str
    reviewed_by: str
    reviewed_timestamp: str
    notes: list[str]
    warnings: list[str]
    decision_digest: str


class PortfolioReviewRecordResponse(_StrictModel):
    record_schema_version: Literal[1]
    review_id: str
    status: Literal["awaiting_decision", "approved", "rejected", "deferred"]
    source_schema_version: Literal[1]
    source_id: str
    source_digest: str
    baseline_scenario_id: str
    baseline_scenario_digest: str
    proposed_scenario_id: str
    proposed_scenario_digest: str
    proposed_component_id: str
    analysis_schema_version: Literal[1]
    analysis_digest: str
    created_by: str
    created_timestamp: datetime
    decision_schema_version: Literal[1] | None
    decision_id: str | None
    decision_digest: str | None
    outcome: Literal["approved", "rejected", "deferred"] | None
    reviewed_by: str | None
    reviewed_timestamp: datetime | None
    version: Literal[1, 2]
    updated_timestamp: datetime


class PortfolioReviewDetailResponse(_StrictModel):
    record: PortfolioReviewRecordResponse
    source: PortfolioReviewSourceResponse
    analysis: PortfolioReviewAnalysisResponse
    decision: PortfolioReviewDecisionResponse | None


class PortfolioReviewCommandResponse(_StrictModel):
    outcome: Literal["created", "replayed"]
    review: PortfolioReviewDetailResponse
