import type { paths } from "@/generated/api-types";
import {
  isPortfolioReviewCommandResponse,
  isPortfolioReviewDetailResponse,
  isPortfolioReviewListResponse,
  isPortfolioReviewStatus,
} from "@/lib/portfolio-review-validators";
import {
  acceptedScenarioWeightTotal,
  isTimezoneAwareTimestamp,
  portfolioReviewEvidenceReferenceTypes,
  portfolioReviewResearchReferenceTypes,
  type PortfolioReviewEvidenceReferenceType,
} from "@/lib/portfolio-reviews";
import {
  isPaperAccountCommandResponse,
  isPaperAccountDetailResponse,
  isPaperAccountLedgerResponse,
  isPaperAccountLifecycleStatus,
  isPaperAccountListResponse,
  isPaperAccountReconciliationCommandResponse,
  isPaperAccountSnapshotCommandResponse,
} from "@/lib/paper-account-validators";
import {
  isMarketDataReplayDetailResponse,
  isReplaySessionListResponse,
  isReplayStatus,
  isTradingCalendarDetailResponse,
  isTradingCalendarListResponse,
} from "@/lib/market-time-validators";
import {
  isOrderIntentCommandResponse,
  isOrderIntentListResponse,
  isOrderIntentResponse,
  isPreTradeRiskDecisionCommandResponse,
  isPreTradeRiskDecisionListResponse,
  isPreTradeRiskDecisionResponse,
  isStrategySignalCommandResponse,
  isStrategySignalListResponse,
  isStrategySignalResponse,
} from "@/lib/strategy-order-validators";
import {
  isPaperExecutionAttemptListResponse,
  isPaperExecutionAttemptResponse,
  isPaperExecutionFillListResponse,
  isPaperExecutionFillResponse,
  isPaperExecutionOrderCommandResponse,
  isPaperExecutionOrderListResponse,
  isPaperExecutionOrderViewResponse,
  isPaperExecutionReconciliationResponse,
  isPaperExecutionStepCommandResponse,
} from "@/lib/paper-execution-validators";

const API_BASE_PATH = "/api/backend";
const HEALTH_PATH = "/api/v1/health";
const DEMO_WORKSPACE_PATH = "/api/v1/demo-workspace";
const STRATEGIES_PATH = "/api/v1/strategies";
const STRATEGY_DETAIL_PATH = "/api/v1/strategies/{strategy_name}";
const RESEARCH_RUNS_PATH = "/api/v1/research-runs";
const RESEARCH_RUN_DETAIL_PATH =
  "/api/v1/research-runs/{experiment_slug}/{run_id}";
const EVIDENCE_MANIFESTS_PATH = "/api/v1/evidence-manifests";
const EVIDENCE_MANIFEST_DETAIL_PATH =
  "/api/v1/evidence-manifests/{manifest_type}/{artifact_key}";
const PAPER_JOBS_PATH = "/api/v1/paper-jobs";
const PAPER_JOB_DETAIL_PATH = "/api/v1/paper-jobs/{job_id}";
const PAPER_JOB_ATTEMPTS_PATH = "/api/v1/paper-jobs/{job_id}/attempts";
const PAPER_JOB_RUN_PATH = "/api/v1/paper-jobs/{job_id}/run";
const PAPER_JOB_CANCEL_PATH = "/api/v1/paper-jobs/{job_id}/cancel";
const PAPER_JOB_RETRY_PATH = "/api/v1/paper-jobs/{job_id}/retry";
const PAPER_JOB_RECOVER_PATH = "/api/v1/paper-jobs/{job_id}/recover";
const PAPER_JOB_RESULT_PATH = "/api/v1/paper-jobs/{job_id}/result";
const LIFECYCLE_TRANSITION_PROPOSALS_PATH =
  "/api/v1/lifecycle-transition-proposals";
const LIFECYCLE_TRANSITION_RECORDS_PATH =
  "/api/v1/lifecycle-transition-records";
const TRADING_CALENDARS_PATH = "/api/v1/market-time/calendars";
const TRADING_CALENDAR_DETAIL_PATH =
  "/api/v1/market-time/calendars/{calendar_id}";
const MARKET_DATA_REPLAYS_PATH = "/api/v1/market-time/replays";
const MARKET_DATA_REPLAY_DETAIL_PATH =
  "/api/v1/market-time/replays/{replay_id}";
const PORTFOLIO_REVIEWS_PATH = "/api/v1/portfolio-reviews";
const PORTFOLIO_REVIEW_DETAIL_PATH = "/api/v1/portfolio-reviews/{review_id}";
const PORTFOLIO_REVIEW_DECISION_PATH =
  "/api/v1/portfolio-reviews/{review_id}/decision";
const PAPER_ACCOUNTS_PATH = "/api/v1/paper-accounts";
const PAPER_ACCOUNT_DETAIL_PATH = "/api/v1/paper-accounts/{account_id}";
const PAPER_ACCOUNT_LEDGER_PATH =
  "/api/v1/paper-accounts/{account_id}/ledger";
const PAPER_ACCOUNT_CASH_MOVEMENTS_PATH =
  "/api/v1/paper-accounts/{account_id}/cash-movements";
const PAPER_ACCOUNT_POSITION_ADJUSTMENTS_PATH =
  "/api/v1/paper-accounts/{account_id}/position-adjustments";
const PAPER_ACCOUNT_EVIDENCE_LINKS_PATH =
  "/api/v1/paper-accounts/{account_id}/evidence-links";
const PAPER_ACCOUNT_LIFECYCLE_PATH =
  "/api/v1/paper-accounts/{account_id}/lifecycle";
const PAPER_ACCOUNT_SNAPSHOTS_PATH =
  "/api/v1/paper-accounts/{account_id}/snapshots";
const PAPER_ACCOUNT_RECONCILIATIONS_PATH =
  "/api/v1/paper-accounts/{account_id}/reconciliations";
const STRATEGY_SIGNALS_PATH = "/api/v1/strategy-signals";
const STRATEGY_SIGNAL_EVALUATE_PATH = "/api/v1/strategy-signals/evaluate";
const STRATEGY_SIGNAL_DETAIL_PATH = "/api/v1/strategy-signals/{signal_id}";
const ORDER_INTENTS_PATH = "/api/v1/order-intents";
const ORDER_INTENT_DETAIL_PATH = "/api/v1/order-intents/{intent_id}";
const PRE_TRADE_RISK_DECISIONS_PATH = "/api/v1/pre-trade-risk-decisions";
const PRE_TRADE_RISK_DECISION_DETAIL_PATH =
  "/api/v1/pre-trade-risk-decisions/{decision_id}";
const PAPER_EXECUTION_ORDERS_PATH = "/api/v1/paper-execution/orders";
const PAPER_EXECUTION_ORDER_DETAIL_PATH =
  "/api/v1/paper-execution/orders/{execution_order_id}";
const PAPER_EXECUTION_ORDER_STEPS_PATH =
  "/api/v1/paper-execution/orders/{execution_order_id}/steps";
const PAPER_EXECUTION_ORDER_ATTEMPTS_PATH =
  "/api/v1/paper-execution/orders/{execution_order_id}/attempts";
const PAPER_EXECUTION_ATTEMPT_DETAIL_PATH =
  "/api/v1/paper-execution/attempts/{attempt_id}";
const PAPER_EXECUTION_FILLS_PATH = "/api/v1/paper-execution/fills";
const PAPER_EXECUTION_FILL_DETAIL_PATH =
  "/api/v1/paper-execution/fills/{fill_id}";
const PAPER_EXECUTION_RECONCILIATION_PATH =
  "/api/v1/paper-execution/orders/{execution_order_id}/reconciliation";
const REQUEST_ID_HEADER = "X-Request-ID";
const MAX_CODE_LENGTH = 80;
const MAX_MESSAGE_LENGTH = 240;
const MAX_REQUEST_ID_LENGTH = 128;

type SuccessResponse<Path extends keyof paths> =
  paths[Path]["get"] extends {
    responses: { 200: { content: { "application/json": infer Response } } };
  }
    ? Response
    : never;

type PostSuccessResponse<Path extends keyof paths, Status extends number> =
  paths[Path]["post"] extends {
    responses: Record<Status, { content: { "application/json": infer Response } }>;
  }
    ? Response
    : never;

type PostRequestBody<Path extends keyof paths> = paths[Path]["post"] extends {
  requestBody: { content: { "application/json": infer Request } };
}
  ? Request
  : never;

type GetQueryParameters<Path extends keyof paths> = paths[Path]["get"] extends {
  parameters: { query?: infer Query };
}
  ? NonNullable<Query>
  : never;

export type HealthResponse = SuccessResponse<typeof HEALTH_PATH>;
export type DemoWorkspaceDescriptorResponse = SuccessResponse<
  typeof DEMO_WORKSPACE_PATH
>;
export type StrategyListResponse = SuccessResponse<typeof STRATEGIES_PATH>;
export type StrategyDetailResponse = SuccessResponse<typeof STRATEGY_DETAIL_PATH>;
export type ResearchRunListResponse = SuccessResponse<typeof RESEARCH_RUNS_PATH>;
export type ResearchRunDetailResponse = SuccessResponse<
  typeof RESEARCH_RUN_DETAIL_PATH
>;
export type EvidenceManifestListResponse = SuccessResponse<
  typeof EVIDENCE_MANIFESTS_PATH
>;
export type EvidenceManifestDetailResponse = SuccessResponse<
  typeof EVIDENCE_MANIFEST_DETAIL_PATH
>;
export type PaperJobListResponse = SuccessResponse<typeof PAPER_JOBS_PATH>;
export type PaperJobResponse = SuccessResponse<typeof PAPER_JOB_DETAIL_PATH>;
export type PaperJobStatus = PaperJobResponse["status"];
export type PaperJobAttemptListResponse = SuccessResponse<
  typeof PAPER_JOB_ATTEMPTS_PATH
>;
export type PaperJobResultResponse = SuccessResponse<typeof PAPER_JOB_RESULT_PATH>;
export type PaperJobSubmissionRequest = PostRequestBody<typeof PAPER_JOBS_PATH>;
export type PaperJobRecoveryRequest = PostRequestBody<typeof PAPER_JOB_RECOVER_PATH>;
export type PaperJobSubmissionResponse = PostSuccessResponse<
  typeof PAPER_JOBS_PATH,
  200
>;
export type PaperJobRunAcceptedResponse = PostSuccessResponse<
  typeof PAPER_JOB_RUN_PATH,
  202
