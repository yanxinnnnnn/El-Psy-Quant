import { useTranslations } from "next-intl";

const SUPPORTED_ERROR_CODES = [
  "api_unavailable",
  "api_request_failed",
  "api_response_invalid",
  "not_found",
  "research_artifact_root_unavailable",
  "research_artifact_invalid",
  "research_run_not_found",
  "evidence_artifact_root_unavailable",
  "evidence_artifact_invalid",
  "evidence_manifest_not_found",
  "product_database_unavailable",
  "paper_artifact_root_unavailable",
  "paper_job_not_found",
  "paper_job_invalid",
  "paper_job_idempotency_conflict",
  "paper_job_conflict",
  "paper_job_state_conflict",
  "paper_job_output_conflict",
  "paper_job_recovery_failed",
  "paper_job_result_unavailable",
  "paper_job_result_invalid",
  "lifecycle_transition_proposal_invalid",
  "lifecycle_transition_record_invalid",
  "request_validation_error",
  "demo_workspace_not_configured",
  "demo_workspace_unavailable",
] as const;

type SupportedErrorCode = (typeof SUPPORTED_ERROR_CODES)[number];
const SUPPORTED_ERROR_CODE_SET: ReadonlySet<string> = new Set(SUPPORTED_ERROR_CODES);

const CONTEXTUAL_TITLE_ERROR_CODES = new Set([
  "api_unavailable",
  "api_request_failed",
  "api_response_invalid",
]);

export function useErrorPresentation(code: string | null | undefined) {
  const t = useTranslations("errors");
  const key: SupportedErrorCode | "unknown" = code && SUPPORTED_ERROR_CODE_SET.has(code)
    ? code as SupportedErrorCode
    : "unknown";
  const known = key !== "unknown";
  return {
    known,
    useContextTitle: !known || CONTEXTUAL_TITLE_ERROR_CODES.has(code ?? ""),
    title: t(`${key}.title` as const),
    explanation: t(`${key}.explanation` as const),
    recovery: t(`${key}.recovery` as const),
  };
}
