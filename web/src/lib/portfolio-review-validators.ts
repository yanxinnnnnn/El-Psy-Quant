import type { components } from "@/generated/api-types";

type Schemas = components["schemas"];
type RecordResponse = Schemas["PortfolioReviewRecordResponse"];
type DetailResponse = Schemas["PortfolioReviewDetailResponse"];
type CommandResponse = Schemas["PortfolioReviewCommandResponse"];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function number(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function integer(value: unknown): value is number {
  return Number.isInteger(value);
}

function boolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function nullableString(value: unknown): value is string | null {
  return value === null || string(value);
}

function nullableNumber(value: unknown): value is number | null {
  return value === null || number(value);
}

function nullableInteger(value: unknown): value is number | null {
  return value === null || integer(value);
}

function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(string);
}

function arrayOf(
  value: unknown,
  validator: (item: unknown) => boolean,
): value is unknown[] {
  return Array.isArray(value) && value.every(validator);
}

function one(value: unknown): value is 1 {
  return value === 1;
}

export function isPortfolioReviewStatus(
  value: unknown,
): value is RecordResponse["status"] {
  return (
    value === "awaiting_decision" ||
    value === "approved" ||
    value === "rejected" ||
    value === "deferred"
  );
}

function decisionOutcome(
  value: unknown,
): value is "approved" | "rejected" | "deferred" {
  return value === "approved" || value === "rejected" || value === "deferred";
}

function availability(value: unknown): value is "available" | "unavailable" {
  return value === "available" || value === "unavailable";
}

function evidenceReference(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.reference_type) &&
    string(value.reference_id) &&
    nullableString(value.label) &&
    nullableString(value.description)
  );
}

function component(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.component_id) &&
    string(value.strategy_id) &&
    arrayOf(value.evidence_references, evidenceReference) &&
    (value.symbols === null || strings(value.symbols)) &&
    nullableString(value.label) &&
    nullableString(value.description)
  );
}

function returnObservation(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.timestamp) &&
    arrayOf(value.component_returns, number)
  );
}

function source(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.source_id) &&
    arrayOf(value.components, component) &&
    arrayOf(value.return_observations, returnObservation) &&
    string(value.evaluation_frequency) &&
    nullableNumber(value.periods_per_year) &&
    string(value.created_by) &&
    string(value.created_timestamp) &&
    strings(value.assumptions) &&
    strings(value.warnings) &&
    strings(value.missing_evidence) &&
    string(value.source_digest)
  );
}

function componentWeight(value: unknown): boolean {
  return object(value) && string(value.component_id) && number(value.weight);
}

function baselineScenario(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.scenario_id) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    arrayOf(value.component_weights, componentWeight) &&
    string(value.rationale) &&
    strings(value.assumptions) &&
    strings(value.warnings) &&
    string(value.scenario_digest)
  );
}

function proposedScenario(value: unknown): boolean {
  return (
    baselineScenario(value) &&
    object(value) &&
    string(value.proposed_component_id)
  );
}

function concentration(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.scenario_id) &&
    string(value.scenario_digest) &&
    string(value.largest_component_id) &&
    number(value.largest_component_weight) &&
    number(value.top_3_weight) &&
    number(value.herfindahl_hirschman_index) &&
    number(value.effective_component_count)
  );
}

function universeCoverage(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.scenario_id) &&
    string(value.scenario_digest) &&
    strings(value.components_with_symbol_evidence) &&
    strings(value.components_missing_symbol_evidence) &&
    strings(value.active_component_ids) &&
    strings(value.active_components_with_symbol_evidence) &&
    strings(value.active_components_missing_symbol_evidence) &&
    integer(value.source_component_count) &&
    integer(value.components_with_symbol_evidence_count) &&
    integer(value.components_missing_symbol_evidence_count) &&
    integer(value.active_component_count) &&
    integer(value.active_components_with_symbol_evidence_count) &&
    integer(value.active_components_missing_symbol_evidence_count) &&
    boolean(value.active_coverage_complete)
  );
}

function componentExposure(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.component_id) &&
    string(value.strategy_id) &&
    number(value.baseline_weight) &&
    number(value.proposed_weight) &&
    number(value.weight_delta) &&
    (value.change_type === "added" ||
      value.change_type === "removed" ||
      value.change_type === "increased" ||
      value.change_type === "decreased" ||
      value.change_type === "unchanged") &&
    boolean(value.baseline_active) &&
    boolean(value.proposed_active) &&
    (value.symbols === null || strings(value.symbols)) &&
    (value.symbol_evidence_status === "available" ||
      value.symbol_evidence_status === "missing")
  );
}