>;
export type PaperJobCancelResponse = PostSuccessResponse<
  typeof PAPER_JOB_CANCEL_PATH,
  200
>;
export type PaperJobRetryResponse = PostSuccessResponse<
  typeof PAPER_JOB_RETRY_PATH,
  200
>;
export type PaperJobRecoverResponse = PostSuccessResponse<
  typeof PAPER_JOB_RECOVER_PATH,
  200
>;
export type LifecycleTransitionProposalRequest = PostRequestBody<
  typeof LIFECYCLE_TRANSITION_PROPOSALS_PATH
>;
export type LifecycleTransitionProposalResponse = PostSuccessResponse<
  typeof LIFECYCLE_TRANSITION_PROPOSALS_PATH,
  200
>;
export type LifecycleTransitionReviewRequest = PostRequestBody<
  typeof LIFECYCLE_TRANSITION_RECORDS_PATH
>;
export type LifecycleTransitionReviewResponse = PostSuccessResponse<
  typeof LIFECYCLE_TRANSITION_RECORDS_PATH,
  200
>;
export type TradingCalendarListResponse = SuccessResponse<
  typeof TRADING_CALENDARS_PATH
>;
export type TradingCalendarDetailResponse = SuccessResponse<
  typeof TRADING_CALENDAR_DETAIL_PATH
>;
export type ReplaySessionListResponse = SuccessResponse<
  typeof MARKET_DATA_REPLAYS_PATH
>;
export type ReplayStatus = ReplaySessionListResponse[number]["status"];
export type MarketDataReplayDetailResponse = SuccessResponse<
  typeof MARKET_DATA_REPLAY_DETAIL_PATH
>;
export type PortfolioReviewListResponse = SuccessResponse<
  typeof PORTFOLIO_REVIEWS_PATH
>;
export type PortfolioReviewStatus = PortfolioReviewListResponse[number]["status"];
export type PortfolioReviewDetailResponse = SuccessResponse<
  typeof PORTFOLIO_REVIEW_DETAIL_PATH
>;
export type PortfolioReviewCreateRequest = PostRequestBody<
  typeof PORTFOLIO_REVIEWS_PATH
>;
export type PortfolioReviewDecisionRequest = PostRequestBody<
  typeof PORTFOLIO_REVIEW_DECISION_PATH
>;
export type PortfolioReviewCommandResponse = PostSuccessResponse<
  typeof PORTFOLIO_REVIEWS_PATH,
  201
>;
export type PaperAccountListResponse = SuccessResponse<
  typeof PAPER_ACCOUNTS_PATH
>;
export type PaperAccountSummary = PaperAccountListResponse["items"][number];
export type PaperAccountLifecycleStatus =
  PaperAccountSummary["lifecycle_status"];
export type PaperAccountDetailResponse = SuccessResponse<
  typeof PAPER_ACCOUNT_DETAIL_PATH
>;
export type PaperAccountLedgerResponse = SuccessResponse<
  typeof PAPER_ACCOUNT_LEDGER_PATH
>;
export type PaperAccountCreateRequest = PostRequestBody<
  typeof PAPER_ACCOUNTS_PATH
>;
export type PaperAccountCashMovementRequest = PostRequestBody<
  typeof PAPER_ACCOUNT_CASH_MOVEMENTS_PATH
>;
export type PaperAccountPositionAdjustmentRequest = PostRequestBody<
  typeof PAPER_ACCOUNT_POSITION_ADJUSTMENTS_PATH
>;
export type PaperAccountEvidenceLinkRequest = PostRequestBody<
  typeof PAPER_ACCOUNT_EVIDENCE_LINKS_PATH
>;
export type PaperAccountLifecycleRequest = PostRequestBody<
  typeof PAPER_ACCOUNT_LIFECYCLE_PATH
>;
export type PaperAccountEvidenceOperationRequest = PostRequestBody<
  typeof PAPER_ACCOUNT_SNAPSHOTS_PATH
>;
export type PaperAccountCommandResponse = PostSuccessResponse<
  typeof PAPER_ACCOUNTS_PATH,
  201
>;
export type PaperAccountSnapshotCommandResponse = PostSuccessResponse<
  typeof PAPER_ACCOUNT_SNAPSHOTS_PATH,
  201
>;
export type PaperAccountReconciliationCommandResponse = PostSuccessResponse<
  typeof PAPER_ACCOUNT_RECONCILIATIONS_PATH,
  201
>;
export type StrategySignalListResponse = SuccessResponse<
  typeof STRATEGY_SIGNALS_PATH
>;
export type StrategySignalResponse = SuccessResponse<
  typeof STRATEGY_SIGNAL_DETAIL_PATH
>;
export type StrategySignalEvaluateRequest = PostRequestBody<
  typeof STRATEGY_SIGNAL_EVALUATE_PATH
>;
export type StrategySignalCommandResponse = PostSuccessResponse<
  typeof STRATEGY_SIGNAL_EVALUATE_PATH,
  200
>;
export type StrategySignalListFilters = GetQueryParameters<
  typeof STRATEGY_SIGNALS_PATH
>;
export type OrderIntentListResponse = SuccessResponse<typeof ORDER_INTENTS_PATH>;
export type OrderIntentResponse = SuccessResponse<typeof ORDER_INTENT_DETAIL_PATH>;
export type OrderIntentCreateRequest = PostRequestBody<typeof ORDER_INTENTS_PATH>;
export type OrderIntentCommandResponse = PostSuccessResponse<
  typeof ORDER_INTENTS_PATH,
  200
>;
export type OrderIntentListFilters = GetQueryParameters<typeof ORDER_INTENTS_PATH>;
export type PreTradeRiskDecisionListResponse = SuccessResponse<
  typeof PRE_TRADE_RISK_DECISIONS_PATH
>;
export type PreTradeRiskDecisionResponse = SuccessResponse<
  typeof PRE_TRADE_RISK_DECISION_DETAIL_PATH
>;
export type PreTradeRiskDecisionCreateRequest = PostRequestBody<
  typeof PRE_TRADE_RISK_DECISIONS_PATH
>;
export type PreTradeRiskDecisionCommandResponse = PostSuccessResponse<
  typeof PRE_TRADE_RISK_DECISIONS_PATH,
  200
>;
export type PreTradeRiskDecisionListFilters = GetQueryParameters<
  typeof PRE_TRADE_RISK_DECISIONS_PATH
>;
export type PaperExecutionOrderListResponse = SuccessResponse<
  typeof PAPER_EXECUTION_ORDERS_PATH
>;
export type PaperExecutionOrderViewResponse = SuccessResponse<
  typeof PAPER_EXECUTION_ORDER_DETAIL_PATH
>;
export type PaperExecutionAttemptListResponse = SuccessResponse<
  typeof PAPER_EXECUTION_ORDER_ATTEMPTS_PATH
>;
export type PaperExecutionAttemptResponse = SuccessResponse<
  typeof PAPER_EXECUTION_ATTEMPT_DETAIL_PATH
>;
export type PaperExecutionFillListResponse = SuccessResponse<
  typeof PAPER_EXECUTION_FILLS_PATH
>;
export type PaperExecutionFillResponse = SuccessResponse<
  typeof PAPER_EXECUTION_FILL_DETAIL_PATH
>;
export type PaperExecutionReconciliationResponse = SuccessResponse<
  typeof PAPER_EXECUTION_RECONCILIATION_PATH
>;
export type PaperExecutionOrderCreateRequest = PostRequestBody<
  typeof PAPER_EXECUTION_ORDERS_PATH
>;
export type PaperExecutionOrderStepRequest = PostRequestBody<
  typeof PAPER_EXECUTION_ORDER_STEPS_PATH
>;
export type PaperExecutionOrderCommandResponse = PostSuccessResponse<
  typeof PAPER_EXECUTION_ORDERS_PATH,
  200
>;
export type PaperExecutionStepCommandResponse = PostSuccessResponse<
  typeof PAPER_EXECUTION_ORDER_STEPS_PATH,
  200
>;
export type PaperExecutionOrderListFilters = GetQueryParameters<
  typeof PAPER_EXECUTION_ORDERS_PATH
>;
export type PaperExecutionAttemptListFilters = GetQueryParameters<
  typeof PAPER_EXECUTION_ORDER_ATTEMPTS_PATH
>;
export type PaperExecutionFillListFilters = GetQueryParameters<
  typeof PAPER_EXECUTION_FILLS_PATH
>;

export type ApiResult<Response> = {
  data: Response;
  requestId: string | null;
};

type PublicErrorEnvelope = {
  error: {
    code: string;
    message: string;
  };
  request_id: string;
};

type RuntimeValidator<Response> = (value: unknown) => value is Response;

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly publicMessage: string;
  readonly requestId: string | null;

  constructor({
    status,
    code,
    publicMessage,
    requestId,
  }: {
    status: number;
    code: string;
    publicMessage: string;
    requestId: string | null;
  }) {
    super(publicMessage);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.publicMessage = publicMessage;
    this.requestId = requestId;
  }
}

function boundedString(value: unknown, maximumLength: number): string | null {
  return typeof value === "string" && value.length > 0 && value.length <= maximumLength
    ? value
    : null;
}

function requestIdFrom(response: Response, bodyRequestId?: unknown): string | null {
  return (
    boundedString(response.headers.get(REQUEST_ID_HEADER), MAX_REQUEST_ID_LENGTH) ??
    boundedString(bodyRequestId, MAX_REQUEST_ID_LENGTH)
  );
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || isNumber(value);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || isString(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isNumericRecord(value: unknown): boolean {
  return (
    isObject(value) && Object.values(value).every((item) => isNumber(item))
  );
}

function isPaperCommandAccount(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.timestamp) &&
    isNumber(value.starting_cash) &&
    isNumber(value.current_cash) &&
    isNumericRecord(value.positions)
  );
}

function isPaperCommandRequest(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.run_id) &&
    isString(value.created_timestamp) &&
    isPaperCommandAccount(value.starting_account_state) &&
    isPaperCommandAccount(value.ending_account_state) &&
    Array.isArray(value.orders) &&
    value.orders.every(
      (order) =>
        isObject(order) &&
        isString(order.order_id) &&
        isString(order.timestamp) &&
        isString(order.symbol) &&
        isString(order.side) &&
        isNumber(order.quantity) &&
        isString(order.status),
    ) &&
    Array.isArray(value.fills) &&
    value.fills.every(
      (fill) =>
        isObject(fill) &&
        isString(fill.timestamp) &&
        isString(fill.symbol) &&
        isString(fill.side) &&
        isNumber(fill.quantity) &&
        isNumber(fill.price) &&
        isNullableString(fill.order_id),
    )
  );
}

