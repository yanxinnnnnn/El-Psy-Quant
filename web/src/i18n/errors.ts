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