function concentrationExposure(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    strings(value.component_ids) &&
    concentration(value.baseline_concentration) &&
    concentration(value.proposed_concentration) &&
    arrayOf(value.component_exposures, componentExposure) &&
    universeCoverage(value.baseline_universe_coverage) &&
    universeCoverage(value.proposed_universe_coverage)
  );
}

function symbolOverlap(value: unknown): boolean {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.left_component_id) ||
    !string(value.right_component_id) ||
    !availability(value.status) ||
    !strings(value.missing_symbol_component_ids)
  ) {
    return false;
  }
  if (value.status === "available") {
    return (
      value.unavailable_reason === null &&
      strings(value.shared_symbols) &&
      integer(value.shared_symbol_count) &&
      integer(value.union_symbol_count) &&
      number(value.jaccard_overlap)
    );
  }
  return (
    value.unavailable_reason === "missing_symbol_evidence" &&
    value.shared_symbols === null &&
    value.shared_symbol_count === null &&
    value.union_symbol_count === null &&
    value.jaccard_overlap === null
  );
}

function pairwiseCorrelation(value: unknown): boolean {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.left_component_id) ||
    !string(value.right_component_id) ||
    !availability(value.status) ||
    !strings(value.zero_variance_series) ||
    !integer(value.observation_count) ||
    !string(value.evaluation_start_timestamp) ||
    !string(value.evaluation_end_timestamp)
  ) {
    return false;
  }
  return value.status === "available"
    ? value.unavailable_reason === null && number(value.correlation)
    : value.unavailable_reason === "zero_variance" && value.correlation === null;
}

function candidateCorrelation(value: unknown): boolean {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.candidate_component_id) ||
    !number(value.candidate_baseline_weight) ||
    !string(value.baseline_scenario_id) ||
    !string(value.baseline_scenario_digest) ||
    !availability(value.status) ||
    !strings(value.zero_variance_series) ||
    !integer(value.observation_count) ||
    !string(value.evaluation_start_timestamp) ||
    !string(value.evaluation_end_timestamp)
  ) {
    return false;
  }
  return value.status === "available"
    ? value.unavailable_reason === null && number(value.correlation)
    : value.unavailable_reason === "zero_variance" && value.correlation === null;
}

function worstDrawdown(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    number(value.max_drawdown) &&
    string(value.peak_date) &&
    string(value.trough_date) &&
    nullableString(value.recovery_date) &&
    boolean(value.recovered) &&
    integer(value.duration_periods) &&
    integer(value.time_to_trough_periods) &&
    nullableInteger(value.time_to_recovery_periods)
  );
}

function contribution(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.component_id) &&
    string(value.strategy_id) &&
    number(value.weight) &&
    number(value.total_contribution) &&
    number(value.mean_contribution) &&
    integer(value.positive_periods) &&
    integer(value.negative_periods) &&
    integer(value.zero_periods)
  );
}

function scenarioBehavior(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.scenario_id) &&
    string(value.scenario_digest) &&
    integer(value.observation_count) &&
    string(value.evaluation_start_timestamp) &&
    string(value.evaluation_end_timestamp) &&
    nullableNumber(value.periods_per_year) &&
    number(value.mean_return) &&
    number(value.sample_volatility) &&
    nullableNumber(value.annualized_volatility) &&
    number(value.min_return) &&
    number(value.max_return) &&
    integer(value.positive_periods) &&
    integer(value.negative_periods) &&
    integer(value.zero_periods) &&
    number(value.loss_rate) &&
    number(value.ending_equity) &&
    number(value.cumulative_return) &&
    worstDrawdown(value.worst_drawdown) &&
    arrayOf(value.component_contributions, contribution)
  );
}

function proposedImpact(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    number(value.mean_return_delta) &&
    number(value.sample_volatility_delta) &&
    nullableNumber(value.annualized_volatility_delta) &&
    number(value.min_return_delta) &&
    number(value.max_return_delta) &&
    integer(value.positive_periods_delta) &&
    integer(value.negative_periods_delta) &&
    integer(value.zero_periods_delta) &&
    number(value.loss_rate_delta) &&
    number(value.ending_equity_delta) &&
    number(value.cumulative_return_delta) &&
    number(value.max_drawdown_delta)
  );
}