function isLifecycleSnapshotRequest(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.snapshot_id) &&
    isString(value.strategy_id) &&
    isString(value.lifecycle_state) &&
    isString(value.rationale) &&
    isNullableString(value.declared_by) &&
    isNullableString(value.declared_timestamp) &&
    isStringArray(value.notes) &&
    isStringArray(value.warnings)
  );
}

function isLifecycleEvidenceRequest(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.reference_type) &&
    isString(value.reference_id) &&
    isNullableString(value.label) &&
    isNullableString(value.description)
  );
}

function isLifecycleProposalRequest(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.proposal_id) &&
    isLifecycleSnapshotRequest(value.source_snapshot) &&
    isString(value.target_state) &&
    isString(value.rationale) &&
    Array.isArray(value.evidence_references) &&
    value.evidence_references.every(isLifecycleEvidenceRequest) &&
    isNullableString(value.requested_by) &&
    isNullableString(value.requested_timestamp) &&
    isStringArray(value.notes) &&
    isStringArray(value.warnings)
  );
}

function isLifecycleReviewRequest(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.transition_record_id) &&
    isLifecycleProposalRequest(value.proposal) &&
    isString(value.review_outcome) &&
    isString(value.rationale) &&
    (value.resulting_snapshot === null ||
      isLifecycleSnapshotRequest(value.resulting_snapshot)) &&
    isNullableString(value.reviewed_by) &&
    isNullableString(value.reviewed_timestamp) &&
    isStringArray(value.notes) &&
    isStringArray(value.warnings)
  );
}

function hasOnlyKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  return Object.keys(value).length === keys.length &&
    keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

function isNormalizedNonblankString(value: unknown): value is string {
  return isString(value) && value.length > 0 && value === value.trim();
}

function isNormalizedStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isNormalizedNonblankString);
}

function isNullableNormalizedString(value: unknown): value is string | null {
  return value === null || isNormalizedNonblankString(value);
}

function isPortfolioReviewEvidenceRequest(value: unknown): boolean {
  if (!isObject(value) ||
    !hasOnlyKeys(value, ["reference_type", "reference_id", "label", "description"]) ||
    !isNormalizedNonblankString(value.reference_type) ||
    !portfolioReviewEvidenceReferenceTypes.includes(
      value.reference_type as PortfolioReviewEvidenceReferenceType,
    ) ||
    !isNormalizedNonblankString(value.reference_id) ||
    !isNullableNormalizedString(value.label) ||
    !isNullableNormalizedString(value.description)
  ) return false;
  return true;
}

function isPortfolioReviewComponentRequest(value: unknown): boolean {
  if (!isObject(value) ||
    !hasOnlyKeys(value, [
      "component_id",
      "strategy_id",
      "evidence_references",
      "symbols",
      "label",
      "description",
    ]) ||
    !isNormalizedNonblankString(value.component_id) ||
    !isNormalizedNonblankString(value.strategy_id) ||
    !Array.isArray(value.evidence_references) ||
    value.evidence_references.length === 0 ||
    !value.evidence_references.every(isPortfolioReviewEvidenceRequest) ||
    (value.symbols !== null && !isStringArray(value.symbols)) ||
    !isNullableNormalizedString(value.label) ||
    !isNullableNormalizedString(value.description)
  ) return false;

  const identities = new Set<string>();
  let hasResearchOrigin = false;
  for (const reference of value.evidence_references) {
    if (!isObject(reference) ||
      !isString(reference.reference_type) ||
      !isString(reference.reference_id)
    ) return false;
    const identity = `${reference.reference_type}\u0000${reference.reference_id}`;
    if (identities.has(identity)) return false;
    identities.add(identity);
    if (portfolioReviewResearchReferenceTypes.has(
      reference.reference_type as PortfolioReviewEvidenceReferenceType,
    )) hasResearchOrigin = true;
  }
  return hasResearchOrigin;
}

function isPortfolioReviewScenarioRequest(
  value: unknown,
  proposed: boolean,
  componentIds: readonly string[],
): boolean {
  const keys = ["scenario_id", "weights", "rationale", "assumptions", "warnings"];
  if (proposed) keys.push("proposed_component_id");
  if (!isObject(value) ||
    !hasOnlyKeys(value, keys) ||
    !isNormalizedNonblankString(value.scenario_id) ||
    !isObject(value.weights) ||
    Object.keys(value.weights).length !== componentIds.length ||
    !componentIds.every((componentId) =>
      Object.prototype.hasOwnProperty.call(value.weights, componentId)
    ) ||
    !isNormalizedNonblankString(value.rationale) ||
    !isNormalizedStringArray(value.assumptions) ||
    !isNormalizedStringArray(value.warnings) ||
    (proposed && !isNormalizedNonblankString(value.proposed_component_id))
  ) return false;
  const weights = Object.values(value.weights);
  if (!weights.every(isNumber)) return false;
  return weights.every((weight) => weight >= 0) &&
    weights.some((weight) => weight > 0) &&
    acceptedScenarioWeightTotal(weights.reduce((total, weight) => total + weight, 0));
}

export function isPortfolioReviewCreateRequest(
  value: unknown,
): value is PortfolioReviewCreateRequest {
  if (!isObject(value) || !hasOnlyKeys(value, [
    "review_id",
    "source",
    "baseline_scenario",
    "proposed_scenario",
    "analysis",
  ])) return false;
  const source = value.source;
  const analysis = value.analysis;
  if (!isNormalizedNonblankString(value.review_id) ||
    !isObject(source) ||
    !hasOnlyKeys(source, [
      "source_id",
      "components",
      "return_observations",
      "evaluation_frequency",
      "periods_per_year",
      "created_by",
      "created_timestamp",
      "assumptions",
      "warnings",
      "missing_evidence",
    ]) ||
    !isNormalizedNonblankString(source.source_id) ||
    !Array.isArray(source.components) ||
    source.components.length < 2 ||
    source.components.length > 12 ||
    !source.components.every(isPortfolioReviewComponentRequest) ||
    !Array.isArray(source.return_observations) ||
    source.return_observations.length < 3 ||
    !isNormalizedNonblankString(source.evaluation_frequency) ||
    (source.periods_per_year !== null &&
      (!isNumber(source.periods_per_year) || source.periods_per_year <= 0)) ||
    !isNormalizedNonblankString(source.created_by) ||
    !isString(source.created_timestamp) ||
    !isTimezoneAwareTimestamp(source.created_timestamp) ||
    !isNormalizedStringArray(source.assumptions) ||
    !isNormalizedStringArray(source.warnings) ||
    !isNormalizedStringArray(source.missing_evidence) ||
    !isObject(analysis) ||
    !hasOnlyKeys(analysis, [
      "created_by",
      "created_timestamp",
      "assumptions",
      "warnings",
      "missing_evidence",
    ]) ||
    !isNormalizedNonblankString(analysis.created_by) ||
    !isString(analysis.created_timestamp) ||
    !isTimezoneAwareTimestamp(analysis.created_timestamp) ||
    !isNormalizedStringArray(analysis.assumptions) ||
    !isNormalizedStringArray(analysis.warnings) ||
    !isNormalizedStringArray(analysis.missing_evidence)
  ) return false;

  const componentIds = source.components.map((component) =>
    (component as Record<string, unknown>).component_id as string
  );
  if (new Set(componentIds).size !== componentIds.length ||
    !isPortfolioReviewScenarioRequest(value.baseline_scenario, false, componentIds) ||
    !isPortfolioReviewScenarioRequest(value.proposed_scenario, true, componentIds)
  ) return false;

  let previousTimestamp = Number.NEGATIVE_INFINITY;
  for (const observation of source.return_observations) {
    if (!isObject(observation) ||
      !hasOnlyKeys(observation, ["timestamp", "component_returns"]) ||
      !isString(observation.timestamp) ||
      !isTimezoneAwareTimestamp(observation.timestamp) ||
      !Array.isArray(observation.component_returns) ||
      observation.component_returns.length !== componentIds.length ||
      !observation.component_returns.every(isNumber)
    ) return false;
    const timestamp = Date.parse(observation.timestamp);
    if (timestamp <= previousTimestamp) return false;
    previousTimestamp = timestamp;
  }

  const baseline = value.baseline_scenario as Record<string, unknown>;
  const proposed = value.proposed_scenario as Record<string, unknown>;
  if (baseline.scenario_id === proposed.scenario_id) return false;
  const baselineWeights = baseline.weights as Record<string, number>;
  const proposedWeights = proposed.weights as Record<string, number>;
  const proposedComponentId = proposed.proposed_component_id as string;
  return componentIds.includes(proposedComponentId) &&
    componentIds.some((componentId) =>
      baselineWeights[componentId] !== proposedWeights[componentId]
    ) &&
    baselineWeights[proposedComponentId] !== proposedWeights[proposedComponentId];
}

