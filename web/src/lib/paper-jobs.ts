import type {
  PaperJobAttemptListResponse,
  PaperJobStatus,
} from "@/lib/api-client";

export const paperJobStatuses: readonly PaperJobStatus[] = [
  "queued",
  "running",
  "succeeded",
  "failed",
  "canceled",
];

export const paperJobLimits = [25, 50, 100, 200] as const;

export type PaperJobAction = "run" | "cancel" | "retry" | "recover";

const paperJobActionMatrix: Readonly<
  Record<PaperJobStatus, readonly PaperJobAction[]>
> = {
  queued: ["run", "cancel"],
  running: ["recover"],
  failed: ["retry"],
  succeeded: [],
  canceled: [],
};

export function paperJobActionsForStatus(
  status: string,
): readonly PaperJobAction[] {
  return Object.prototype.hasOwnProperty.call(paperJobActionMatrix, status)
    ? paperJobActionMatrix[status as PaperJobStatus]
    : [];
}

export function reconcilePaperJobAttempts(
  sourceAttempts: readonly PaperJobAttemptListResponse[number][],
  mutationAttempts: readonly PaperJobAttemptListResponse[number][],
): PaperJobAttemptListResponse {
  const mutationById = new Map(
    mutationAttempts.map((attempt) => [attempt.attempt_id, attempt]),
  );
  const sourceIds = new Set(
    sourceAttempts.map((attempt) => attempt.attempt_id),
  );
  const reconciled = sourceAttempts.map(
    (attempt) => mutationById.get(attempt.attempt_id) ?? attempt,
  );
  for (const attempt of mutationAttempts) {
    if (!sourceIds.has(attempt.attempt_id)) {
      reconciled.push(attempt);
      sourceIds.add(attempt.attempt_id);
    }
  }
  return reconciled;
}

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
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|\+00:00)$/.exec(value);
  if (match === null) {
    return false;
  }

  const [, yearText, monthText, dayText, hourText, minuteText, secondText] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) {
    return false;
  }

  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day >= 1 && day <= daysInMonth[month - 1];
}

export function isExplicitUtcTimestampAtOrAfter(
  value: string,
  minimum: string,
): boolean {
  if (!isExplicitUtcTimestamp(value) || !isExplicitUtcTimestamp(minimum)) {
    return false;
  }
  const instant = Date.parse(value);
  const minimumInstant = Date.parse(minimum);
  return (
    Number.isFinite(instant) &&
    Number.isFinite(minimumInstant) &&
    instant >= minimumInstant
  );
}
