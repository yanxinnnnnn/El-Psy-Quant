import type { paths } from "@/generated/api-types";

const API_BASE_PATH = "/api/backend";
const HEALTH_PATH = "/api/v1/health";
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

export type HealthResponse = SuccessResponse<typeof HEALTH_PATH>;
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

function isPaperJobListResponse(value: unknown): value is PaperJobListResponse {
  return Array.isArray(value) && value.every(isPaperJobResponse);
}

function isPaperJobAttemptListResponse(
  value: unknown,
): value is PaperJobAttemptListResponse {
  return Array.isArray(value) && value.every(isPaperJobAttempt);
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
    validate: isPaperJobResponse,
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
  return mutatePaperJob<PaperJobRecoverResponse>(
    paperJobPath(PAPER_JOB_RECOVER_PATH, jobId),
    fetchImplementation,
    request,
  );
}