function isDemoWorkspaceDescriptor(
  value: unknown,
): value is DemoWorkspaceDescriptorResponse {
  if (!isObject(value) || !hasOnlyKeys(value, [
    "schema_version",
    "dataset_id",
    "dataset_version",
    "display_name",
    "warning",
    "canonical_strategy_name",
    "research_run",
    "evidence_manifests",
    "paper_jobs",
    "comparison_candidate_job_ids",
    "lifecycle_proposal_example",
    "lifecycle_review_example",
    "paper_job_submission_example",
    "portfolio_review_example",
    "paper_account",
    "market_time",
    "strategy_order",
    "paper_execution",
  ])) {
    return false;
  }
  const jobIds = Array.isArray(value.paper_jobs)
    ? value.paper_jobs
        .filter(isObject)
        .map((job) => job.job_id)
        .filter(isString)
    : [];
  return (
    value.schema_version === 6 &&
    isString(value.dataset_id) &&
    value.dataset_version === 6 &&
    isString(value.display_name) &&
    isString(value.warning) &&
    isString(value.canonical_strategy_name) &&
    isObject(value.research_run) &&
    isString(value.research_run.experiment_slug) &&
    isString(value.research_run.run_id) &&
    Array.isArray(value.evidence_manifests) &&
    value.evidence_manifests.every(
      (reference) =>
        isObject(reference) &&
        isEvidenceManifestType(reference.manifest_type) &&
        isString(reference.artifact_key),
    ) &&
    Array.isArray(value.paper_jobs) &&
    value.paper_jobs.every(
      (job) =>
        isObject(job) && isString(job.job_id) && isString(job.run_id),
    ) &&
    Array.isArray(value.comparison_candidate_job_ids) &&
    value.comparison_candidate_job_ids.length >= 2 &&
    value.comparison_candidate_job_ids.every(
      (jobId) => isString(jobId) && jobIds.includes(jobId),
    ) &&
    new Set(value.comparison_candidate_job_ids).size ===
      value.comparison_candidate_job_ids.length &&
    isLifecycleProposalRequest(value.lifecycle_proposal_example) &&
    isLifecycleReviewRequest(value.lifecycle_review_example) &&
    isObject(value.paper_job_submission_example) &&
    isString(value.paper_job_submission_example.idempotency_key) &&
    isPaperCommandRequest(value.paper_job_submission_example.request) &&
    isObject(value.portfolio_review_example) &&
    hasOnlyKeys(value.portfolio_review_example, ["create_idempotency_key", "request"]) &&
    isNormalizedNonblankString(
      value.portfolio_review_example.create_idempotency_key,
    ) &&
    isPortfolioReviewCreateRequest(value.portfolio_review_example.request) &&
    isObject(value.paper_account) &&
    hasOnlyKeys(value.paper_account, [
      "account_id",
      "head_version",
      "event_types",
      "snapshot_id",
      "reconciliation_id",
    ]) &&
    isNormalizedNonblankString(value.paper_account.account_id) &&
    value.paper_account.head_version === 5 &&
    Array.isArray(value.paper_account.event_types) &&
    value.paper_account.event_types.join(",") === [
      "account_created",
      "cash_movement_posted",
      "position_adjustment_posted",
      "account_frozen",
      "account_reactivated",
    ].join(",") &&
    isNormalizedNonblankString(value.paper_account.snapshot_id) &&
    isNormalizedNonblankString(value.paper_account.reconciliation_id) &&
    isObject(value.market_time) &&
    hasOnlyKeys(value.market_time, [
      "calendar_id",
      "session_ids",
      "replay_id",
      "event_count",
      "event_stream_digest",
      "checkpoint",
      "recovery",
    ]) &&
    isNormalizedNonblankString(value.market_time.calendar_id) &&
    Array.isArray(value.market_time.session_ids) &&
    value.market_time.session_ids.length >= 2 &&
    value.market_time.session_ids.every(isNormalizedNonblankString) &&
    new Set(value.market_time.session_ids).size ===
      value.market_time.session_ids.length &&
    isNormalizedNonblankString(value.market_time.replay_id) &&
    Number.isInteger(value.market_time.event_count) &&
    (value.market_time.event_count as number) >= 3 &&
    typeof value.market_time.event_stream_digest === "string" &&
    /^[0-9a-f]{64}$/.test(value.market_time.event_stream_digest) &&
    isObject(value.market_time.checkpoint) &&
    hasOnlyKeys(value.market_time.checkpoint, [
      "status",
      "position",
      "last_event_id",
      "current_time",
    ]) &&
    value.market_time.checkpoint.status === "paused" &&
    Number.isInteger(value.market_time.checkpoint.position) &&
    (value.market_time.checkpoint.position as number) >= 1 &&
    (value.market_time.checkpoint.position as number) <
      (value.market_time.event_count as number) &&
    isNormalizedNonblankString(value.market_time.checkpoint.last_event_id) &&
    isNormalizedNonblankString(value.market_time.checkpoint.current_time) &&
    isObject(value.market_time.recovery) &&
    hasOnlyKeys(value.market_time.recovery, [
      "remaining_event_ids",
      "final_status",
      "final_position",
      "last_event_id",
      "current_time",
    ]) &&
    Array.isArray(value.market_time.recovery.remaining_event_ids) &&
    value.market_time.recovery.remaining_event_ids.every(
      isNormalizedNonblankString,
    ) &&
    value.market_time.recovery.remaining_event_ids.length ===
      (value.market_time.event_count as number) -
        (value.market_time.checkpoint.position as number) &&
    value.market_time.recovery.final_status === "completed" &&
    value.market_time.recovery.final_position ===
      value.market_time.event_count &&
    isNormalizedNonblankString(value.market_time.recovery.last_event_id) &&
    value.market_time.recovery.last_event_id ===
      value.market_time.recovery.remaining_event_ids.at(-1) &&
    isNormalizedNonblankString(value.market_time.recovery.current_time) &&
    isObject(value.strategy_order) &&
    hasOnlyKeys(value.strategy_order, [
      "workspace_path",
      "account_id",
      "trading_session_id",
      "instrument_id",
      "runtime",
      "signal",
      "intent",
      "allow_decision",
      "reject_decision",
    ]) &&
    value.strategy_order.workspace_path === "/strategy-to-risk" &&
    isNormalizedNonblankString(value.strategy_order.account_id) &&
    isNormalizedNonblankString(value.strategy_order.trading_session_id) &&
    isNormalizedNonblankString(value.strategy_order.instrument_id) &&
    isObject(value.strategy_order.runtime) &&
    hasOnlyKeys(value.strategy_order.runtime, [
      "fast_window", "slow_window", "target_position_quantity",
    ]) &&
    Number.isInteger(value.strategy_order.runtime.fast_window) &&
    Number.isInteger(value.strategy_order.runtime.slow_window) &&
    isNormalizedNonblankString(
      value.strategy_order.runtime.target_position_quantity,
    ) &&
    [
      [value.strategy_order.signal, "evaluate_strategy_signal"],
      [value.strategy_order.intent, "derive_order_intent"],
    ].every(([authority, namespace]) =>
      isObject(authority) &&
        hasOnlyKeys(authority, ["id", "digest", "receipt"]) &&
        isNormalizedNonblankString(authority.id) &&
        typeof authority.digest === "string" &&
        /^[0-9a-f]{64}$/.test(authority.digest) &&
        isObject(authority.receipt) &&
        hasOnlyKeys(authority.receipt, ["namespace", "idempotency_key"]) &&
        authority.receipt.namespace === namespace &&
        isNormalizedNonblankString(authority.receipt.idempotency_key),
    ) &&
    [
      [value.strategy_order.allow_decision, "allow", []],
      [value.strategy_order.reject_decision, "reject", [
        "maximum_order_quantity_exceeded",
      ]],
    ].every(([authority, outcome, reasonCodes]) =>
      isObject(authority) &&
      hasOnlyKeys(authority, [
        "id", "digest", "outcome", "reason_codes", "receipt",
      ]) &&
      isNormalizedNonblankString(authority.id) &&
      typeof authority.digest === "string" &&
      /^[0-9a-f]{64}$/.test(authority.digest) &&
      isObject(authority.receipt) &&
      hasOnlyKeys(authority.receipt, ["namespace", "idempotency_key"]) &&
      authority.receipt.namespace === "evaluate_pre_trade_risk" &&
      isNormalizedNonblankString(authority.receipt.idempotency_key) &&
      authority.outcome === outcome &&
      JSON.stringify(authority.reason_codes) === JSON.stringify(reasonCodes)
    ) &&
    isObject(value.paper_execution) &&
    hasOnlyKeys(value.paper_execution, [
      "workspace_path",
      "manual_candidate",
      "policy_draft",
      "completed_order",
      "risk_rejection_order",
      "exhaustion_order",
    ]) &&
    value.paper_execution.workspace_path === "/paper-execution" &&
    isObject(value.paper_execution.manual_candidate) &&
    hasOnlyKeys(value.paper_execution.manual_candidate, [
      "intent_id", "intent_digest", "decision_id", "decision_digest",
    ]) &&
    isNormalizedNonblankString(value.paper_execution.manual_candidate.intent_id) &&
    typeof value.paper_execution.manual_candidate.intent_digest === "string" &&
    /^[0-9a-f]{64}$/.test(value.paper_execution.manual_candidate.intent_digest) &&
    isNormalizedNonblankString(value.paper_execution.manual_candidate.decision_id) &&
    typeof value.paper_execution.manual_candidate.decision_digest === "string" &&
    /^[0-9a-f]{64}$/.test(value.paper_execution.manual_candidate.decision_digest) &&
    isObject(value.paper_execution.policy_draft) &&
    hasOnlyKeys(value.paper_execution.policy_draft, [
      "max_fill_quantity_per_trade_event",
      "slippage_bps",
      "commission_bps",
      "fee_bps",
      "buy_tax_bps",
      "sell_tax_bps",
    ]) &&
    (value.paper_execution.policy_draft.max_fill_quantity_per_trade_event === null ||
      isNormalizedNonblankString(value.paper_execution.policy_draft.max_fill_quantity_per_trade_event)) &&
    [
      value.paper_execution.policy_draft.slippage_bps,
      value.paper_execution.policy_draft.commission_bps,
      value.paper_execution.policy_draft.fee_bps,
      value.paper_execution.policy_draft.buy_tax_bps,
      value.paper_execution.policy_draft.sell_tax_bps,
    ].every(isNormalizedNonblankString) &&
    [
      value.paper_execution.completed_order,
      value.paper_execution.risk_rejection_order,
      value.paper_execution.exhaustion_order,
    ].every((reference) =>
      isObject(reference) &&
      hasOnlyKeys(reference, ["id", "digest"]) &&
      isNormalizedNonblankString(reference.id) &&
      typeof reference.digest === "string" &&
      /^[0-9a-f]{64}$/.test(reference.digest) &&
      reference.id.endsWith(reference.digest)
    )
  );
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (!isObject(value)) {
    return false;
  }
  return (
    value.status === "ok" &&
    value.service === "el-psy-quant" &&
    value.api_version === "v1"
  );
}

function isStrategySummary(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.name) &&
    isString(value.display_name) &&
    isString(value.description)
  );
}

function isStrategyListResponse(value: unknown): value is StrategyListResponse {
  return (
    isObject(value) &&
    Array.isArray(value.strategies) &&
    value.strategies.every(isStrategySummary)
  );
}

function isStrategyParameter(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.name) &&
    (value.value_type === "integer" || value.value_type === "number") &&
    typeof value.required === "boolean" &&
    isNullableNumber(value.default)
  );
}

function isStrategyDetailResponse(value: unknown): value is StrategyDetailResponse {
  return (
    isStrategySummary(value) &&
    isObject(value) &&
    Array.isArray(value.parameters) &&
    value.parameters.every(isStrategyParameter)
  );
}

function isResearchRunSummary(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.experiment_slug) &&
    isString(value.run_id) &&
    isString(value.experiment_name) &&
    isString(value.strategy) &&
    (value.data_source === "csv" || value.data_source === "cache") &&
    isStringArray(value.symbols)
  );
}