function contributionImpact(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.component_id) &&
    string(value.strategy_id) &&
    number(value.baseline_weight) &&
    number(value.proposed_weight) &&
    number(value.total_contribution_delta) &&
    number(value.mean_contribution_delta) &&
    integer(value.positive_periods_delta) &&
    integer(value.negative_periods_delta) &&
    integer(value.zero_periods_delta)
  );
}

function interactionImpact(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    strings(value.component_ids) &&
    string(value.proposed_component_id) &&
    arrayOf(value.symbol_overlaps, symbolOverlap) &&
    arrayOf(value.pairwise_correlations, pairwiseCorrelation) &&
    candidateCorrelation(value.candidate_baseline_correlation) &&
    scenarioBehavior(value.baseline_behavior) &&
    scenarioBehavior(value.proposed_behavior) &&
    proposedImpact(value.proposed_impact) &&
    arrayOf(value.component_contribution_impacts, contributionImpact)
  );
}

function analysis(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.review_id) &&
    value.analysis_evidence_scope === "historical_scenario_evidence" &&
    string(value.source_id) &&
    string(value.source_digest) &&
    strings(value.component_ids) &&
    string(value.baseline_scenario_id) &&
    string(value.baseline_scenario_digest) &&
    string(value.proposed_scenario_id) &&
    string(value.proposed_scenario_digest) &&
    string(value.proposed_component_id) &&
    baselineScenario(value.baseline_scenario) &&
    proposedScenario(value.proposed_scenario) &&
    concentrationExposure(value.concentration_exposure_analysis) &&
    interactionImpact(value.interaction_impact_analysis) &&
    strings(value.assumptions) &&
    strings(value.warnings) &&
    strings(value.missing_evidence) &&
    string(value.created_by) &&
    string(value.created_timestamp) &&
    string(value.analysis_digest)
  );
}

function decision(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.decision_id) &&
    value.decision_scope === "portfolio_review_governance_only" &&
    string(value.review_id) &&
    string(value.analysis_digest) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    string(value.baseline_scenario_id) &&
    string(value.baseline_scenario_digest) &&
    string(value.proposed_scenario_id) &&
    string(value.proposed_scenario_digest) &&
    decisionOutcome(value.outcome) &&
    string(value.rationale) &&
    string(value.reviewed_by) &&
    string(value.reviewed_timestamp) &&
    strings(value.notes) &&
    strings(value.warnings) &&
    string(value.decision_digest)
  );
}

function nullableDecisionOutcome(
  value: unknown,
): value is "approved" | "rejected" | "deferred" | null {
  return value === null || decisionOutcome(value);
}

export function isPortfolioReviewRecord(
  value: unknown,
): value is RecordResponse {
  return (
    object(value) &&
    one(value.record_schema_version) &&
    string(value.review_id) &&
    isPortfolioReviewStatus(value.status) &&
    one(value.source_schema_version) &&
    string(value.source_id) &&
    string(value.source_digest) &&
    string(value.baseline_scenario_id) &&
    string(value.baseline_scenario_digest) &&
    string(value.proposed_scenario_id) &&
    string(value.proposed_scenario_digest) &&
    string(value.proposed_component_id) &&
    one(value.analysis_schema_version) &&
    string(value.analysis_digest) &&
    string(value.created_by) &&
    string(value.created_timestamp) &&
    (value.decision_schema_version === null || one(value.decision_schema_version)) &&
    nullableString(value.decision_id) &&
    nullableString(value.decision_digest) &&
    nullableDecisionOutcome(value.outcome) &&
    nullableString(value.reviewed_by) &&
    nullableString(value.reviewed_timestamp) &&
    (value.version === 1 || value.version === 2) &&
    string(value.updated_timestamp)
  );
}

export function isPortfolioReviewListResponse(
  value: unknown,
): value is RecordResponse[] {
  return arrayOf(value, isPortfolioReviewRecord);
}

export function isPortfolioReviewDetailResponse(
  value: unknown,
): value is DetailResponse {
  return (
    object(value) &&
    isPortfolioReviewRecord(value.record) &&
    source(value.source) &&
    analysis(value.analysis) &&
    (value.decision === null || decision(value.decision))
  );
}

export function isPortfolioReviewCommandResponse(
  value: unknown,
): value is CommandResponse {
  return (
    object(value) &&
    (value.outcome === "created" || value.outcome === "replayed") &&
    isPortfolioReviewDetailResponse(value.review)
  );
}
