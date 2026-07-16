import { ApiClientError } from "@/lib/api-client";

export const comparisonCandidateLimits = [25, 50, 100, 200] as const;

export type ComparisonSelectionErrorKey = "blank" | "duplicate" | "minimum" | "maximum";

export function comparisonSelectionErrorKey(jobIds: readonly string[]): ComparisonSelectionErrorKey | null {
  if (jobIds.length === 0) return null;
  if (jobIds.some((jobId) => jobId.trim().length === 0)) return "blank";
  if (new Set(jobIds).size !== jobIds.length) return "duplicate";
  if (jobIds.length < 2) return "minimum";
  if (jobIds.length > 4) return "maximum";
  return null;
}

export function comparisonSelectionError(jobIds: readonly string[]): string | null {
  const key = comparisonSelectionErrorKey(jobIds);
  if (key === "blank") return "Comparison job IDs must be nonblank.";
  if (key === "duplicate") return "Comparison job IDs must be distinct. Duplicate IDs are not allowed.";
  if (key === "minimum") return "Select at least two backend-available results before comparing.";
  if (key === "maximum") return "Select no more than four backend-available results before comparing.";
  return null;
}

export function comparisonHref(jobIds: readonly string[]): string {
  const query = jobIds
    .map((jobId) => `job_id=${encodeURIComponent(jobId)}`)
    .join("&");
  return `/comparisons?${query}`;
}

export function comparisonCandidateErrorTitle(code: string): string {
  return code === "product_database_unavailable"
    ? "Product database unavailable"
    : "Comparison candidates unavailable";
}

export function comparisonResultErrorTitle(code: string): string {
  const titles: Readonly<Record<string, string>> = {
    product_database_unavailable: "Product database unavailable",
    paper_artifact_root_unavailable: "Paper artifact root unavailable",
    paper_job_not_found: "Paper job not found",
    paper_job_result_unavailable: "Paper job result unavailable",
    paper_job_result_invalid: "Paper job result is invalid",
  };
  return titles[code] ?? "Comparison result unavailable";
}

export type ComparisonFailure = Readonly<{
  code: string;
  message: string;
  requestId: string | null;
}>;

export function comparisonFailure(error: unknown): ComparisonFailure {
  if (error instanceof ApiClientError) {
    return {
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
    };
  }
  return {
    code: "api_unavailable",
    message: "The local API is unavailable.",
    requestId: null,
  };
}