function isResearchRunListResponse(value: unknown): value is ResearchRunListResponse {
  return (
    isObject(value) &&
    Array.isArray(value.runs) &&
    value.runs.every(isResearchRunSummary)
  );
}

function isResearchData(value: unknown): boolean {
  return (
    isObject(value) &&
    (value.source === "csv" || value.source === "cache") &&
    isStringArray(value.symbols)
  );
}

function isResearchParameters(value: unknown): boolean {
  return (
    isObject(value) &&
    isNumber(value.fast_window) &&
    isNumber(value.slow_window) &&
    isNumber(value.initial_capital) &&
    isNumber(value.transaction_cost_rate) &&
    isNumber(value.slippage_rate)
  );
}

function isResearchEvaluation(value: unknown): boolean {
  return (
    isObject(value) &&
    isNullableNumber(value.periods_per_year) &&
    isNumber(value.annual_risk_free_rate)
  );
}

function isResearchArtifacts(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.config) &&
    isString(value.metadata) &&
    isString(value.summary) &&
    isString(value.metrics) &&
    isString(value.logs_dir)
  );
}

function isResearchMetric(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.symbol) &&
    isNumber(value.initial_equity) &&
    isNumber(value.final_equity) &&
    isNumber(value.total_return) &&
    isNumber(value.max_drawdown) &&
    isNumber(value.periods) &&
    isNullableNumber(value.cagr) &&
    isNullableNumber(value.annualized_volatility) &&
    isNullableNumber(value.sharpe_ratio)
  );
}

function isResearchRunDetailResponse(
  value: unknown,
): value is ResearchRunDetailResponse {
  return (
    isObject(value) &&
    value.manifest_schema_version === 1 &&
    value.metrics_schema_version === 1 &&
    isString(value.experiment_slug) &&
    isString(value.run_id) &&
    isString(value.experiment_name) &&
    isString(value.strategy) &&
    isResearchData(value.data) &&
    isResearchParameters(value.parameters) &&
    isResearchEvaluation(value.evaluation) &&
    isResearchArtifacts(value.artifacts) &&
    Array.isArray(value.metrics) &&
    value.metrics.every(isResearchMetric)
  );
}

function isEvidenceManifestType(value: unknown): boolean {
  return (
    value === "strategy_decision_manifest" ||
    value === "report_artifact_manifest" ||
    value === "strategy_review_workflow_manifest"
  );
}

function isEvidenceManifestSummary(value: unknown): boolean {
  return (
    isObject(value) &&
    isEvidenceManifestType(value.manifest_type) &&
    isString(value.artifact_key) &&
    isString(value.manifest_id) &&
    isNumber(value.reference_count) &&
    isNullableString(value.created_by) &&
    isNullableString(value.created_timestamp) &&
    isNullableString(value.label) &&
    isNullableString(value.description)
  );
}

function isEvidenceManifestListResponse(
  value: unknown,
): value is EvidenceManifestListResponse {
  return (
    isObject(value) &&
    Array.isArray(value.manifests) &&
    value.manifests.every(isEvidenceManifestSummary)
  );
}

function isEvidenceManifestReference(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.reference_type) &&
    isString(value.reference_id) &&
    isNullableString(value.label) &&
    isNullableString(value.description)
  );
}

function isEvidenceManifestReferenceArray(value: unknown): boolean {
  return Array.isArray(value) && value.every(isEvidenceManifestReference);
}

function hasEvidenceManifestCommonFields(value: Record<string, unknown>): boolean {
  return (
    isString(value.artifact_key) &&
    value.schema_version === 1 &&
    isString(value.manifest_id) &&
    isNullableString(value.created_by) &&
    isNullableString(value.created_timestamp) &&
    isNullableString(value.description)
  );
}

function isEvidenceManifestDetailResponse(
  value: unknown,
): value is EvidenceManifestDetailResponse {
  if (!isObject(value) || !hasEvidenceManifestCommonFields(value)) {
    return false;
  }
  if (value.manifest_type === "strategy_decision_manifest") {
    return (
      isEvidenceManifestReferenceArray(value.summary_references) &&
      isEvidenceManifestReferenceArray(value.record_references)
    );
  }
  if (value.manifest_type === "report_artifact_manifest") {
    return (
      isNullableString(value.label) &&
      isNullableString(value.notes) &&
      isEvidenceManifestReferenceArray(value.references)
    );
  }
  if (value.manifest_type === "strategy_review_workflow_manifest") {
    return (
      isEvidenceManifestReferenceArray(value.state_snapshot_references) &&
      isEvidenceManifestReferenceArray(value.transition_proposal_references) &&
      isEvidenceManifestReferenceArray(value.transition_record_references)
    );
  }
  return false;
}

function isPaperJobStatus(value: unknown): value is PaperJobStatus {
  return (
    value === "queued" ||
    value === "running" ||
    value === "succeeded" ||
    value === "failed" ||
    value === "canceled"
  );
}

function isPaperJobAttemptStatus(value: unknown): boolean {
  return (
    value === "running" ||
    value === "succeeded" ||
    value === "failed" ||
    value === "interrupted"
  );
}

function isPaperJobErrorCode(value: unknown): boolean {
  return (
    value === null ||
    value === "workflow_validation_failed" ||
    value === "output_conflict" ||
    value === "filesystem_io_failed" ||
    value === "interrupted_without_output" ||
    value === "partial_output_detected" ||
    value === "invalid_output_detected"
  );
}

function isPaperJobAttempt(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.attempt_id) &&
    Number.isInteger(value.attempt_number) &&
    (value.attempt_number as number) > 0 &&
    isPaperJobAttemptStatus(value.status) &&
    isString(value.started_timestamp) &&
    isNullableString(value.completed_timestamp) &&
    isPaperJobErrorCode(value.error_code)
  );
}

function isPaperJobResponse(value: unknown): value is PaperJobResponse {
  return (
    isObject(value) &&
    isString(value.job_id) &&
    isString(value.run_id) &&
    isPaperJobStatus(value.status) &&
    isString(value.submitted_timestamp) &&
    isString(value.updated_timestamp) &&
    Number.isInteger(value.attempt_count) &&
    (value.attempt_count as number) >= 0 &&
    ((value.attempt_count === 0 && value.latest_attempt === null) ||
      ((value.attempt_count as number) > 0 && isPaperJobAttempt(value.latest_attempt))) &&
    ((value.result_available === true && isString(value.result_url)) ||
      (value.result_available === false && value.result_url === null))
  );
}

function isPaperJobSubmissionResponse(
  value: unknown,
): value is PaperJobSubmissionResponse {
  return (
    isObject(value) &&
    (value.submission_outcome === "created" ||
      value.submission_outcome === "replayed") &&
    isPaperJobResponse(value.job)
  );
}

function isPaperJobRecoveryResponse(
  value: unknown,
): value is PaperJobRecoverResponse {
  return (
    isObject(value) &&
    (value.recovery_outcome === "requeued" ||
      value.recovery_outcome === "succeeded" ||
      value.recovery_outcome === "failed") &&
    isPaperJobResponse(value.job)
  );
}

function isPaperJobListResponse(value: unknown): value is PaperJobListResponse {
  return Array.isArray(value) && value.every(isPaperJobResponse);
}

function isPaperJobAttemptListResponse(
  value: unknown,
): value is PaperJobAttemptListResponse {
  return Array.isArray(value) && value.every(isPaperJobAttempt);
}

function isPaperPosition(value: unknown): boolean {
  return isObject(value) && isString(value.symbol) && isNumber(value.quantity);
}

function isPaperPositionArray(value: unknown): boolean {
  return Array.isArray(value) && value.every(isPaperPosition);
}

function isPaperAccountState(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.timestamp) &&
    isNumber(value.starting_cash) &&
    isNumber(value.current_cash) &&
    isPaperPositionArray(value.positions)
  );
}

function isPaperOrder(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.order_id) &&
    isString(value.timestamp) &&
    isString(value.symbol) &&
    isString(value.side) &&
    isNumber(value.quantity) &&
    isString(value.status)
  );
}

function isPaperFill(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.timestamp) &&
    isString(value.symbol) &&
    isString(value.side) &&
    isNumber(value.quantity) &&
    isNumber(value.price) &&
    isNullableString(value.order_id)
  );
}

function isPaperPositionChange(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.symbol) &&
    isNumber(value.starting_quantity) &&
    isNumber(value.ending_quantity) &&
    isNumber(value.quantity_change)
  );
}

function isPaperSessionSummary(value: unknown): boolean {
  return (
    isObject(value) &&
    isString(value.session_start_timestamp) &&
    isString(value.session_end_timestamp) &&
    isNumber(value.starting_cash) &&
    isNumber(value.ending_cash) &&
    isNumber(value.cash_change) &&
    isPaperPositionArray(value.starting_positions) &&
    isPaperPositionArray(value.ending_positions) &&
    Array.isArray(value.position_changes) &&
    value.position_changes.every(isPaperPositionChange) &&
    Number.isInteger(value.order_count) &&
    (value.order_count as number) >= 0 &&
    Number.isInteger(value.fill_count) &&
    (value.fill_count as number) >= 0
  );
}

function isPaperTradingArtifact(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.created_timestamp) &&
    isPaperAccountState(value.starting_account_state) &&
    isPaperAccountState(value.ending_account_state) &&
    Array.isArray(value.orders) &&
    value.orders.every(isPaperOrder) &&
    Array.isArray(value.fills) &&
    value.fills.every(isPaperFill) &&
    isPaperSessionSummary(value.session_summary)
  );
}

function isPaperJobResultReference(value: unknown): boolean {
  return (
    isObject(value) &&
    value.record_schema_version === 1 &&
    value.root_type === "paper" &&
    value.artifact_schema_version === 1 &&
    value.result_summary_schema_version === 1 &&
    isString(value.created_timestamp)
  );
}

function isNonNegativeInteger(value: unknown): boolean {
  return Number.isInteger(value) && (value as number) >= 0;
}

function isPaperJobResultAudit(value: unknown): boolean {
  return (
    isObject(value) &&
    Number.isInteger(value.schema_version) &&
    isString(value.created_timestamp) &&
    isString(value.session_start_timestamp) &&
    isString(value.session_end_timestamp) &&
    isNumber(value.starting_cash) &&
    isNumber(value.ending_cash) &&
    isNumber(value.cash_change) &&
    isNonNegativeInteger(value.order_count) &&
    isNonNegativeInteger(value.fill_count) &&
    isNonNegativeInteger(value.starting_position_count) &&
    isNonNegativeInteger(value.ending_position_count) &&
    isNonNegativeInteger(value.position_change_count)
  );
}

