import { useTranslations } from "next-intl";

export type ErrorCategory =
  | "authentication"
  | "not_found"
  | "invalid"
  | "conflict"
  | "unavailable"
  | "protocol"
  | "internal"
  | "unknown";

export const ERROR_PRESENTATION_INVENTORY = {
  api_unavailable: "unavailable",
  api_request_failed: "unavailable",
  api_response_invalid: "invalid",
  not_found: "not_found",
  method_not_allowed: "protocol",
  http_error: "protocol",
  request_validation_error: "invalid",
  internal_server_error: "internal",
  founder_authentication_required: "authentication",
  research_artifact_root_unavailable: "unavailable",
  research_run_not_found: "not_found",
  research_artifact_invalid: "invalid",
  evidence_artifact_root_unavailable: "unavailable",
  evidence_manifest_not_found: "not_found",
  evidence_artifact_invalid: "invalid",
  paper_run_invalid: "invalid",
  product_database_unavailable: "unavailable",
  paper_artifact_root_unavailable: "unavailable",
  paper_job_not_found: "not_found",
  paper_job_invalid: "invalid",
  paper_job_idempotency_conflict: "conflict",
  paper_job_conflict: "conflict",
  paper_job_state_conflict: "conflict",
  paper_job_output_conflict: "conflict",
  paper_job_recovery_failed: "unavailable",
  paper_job_result_unavailable: "conflict",
  paper_job_result_invalid: "invalid",
  lifecycle_transition_proposal_invalid: "invalid",
  lifecycle_transition_record_invalid: "invalid",
  portfolio_review_not_found: "not_found",
  portfolio_review_invalid: "invalid",
  portfolio_review_conflict: "conflict",
  portfolio_review_idempotency_conflict: "conflict",
  portfolio_review_settled_conflict: "conflict",
  portfolio_review_artifact_conflict: "conflict",
  portfolio_review_artifact_invalid: "invalid",
  portfolio_review_artifact_unavailable: "unavailable",
  portfolio_review_artifact_root_unavailable: "unavailable",
  paper_account_not_found: "not_found",
  paper_account_version_conflict: "conflict",
  paper_account_idempotency_conflict: "conflict",
  paper_account_frozen: "conflict",
  paper_account_closed: "conflict",
  paper_account_close_not_empty: "conflict",
  paper_account_insufficient_available_cash: "conflict",
  paper_account_negative_position: "conflict",
  paper_account_negative_cost_basis: "conflict",
  paper_account_zero_quantity_nonzero_cost_basis: "conflict",
  paper_account_invalid_decimal: "invalid",
  paper_account_invalid_m30_reference: "invalid",
  paper_account_projection_stale: "conflict",
  paper_account_reconciliation_failed: "conflict",
  paper_account_snapshot_conflict: "conflict",
  paper_account_storage_busy: "unavailable",
  paper_account_schema_incompatible: "unavailable",
  market_time_not_found: "not_found",
  market_time_invalid: "invalid",
  strategy_signal_not_found: "not_found",
  order_intent_not_found: "not_found",
  pre_trade_risk_decision_not_found: "not_found",
  strategy_order_idempotency_conflict: "conflict",
  strategy_order_stale_authority: "conflict",
  strategy_order_reconciliation_required: "conflict",
  strategy_order_invalid_runtime_configuration: "invalid",
  strategy_order_invalid_risk_policy: "invalid",
  strategy_order_invalid_decimal: "invalid",
  strategy_order_invalid_cursor: "invalid",
  strategy_order_authority_unavailable: "unavailable",
  strategy_order_storage_busy: "unavailable",
  strategy_order_schema_incompatible: "unavailable",
  strategy_order_storage_failure: "unavailable",
  paper_execution_upstream_authority_not_found: "not_found",
  paper_execution_order_not_found: "not_found",
  paper_execution_attempt_not_found: "not_found",
  paper_execution_fill_not_found: "not_found",
  paper_execution_idempotency_conflict: "conflict",
  paper_execution_stale_authority: "conflict",
  paper_execution_operation_conflict: "conflict",
  paper_execution_concurrency_conflict: "conflict",
  paper_execution_reconciliation_required: "conflict",
  paper_execution_invalid_policy: "invalid",
  paper_execution_invalid_decimal: "invalid",
  paper_execution_invalid_cursor: "invalid",
  paper_execution_authority_unavailable: "unavailable",
  paper_execution_schema_incompatible: "unavailable",
  paper_execution_storage_busy: "unavailable",
  paper_execution_storage_failure: "unavailable",
  demo_workspace_not_configured: "not_found",
  demo_workspace_unavailable: "unavailable",
} as const satisfies Readonly<Record<string, Exclude<ErrorCategory, "unknown">>>;

export type SupportedErrorCode = keyof typeof ERROR_PRESENTATION_INVENTORY;
export const SUPPORTED_ERROR_CODES = Object.freeze(
  Object.keys(ERROR_PRESENTATION_INVENTORY) as SupportedErrorCode[],
);

const CONTEXTUAL_TITLE_ERROR_CODES: ReadonlySet<string> = new Set([
  "api_unavailable",
  "api_request_failed",
  "api_response_invalid",
  "not_found",
  "internal_server_error",
]);

export function useErrorPresentation(code: string | null | undefined) {
  const t = useTranslations("errors");
  const known = Boolean(
    code
    && Object.prototype.hasOwnProperty.call(ERROR_PRESENTATION_INVENTORY, code),
  );
  const key: SupportedErrorCode | "unknown" = known
    ? code as SupportedErrorCode
    : "unknown";
  const category: ErrorCategory = known
    ? ERROR_PRESENTATION_INVENTORY[key as SupportedErrorCode]
    : "unknown";
  return {
    known,
    category,
    stateLabel: t(`categories.${category}` as const),
    useContextTitle: !known || CONTEXTUAL_TITLE_ERROR_CODES.has(code ?? ""),
    title: t(`${key}.title` as const),
    explanation: t(`${key}.explanation` as const),
    recovery: t(`${key}.recovery` as const),
  };
}
