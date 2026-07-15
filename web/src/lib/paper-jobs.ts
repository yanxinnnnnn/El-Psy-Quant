import type { PaperJobStatus } from "@/lib/api-client";

export const paperJobStatuses: readonly PaperJobStatus[] = [
  "queued",
  "running",
  "succeeded",
  "failed",
  "canceled",
];

export const paperJobLimits = [25, 50, 100, 200] as const;

export function paperJobErrorTitle(code: string, list = false): string {
  const titles: Readonly<Record<string, string>> = {
    product_database_unavailable: "Product database unavailable",
    paper_artifact_root_unavailable: "Paper artifact root unavailable",
    paper_job_not_found: "Paper job not found",
    paper_job_invalid: "Paper job request is invalid",
    paper_job_idempotency_conflict:
      "Idempotency key conflicts with another request",
    paper_job_conflict: "Paper job conflicts with an existing job",
    paper_job_state_conflict: "Paper job state changed",
    paper_job_output_conflict: "Existing paper output conflicts with this operation",
    paper_job_recovery_failed: "Paper job recovery inspection failed",
  };
  return titles[code] ?? (list ? "Paper jobs unavailable" : "Paper job operation failed");
}

export function paperJobErrorGuidance(code: string, message: string): string {
  if (code === "paper_job_state_conflict") {
    return `${message} Another action or execution may have changed the state. Refresh status manually before deciding what to do next.`;
  }
  return message;
}

export function attemptErrorDescription(code: string | null): string {
  if (code === null) {
    return "Not available";
  }
  const descriptions: Readonly<Record<string, string>> = {
    workflow_validation_failed: "Workflow validation failed",
    output_conflict: "Output conflict",
    filesystem_io_failed: "Filesystem I/O failed",
    interrupted_without_output: "Interrupted without output",
    partial_output_detected: "Partial output detected",
    invalid_output_detected: "Invalid output detected",
  };
  return `${descriptions[code] ?? "Operational attempt error"} (${code})`;
}

export function isExplicitUtcTimestamp(value: string): boolean {
  return (
    value.length > 0 &&
    (value.endsWith("Z") || value.endsWith("+00:00") || value.endsWith("-00:00")) &&
    Number.isFinite(Date.parse(value))
  );
}