function isPaperJobResultSummary(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.run_id) &&
    value.request_schema_version === 1 &&
    isString(value.request_created_timestamp) &&
    value.artifact_schema_version === 1 &&
    isString(value.artifact_created_timestamp) &&
    isPaperJobResultAudit(value.audit)
  );
}

function isPaperJobResultResponse(
  value: unknown,
): value is PaperJobResultResponse {
  return (
    isObject(value) &&
    isString(value.job_id) &&
    isString(value.run_id) &&
    isPaperJobResultReference(value.result_reference) &&
    isPaperTradingArtifact(value.artifact) &&
    isPaperJobResultSummary(value.result_summary)
  );
}

function isLifecycleEvidenceReference(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.reference_type) &&
    isString(value.reference_id) &&
    isNullableString(value.label) &&
    isNullableString(value.description)
  );
}

function isLifecycleSnapshot(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.snapshot_id) &&
    isString(value.strategy_id) &&
    isString(value.lifecycle_state) &&
    isString(value.rationale) &&
    isNullableString(value.declared_by) &&
    isNullableString(value.declared_timestamp) &&
    isStringArray(value.notes) &&
    isStringArray(value.warnings)
  );
}

function isLifecycleProposal(value: unknown): boolean {
  return (
    isObject(value) &&
    value.schema_version === 1 &&
    isString(value.proposal_id) &&
    isLifecycleSnapshot(value.source_snapshot) &&
    isString(value.target_state) &&
    isString(value.rationale) &&
    Array.isArray(value.evidence_references) &&
    value.evidence_references.every(isLifecycleEvidenceReference) &&
    isNullableString(value.requested_by) &&
    isNullableString(value.requested_timestamp) &&
    isStringArray(value.notes) &&
    isStringArray(value.warnings)
  );
}

function isLifecycleTransitionProposalResponse(
  value: unknown,
): value is LifecycleTransitionProposalResponse {
  return isObject(value) && isLifecycleProposal(value.proposal);
}

function isLifecycleTransitionReviewResponse(
  value: unknown,
): value is LifecycleTransitionReviewResponse {
  if (!isObject(value) || !isObject(value.transition_record)) {
    return false;
  }
  const record = value.transition_record;
  return (
    record.schema_version === 1 &&
    isString(record.transition_record_id) &&
    isLifecycleProposal(record.proposal) &&
    isString(record.review_outcome) &&
    isString(record.rationale) &&
    (record.resulting_snapshot === null ||
      isLifecycleSnapshot(record.resulting_snapshot)) &&
    isNullableString(record.reviewed_by) &&
    isNullableString(record.reviewed_timestamp) &&
    isStringArray(record.notes) &&
    isStringArray(record.warnings)
  );
}

function publicErrorEnvelope(value: unknown): PublicErrorEnvelope | null {
  if (!isObject(value) || !isObject(value.error)) {
    return null;
  }
  const code = boundedString(value.error.code, MAX_CODE_LENGTH);
  const message = boundedString(value.error.message, MAX_MESSAGE_LENGTH);
  const requestId = boundedString(value.request_id, MAX_REQUEST_ID_LENGTH);
  if (code === null || message === null || requestId === null) {
    return null;
  }
  return { error: { code, message }, request_id: requestId };
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function requestJson<Response>({
  path,
  validate,
  fetchImplementation,
  method = "GET",
  expectedStatuses = [200],
  requestBody,
  headers,
}: {
  path: string;
  validate: RuntimeValidator<Response>;
  fetchImplementation: typeof fetch;
  method?: "GET" | "POST";
  expectedStatuses?: readonly number[];
  requestBody?: unknown;
  headers?: Readonly<Record<string, string>>;
}): Promise<ApiResult<Response>> {
  let response: globalThis.Response;
  try {
    const requestHeaders: Record<string, string> = {
      Accept: "application/json",
      ...headers,
    };
    if (requestBody !== undefined) {
      requestHeaders["Content-Type"] = "application/json";
    }
    response = await fetchImplementation(`${API_BASE_PATH}${path}`, {
      method,
      cache: "no-store",
      headers: requestHeaders,
      ...(requestBody === undefined ? {} : { body: JSON.stringify(requestBody) }),
    });
  } catch {
    throw new ApiClientError({
      status: 0,
      code: "api_unavailable",
      publicMessage: "The local API is unavailable.",
      requestId: null,
    });
  }

  const body = await safeJson(response);
  const requestId = requestIdFrom(response);
  if (!response.ok || !expectedStatuses.includes(response.status)) {
    const envelope = publicErrorEnvelope(body);
    if (envelope !== null) {
      throw new ApiClientError({
        status: response.status,
        code: envelope.error.code,
        publicMessage: envelope.error.message,
        requestId: requestIdFrom(response, envelope.request_id),
      });
    }
    throw new ApiClientError({
      status: response.status,
      code: "api_request_failed",
      publicMessage: "The local API request failed.",
      requestId,
    });
  }

  if (!validate(body)) {
    throw new ApiClientError({
      status: response.status,
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId,
    });
  }

  return { data: body, requestId };
}

export function fetchHealth(
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<HealthResponse>> {
  return requestJson({
    path: HEALTH_PATH,
    validate: isHealthResponse,
    fetchImplementation,
  });
}

export function fetchDemoWorkspace(
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<DemoWorkspaceDescriptorResponse>> {
  return requestJson({
    path: DEMO_WORKSPACE_PATH,
    validate: isDemoWorkspaceDescriptor,
    fetchImplementation,
  });
}

export function fetchStrategies(
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<StrategyListResponse>> {
  return requestJson({
    path: STRATEGIES_PATH,
    validate: isStrategyListResponse,
    fetchImplementation,
  });
}

export function fetchStrategyDetail(
  strategyName: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<StrategyDetailResponse>> {
  return requestJson({
    path: STRATEGY_DETAIL_PATH.replace(
      "{strategy_name}",
      encodeURIComponent(strategyName),
    ),
    validate: isStrategyDetailResponse,
    fetchImplementation,
  });
}

export function fetchResearchRuns(
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<ResearchRunListResponse>> {
  return requestJson({
    path: RESEARCH_RUNS_PATH,
    validate: isResearchRunListResponse,
    fetchImplementation,
  });
}

export function fetchResearchRunDetail(
  experimentSlug: string,
  runId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<ResearchRunDetailResponse>> {
  return requestJson({
    path: RESEARCH_RUN_DETAIL_PATH.replace(
      "{experiment_slug}",
      encodeURIComponent(experimentSlug),
    ).replace("{run_id}", encodeURIComponent(runId)),
    validate: isResearchRunDetailResponse,
    fetchImplementation,
  });
}

export function fetchEvidenceManifests(
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<EvidenceManifestListResponse>> {
  return requestJson({
    path: EVIDENCE_MANIFESTS_PATH,
    validate: isEvidenceManifestListResponse,
    fetchImplementation,
  });
}

export function fetchEvidenceManifestDetail(
  manifestType: string,
  artifactKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<EvidenceManifestDetailResponse>> {
  return requestJson({
    path: EVIDENCE_MANIFEST_DETAIL_PATH.replace(
      "{manifest_type}",
      encodeURIComponent(manifestType),
    ).replace("{artifact_key}", encodeURIComponent(artifactKey)),
    validate: isEvidenceManifestDetailResponse,
    fetchImplementation,
  });
}

export function fetchPaperJobs(
  filters: { status: PaperJobStatus | null; limit: number },
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobListResponse>> {
  if (!Number.isInteger(filters.limit) || filters.limit < 1 || filters.limit > 200) {
    throw new TypeError("Paper job limit must be an integer between 1 and 200.");
  }
  const query = new URLSearchParams();
  if (filters.status !== null) {
    query.set("status", filters.status);
  }
  query.set("limit", String(filters.limit));
  return requestJson({
    path: `${PAPER_JOBS_PATH}?${query.toString()}`,
    validate: isPaperJobListResponse,
    fetchImplementation,
  });
}

function paperJobPath(template: string, jobId: string): string {
  return template.replace("{job_id}", encodeURIComponent(jobId));
}

export function fetchPaperJobDetail(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobResponse>> {
  return requestJson({
    path: paperJobPath(PAPER_JOB_DETAIL_PATH, jobId),
    validate: isPaperJobResponse,
    fetchImplementation,
  });
}

export function fetchPaperJobAttempts(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobAttemptListResponse>> {
  return requestJson({
    path: paperJobPath(PAPER_JOB_ATTEMPTS_PATH, jobId),
    validate: isPaperJobAttemptListResponse,
    fetchImplementation,
  });
}

export function fetchPaperJobResult(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobResultResponse>> {
  return requestJson({
    path: PAPER_JOB_RESULT_PATH.replace("{job_id}", encodeURIComponent(jobId)),
    validate: isPaperJobResultResponse,
    fetchImplementation,
  });
}

export function submitPaperJob(
  request: PaperJobSubmissionRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobSubmissionResponse>> {
  const headers =
    idempotencyKey.trim().length === 0
      ? undefined
      : { "Idempotency-Key": idempotencyKey };
  return requestJson({
    path: PAPER_JOBS_PATH,
    method: "POST",
    requestBody: request,
    headers,
    validate: isPaperJobSubmissionResponse,
    fetchImplementation,
  });
}

function mutatePaperJob<Response extends PaperJobResponse>(
  path: string,
  fetchImplementation: typeof fetch,
  body?: PaperJobRecoveryRequest,
): Promise<ApiResult<Response>> {
  return requestJson<Response>({
    path,
    method: "POST",
    requestBody: body,
    validate: isPaperJobResponse as RuntimeValidator<Response>,
    fetchImplementation,
  });
}

export function runPaperJob(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobRunAcceptedResponse>> {
  return requestJson({
    path: paperJobPath(PAPER_JOB_RUN_PATH, jobId),
    method: "POST",
    expectedStatuses: [202],
    validate: isPaperJobResponse,
    fetchImplementation,
  });
}

export function cancelPaperJob(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobCancelResponse>> {
  return mutatePaperJob<PaperJobCancelResponse>(
    paperJobPath(PAPER_JOB_CANCEL_PATH, jobId),
    fetchImplementation,
  );
}

export function retryPaperJob(
  jobId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobRetryResponse>> {
  return mutatePaperJob<PaperJobRetryResponse>(
    paperJobPath(PAPER_JOB_RETRY_PATH, jobId),
    fetchImplementation,
  );
}

export function recoverPaperJob(
  jobId: string,
  request: PaperJobRecoveryRequest,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperJobRecoverResponse>> {
  return requestJson({
    path: paperJobPath(PAPER_JOB_RECOVER_PATH, jobId),
    method: "POST",
    requestBody: request,
    validate: isPaperJobRecoveryResponse,
    fetchImplementation,
  });
}

export function submitLifecycleTransitionProposal(
  request: LifecycleTransitionProposalRequest,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<LifecycleTransitionProposalResponse>> {
  return requestJson({
    path: LIFECYCLE_TRANSITION_PROPOSALS_PATH,
    method: "POST",
    requestBody: request,
    validate: isLifecycleTransitionProposalResponse,
    fetchImplementation,
  });
}

export function submitLifecycleTransitionReview(
  request: LifecycleTransitionReviewRequest,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<LifecycleTransitionReviewResponse>> {
  return requestJson({
    path: LIFECYCLE_TRANSITION_RECORDS_PATH,
    method: "POST",
    requestBody: request,
    validate: isLifecycleTransitionReviewResponse,
    fetchImplementation,
  });
}

function marketTimePath(template: string, idKey: string, id: string): string {
  return template.replace(`{${idKey}}`, encodeURIComponent(id));
}

export function fetchTradingCalendars(
  filters: { market?: string | null } = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<TradingCalendarListResponse>> {
  const query = new URLSearchParams();
  if (filters.market !== undefined && filters.market !== null) {
    if (filters.market.length === 0 || filters.market !== filters.market.trim()) {
      throw new TypeError("Market must be a nonblank normalized string.");
    }
    query.set("market", filters.market);
  }
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${TRADING_CALENDARS_PATH}${suffix}`,
    validate: isTradingCalendarListResponse,
    fetchImplementation,
  });
}

export function fetchTradingCalendarDetail(
  calendarId: string,
  filters: {
    startDate?: string | null;
    endDate?: string | null;
    sessionType?: string | null;
  } = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<TradingCalendarDetailResponse>> {
  const query = new URLSearchParams();
  if (filters.startDate) query.set("start_date", filters.startDate);
  if (filters.endDate) query.set("end_date", filters.endDate);
  if (filters.sessionType) query.set("session_type", filters.sessionType);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${marketTimePath(
      TRADING_CALENDAR_DETAIL_PATH,
      "calendar_id",
      calendarId,
    )}${suffix}`,
    validate: isTradingCalendarDetailResponse,
    fetchImplementation,
  });
}

export function fetchMarketDataReplays(
  filters: { status?: ReplayStatus | null } = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<ReplaySessionListResponse>> {
  const query = new URLSearchParams();
  if (filters.status !== undefined && filters.status !== null) {
    if (!isReplayStatus(filters.status)) {
      throw new TypeError("Replay status is not supported.");
    }
    query.set("status", filters.status);
  }
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${MARKET_DATA_REPLAYS_PATH}${suffix}`,
    validate: isReplaySessionListResponse,
    fetchImplementation,
  });
}

export function fetchMarketDataReplayDetail(
  replayId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<MarketDataReplayDetailResponse>> {
  return requestJson({
    path: marketTimePath(
      MARKET_DATA_REPLAY_DETAIL_PATH,
      "replay_id",
      replayId,
    ),
    validate: isMarketDataReplayDetailResponse,
    fetchImplementation,
  });
}

function strategyOrderPath(
  template: string,
  parameter: string,
  identity: string,
): string {
  return template.replace(`{${parameter}}`, encodeURIComponent(identity));
}

function validateStrategyOrderListPaging(
  limit: number | undefined,
  cursor: string | null | undefined,
): void {
  if (
    limit !== undefined &&
    (!Number.isInteger(limit) || limit < 1 || limit > 200)
  ) {
    throw new TypeError(
      "Strategy-to-risk limit must be an integer between 1 and 200.",
    );
  }
  if (
    cursor !== undefined &&
    cursor !== null &&
    (cursor.length === 0 || cursor.length > 2048 || cursor !== cursor.trim())
  ) {
    throw new TypeError("Strategy-to-risk cursor is invalid.");
  }
}

function setBoundedStrategyOrderFilter(
  query: URLSearchParams,
  key: string,
  value: string | null | undefined,
  maximumLength = 512,
): void {
  if (value === undefined || value === null) return;
  if (
    value.length === 0 ||
    value.length > maximumLength ||
    value !== value.trim()
  ) {
    throw new TypeError(`Strategy-to-risk ${key} filter is invalid.`);
  }
  query.set(key, value);
}

export function fetchStrategySignals(
  filters: StrategySignalListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<StrategySignalListResponse>> {
  validateStrategyOrderListPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  setBoundedStrategyOrderFilter(
    query,
    "strategy_name",
    filters.strategy_name,
    128,
  );
  setBoundedStrategyOrderFilter(query, "instrument_id", filters.instrument_id);
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${STRATEGY_SIGNALS_PATH}${suffix}`,
    validate: isStrategySignalListResponse,
    fetchImplementation,
  });
}

export function evaluateStrategySignal(
  request: StrategySignalEvaluateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<StrategySignalCommandResponse>> {
  return requestJson({
    path: STRATEGY_SIGNAL_EVALUATE_PATH,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isStrategySignalCommandResponse,
    fetchImplementation,
  });
}

export function fetchStrategySignalDetail(
  signalId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<StrategySignalResponse>> {
  return requestJson({
    path: strategyOrderPath(
      STRATEGY_SIGNAL_DETAIL_PATH,
      "signal_id",
      signalId,
    ),
    validate: isStrategySignalResponse,
    fetchImplementation,
  });
}

export function fetchOrderIntents(
  filters: OrderIntentListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<OrderIntentListResponse>> {
  validateStrategyOrderListPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  setBoundedStrategyOrderFilter(query, "signal_id", filters.signal_id, 68);
  setBoundedStrategyOrderFilter(query, "account_id", filters.account_id);
  setBoundedStrategyOrderFilter(query, "instrument_id", filters.instrument_id);
  if (filters.side !== undefined && filters.side !== null) {
    if (filters.side !== "buy" && filters.side !== "sell") {
      throw new TypeError("Strategy-to-risk side filter is invalid.");
    }
    query.set("side", filters.side);
  }
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${ORDER_INTENTS_PATH}${suffix}`,
    validate: isOrderIntentListResponse,
    fetchImplementation,
  });
}

export function createOrderIntent(
  request: OrderIntentCreateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<OrderIntentCommandResponse>> {
  return requestJson({
    path: ORDER_INTENTS_PATH,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isOrderIntentCommandResponse,
    fetchImplementation,
  });
}

export function fetchOrderIntentDetail(
  intentId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<OrderIntentResponse>> {
  return requestJson({
    path: strategyOrderPath(ORDER_INTENT_DETAIL_PATH, "intent_id", intentId),
    validate: isOrderIntentResponse,
    fetchImplementation,
  });
}

export function fetchPreTradeRiskDecisions(
  filters: PreTradeRiskDecisionListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PreTradeRiskDecisionListResponse>> {
  validateStrategyOrderListPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  setBoundedStrategyOrderFilter(query, "intent_id", filters.intent_id, 67);
  setBoundedStrategyOrderFilter(query, "account_id", filters.account_id);
  if (filters.outcome !== undefined && filters.outcome !== null) {
    if (filters.outcome !== "allow" && filters.outcome !== "reject") {
      throw new TypeError("Strategy-to-risk outcome filter is invalid.");
    }
    query.set("outcome", filters.outcome);
  }
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${PRE_TRADE_RISK_DECISIONS_PATH}${suffix}`,
    validate: isPreTradeRiskDecisionListResponse,
    fetchImplementation,
  });
}

export function createPreTradeRiskDecision(
  request: PreTradeRiskDecisionCreateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PreTradeRiskDecisionCommandResponse>> {
  return requestJson({
    path: PRE_TRADE_RISK_DECISIONS_PATH,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isPreTradeRiskDecisionCommandResponse,
    fetchImplementation,
  });
}

export function fetchPreTradeRiskDecisionDetail(
  decisionId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PreTradeRiskDecisionResponse>> {
  return requestJson({
    path: strategyOrderPath(
      PRE_TRADE_RISK_DECISION_DETAIL_PATH,
      "decision_id",
      decisionId,
    ),
    validate: isPreTradeRiskDecisionResponse,
    fetchImplementation,
  });
}

function validatePaperExecutionPaging(
  limit: number | undefined,
  cursor: string | null | undefined,
): void {
  if (limit !== undefined && (!Number.isInteger(limit) || limit < 1 || limit > 200)) {
    throw new TypeError("Paper Execution limit must be an integer between 1 and 200.");
  }
  if (cursor !== undefined && cursor !== null
    && (cursor.length === 0 || cursor.length > 2048 || cursor !== cursor.trim())) {
    throw new TypeError("Paper Execution cursor is invalid.");
  }
}

function paperExecutionPath(template: string, placeholder: string, id: string): string {
  if (id.length === 0 || id.length > 512 || id !== id.trim()) {
    throw new TypeError("Paper Execution identifier is invalid.");
  }
  return template.replace(`{${placeholder}}`, encodeURIComponent(id));
}

function setPaperExecutionFilter(
  query: URLSearchParams,
  key: string,
  value: string | null | undefined,
): void {
  if (value === undefined || value === null) return;
  if (value.length === 0 || value.length > 512 || value !== value.trim()) {
    throw new TypeError(`Paper Execution ${key} filter is invalid.`);
  }
  query.set(key, value);
}

export function fetchPaperExecutionOrders(
  filters: PaperExecutionOrderListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionOrderListResponse>> {
  validatePaperExecutionPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  setPaperExecutionFilter(query, "account_id", filters.account_id);
  setPaperExecutionFilter(query, "replay_id", filters.replay_id);
  setPaperExecutionFilter(query, "trading_session_id", filters.trading_session_id);
  setPaperExecutionFilter(query, "instrument_id", filters.instrument_id);
  if (filters.side !== undefined && filters.side !== null) {
    if (filters.side !== "buy" && filters.side !== "sell") {
      throw new TypeError("Paper Execution side filter is invalid.");
    }
    query.set("side", filters.side);
  }
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${PAPER_EXECUTION_ORDERS_PATH}${suffix}`,
    validate: isPaperExecutionOrderListResponse,
    fetchImplementation,
  });
}

export function createPaperExecutionOrder(
  request: PaperExecutionOrderCreateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionOrderCommandResponse>> {
  return requestJson({
    path: PAPER_EXECUTION_ORDERS_PATH,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isPaperExecutionOrderCommandResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionOrderDetail(
  executionOrderId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionOrderViewResponse>> {
  return requestJson({
    path: paperExecutionPath(
      PAPER_EXECUTION_ORDER_DETAIL_PATH,
      "execution_order_id",
      executionOrderId,
    ),
    validate: isPaperExecutionOrderViewResponse,
    fetchImplementation,
  });
}

export function stepPaperExecutionOrder(
  executionOrderId: string,
  request: PaperExecutionOrderStepRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionStepCommandResponse>> {
  return requestJson({
    path: paperExecutionPath(
      PAPER_EXECUTION_ORDER_STEPS_PATH,
      "execution_order_id",
      executionOrderId,
    ),
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isPaperExecutionStepCommandResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionAttempts(
  executionOrderId: string,
  filters: PaperExecutionAttemptListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionAttemptListResponse>> {
  validatePaperExecutionPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${paperExecutionPath(
      PAPER_EXECUTION_ORDER_ATTEMPTS_PATH,
      "execution_order_id",
      executionOrderId,
    )}${suffix}`,
    validate: isPaperExecutionAttemptListResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionAttemptDetail(
  attemptId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionAttemptResponse>> {
  return requestJson({
    path: paperExecutionPath(PAPER_EXECUTION_ATTEMPT_DETAIL_PATH, "attempt_id", attemptId),
    validate: isPaperExecutionAttemptResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionFills(
  filters: PaperExecutionFillListFilters = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionFillListResponse>> {
  validatePaperExecutionPaging(filters.limit, filters.cursor);
  const query = new URLSearchParams();
  setPaperExecutionFilter(query, "execution_order_id", filters.execution_order_id);
  if (filters.limit !== undefined) query.set("limit", String(filters.limit));
  if (filters.cursor) query.set("cursor", filters.cursor);
  const suffix = query.size === 0 ? "" : `?${query.toString()}`;
  return requestJson({
    path: `${PAPER_EXECUTION_FILLS_PATH}${suffix}`,
    validate: isPaperExecutionFillListResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionFillDetail(
  fillId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionFillResponse>> {
  return requestJson({
    path: paperExecutionPath(PAPER_EXECUTION_FILL_DETAIL_PATH, "fill_id", fillId),
    validate: isPaperExecutionFillResponse,
    fetchImplementation,
  });
}

export function fetchPaperExecutionReconciliation(
  executionOrderId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperExecutionReconciliationResponse>> {
  return requestJson({
    path: paperExecutionPath(
      PAPER_EXECUTION_RECONCILIATION_PATH,
      "execution_order_id",
      executionOrderId,
    ),
    validate: isPaperExecutionReconciliationResponse,
    fetchImplementation,
  });
}

export function fetchPortfolioReviews(
  filters: { status: PortfolioReviewStatus | null; limit: number },
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PortfolioReviewListResponse>> {
  if (
    !Number.isInteger(filters.limit) ||
    filters.limit < 1 ||
    filters.limit > 200
  ) {
    throw new TypeError(
      "Portfolio review limit must be an integer between 1 and 200.",
    );
  }
  if (filters.status !== null && !isPortfolioReviewStatus(filters.status)) {
    throw new TypeError("Portfolio review status is not supported.");
  }
  const query = new URLSearchParams();
  if (filters.status !== null) {
    query.set("status", filters.status);
  }
  query.set("limit", String(filters.limit));
  return requestJson({
    path: `${PORTFOLIO_REVIEWS_PATH}?${query.toString()}`,
    validate: isPortfolioReviewListResponse,
    fetchImplementation,
  });
}

function portfolioReviewPath(template: string, reviewId: string): string {
  return template.replace("{review_id}", encodeURIComponent(reviewId));
}

export function fetchPortfolioReviewDetail(
  reviewId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PortfolioReviewDetailResponse>> {
  return requestJson({
    path: portfolioReviewPath(PORTFOLIO_REVIEW_DETAIL_PATH, reviewId),
    validate: isPortfolioReviewDetailResponse,
    fetchImplementation,
  });
}

function requireIdempotencyKey(idempotencyKey: string): Record<string, string> {
  if (
    idempotencyKey.length === 0 ||
    idempotencyKey.length > 128 ||
    idempotencyKey !== idempotencyKey.trim()
  ) {
    throw new TypeError(
      "An explicit nonblank normalized Idempotency-Key of at most 128 characters is required.",
    );
  }
  return { "Idempotency-Key": idempotencyKey };
}

export function createPortfolioReview(
  request: PortfolioReviewCreateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PortfolioReviewCommandResponse>> {
  return requestJson({
    path: PORTFOLIO_REVIEWS_PATH,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isPortfolioReviewCommandResponse,
    fetchImplementation,
  });
}

export function submitPortfolioReviewDecision(
  reviewId: string,
  request: PortfolioReviewDecisionRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PortfolioReviewCommandResponse>> {
  return requestJson({
    path: portfolioReviewPath(PORTFOLIO_REVIEW_DECISION_PATH, reviewId),
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate: isPortfolioReviewCommandResponse,
    fetchImplementation,
  });
}

function paperAccountPath(template: string, accountId: string): string {
  return template.replace("{account_id}", encodeURIComponent(accountId));
}

export function fetchPaperAccounts(
  filters: {
    lifecycleStatus: PaperAccountLifecycleStatus | null;
    limit: number;
    cursor?: string | null;
  },
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountListResponse>> {
  if (
    !Number.isInteger(filters.limit) ||
    filters.limit < 1 ||
    filters.limit > 200
  ) {
    throw new TypeError(
      "Paper Account limit must be an integer between 1 and 200.",
    );
  }
  if (
    filters.lifecycleStatus !== null &&
    !isPaperAccountLifecycleStatus(filters.lifecycleStatus)
  ) {
    throw new TypeError("Paper Account lifecycle status is not supported.");
  }
  const query = new URLSearchParams();
  if (filters.lifecycleStatus !== null) {
    query.set("lifecycle_status", filters.lifecycleStatus);
  }
  query.set("limit", String(filters.limit));
  if (filters.cursor) {
    query.set("cursor", filters.cursor);
  }
  return requestJson({
    path: `${PAPER_ACCOUNTS_PATH}?${query.toString()}`,
    validate: isPaperAccountListResponse,
    fetchImplementation,
  });
}

export function fetchPaperAccountDetail(
  accountId: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountDetailResponse>> {
  return requestJson({
    path: paperAccountPath(PAPER_ACCOUNT_DETAIL_PATH, accountId),
    validate: isPaperAccountDetailResponse,
    fetchImplementation,
  });
}

export function fetchPaperAccountLedger(
  accountId: string,
  options: { afterSequenceNumber?: number; limit?: number } = {},
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountLedgerResponse>> {
  const afterSequenceNumber = options.afterSequenceNumber ?? 0;
  const limit = options.limit ?? 50;
  if (
    !Number.isInteger(afterSequenceNumber) ||
    afterSequenceNumber < 0 ||
    !Number.isInteger(limit) ||
    limit < 1 ||
    limit > 200
  ) {
    throw new TypeError("Paper Account ledger pagination is invalid.");
  }
  const query = new URLSearchParams({
    after_sequence_number: String(afterSequenceNumber),
    limit: String(limit),
  });
  return requestJson({
    path: `${paperAccountPath(PAPER_ACCOUNT_LEDGER_PATH, accountId)}?${query.toString()}`,
    validate: isPaperAccountLedgerResponse,
    fetchImplementation,
  });
}

function mutatePaperAccount<Request, Response>({
  path,
  request,
  idempotencyKey,
  validate,
  fetchImplementation,
}: {
  path: string;
  request: Request;
  idempotencyKey: string;
  validate: RuntimeValidator<Response>;
  fetchImplementation: typeof fetch;
}): Promise<ApiResult<Response>> {
  return requestJson({
    path,
    method: "POST",
    expectedStatuses: [200, 201],
    requestBody: request,
    headers: requireIdempotencyKey(idempotencyKey),
    validate,
    fetchImplementation,
  });
}

export function createPaperAccount(
  request: PaperAccountCreateRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountCommandResponse>> {
  return mutatePaperAccount({
    path: PAPER_ACCOUNTS_PATH,
    request,
    idempotencyKey,
    validate: isPaperAccountCommandResponse,
    fetchImplementation,
  });
}

export function postPaperAccountCashMovement(
  accountId: string,
  request: PaperAccountCashMovementRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(PAPER_ACCOUNT_CASH_MOVEMENTS_PATH, accountId),
    request,
    idempotencyKey,
    validate: isPaperAccountCommandResponse,
    fetchImplementation,
  });
}

export function postPaperAccountPositionAdjustment(
  accountId: string,
  request: PaperAccountPositionAdjustmentRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(
      PAPER_ACCOUNT_POSITION_ADJUSTMENTS_PATH,
      accountId,
    ),
    request,
    idempotencyKey,
    validate: isPaperAccountCommandResponse,
    fetchImplementation,
  });
}

export function linkPaperAccountEvidence(
  accountId: string,
  request: PaperAccountEvidenceLinkRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(PAPER_ACCOUNT_EVIDENCE_LINKS_PATH, accountId),
    request,
    idempotencyKey,
    validate: isPaperAccountCommandResponse,
    fetchImplementation,
  });
}

export function changePaperAccountLifecycle(
  accountId: string,
  request: PaperAccountLifecycleRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(PAPER_ACCOUNT_LIFECYCLE_PATH, accountId),
    request,
    idempotencyKey,
    validate: isPaperAccountCommandResponse,
    fetchImplementation,
  });
}

export function createPaperAccountSnapshot(
  accountId: string,
  request: PaperAccountEvidenceOperationRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountSnapshotCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(PAPER_ACCOUNT_SNAPSHOTS_PATH, accountId),
    request,
    idempotencyKey,
    validate: isPaperAccountSnapshotCommandResponse,
    fetchImplementation,
  });
}

export function reconcilePaperAccount(
  accountId: string,
  request: PaperAccountEvidenceOperationRequest,
  idempotencyKey: string,
  fetchImplementation: typeof fetch = fetch,
): Promise<ApiResult<PaperAccountReconciliationCommandResponse>> {
  return mutatePaperAccount({
    path: paperAccountPath(PAPER_ACCOUNT_RECONCILIATIONS_PATH, accountId),
    request,
    idempotencyKey,
    validate: isPaperAccountReconciliationCommandResponse,
    fetchImplementation,
  });
}
