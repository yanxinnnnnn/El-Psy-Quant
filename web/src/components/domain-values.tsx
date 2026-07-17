"use client";

import { useTranslations } from "next-intl";

import { StatusBadge, type StatusTone } from "@/components/ui/status-badge";
export function PaperJobStatusValue({ value }: { value: string }) {
  const t = useTranslations("paperJobs.statuses");
  const label = value === "queued" ? t("queued")
    : value === "running" ? t("running")
      : value === "succeeded" ? t("succeeded")
        : value === "failed" ? t("failed")
          : value === "canceled" ? t("canceled")
            : t("unknown");
  const tone: StatusTone = value === "succeeded" ? "success"
    : value === "failed" ? "danger"
      : value === "canceled" ? "unavailable"
        : value === "queued" || value === "running" ? "info"
          : "neutral";
  return <StatusBadge label={label} rawValue={value} tone={tone} />;
}

export function PaperJobAttemptStatusValue({ value }: { value: string }) {
  const t = useTranslations("paperJobs.attemptStatuses");
  const label = value === "running" ? t("running")
    : value === "succeeded" ? t("succeeded")
      : value === "failed" ? t("failed")
        : value === "interrupted" ? t("interrupted")
          : t("unknown");
  const tone: StatusTone = value === "running" ? "info"
    : value === "succeeded" ? "success"
      : value === "failed" ? "danger"
        : value === "interrupted" ? "warning"
          : "neutral";
  return <StatusBadge label={label} rawValue={value} tone={tone} />;
}

export function PaperJobAttemptSummary({
  attemptNumber,
  status,
}: {
  attemptNumber: number;
  status: string;
}) {
  const t = useTranslations("paperJobs.attemptStatuses");
  return (
    <span className="paper-attempt-summary">
      <span>{t("attemptNumber", { number: attemptNumber })}</span>
      <PaperJobAttemptStatusValue value={status} />
    </span>
  );
}

export function AttemptErrorValue({ code }: { code: string | null }) {
  const t = useTranslations("paperJobs.attemptErrors");
  const common = useTranslations("common.states");
  if (code === null) return <>{common("notAvailable")}</>;
  const label = code === "workflow_validation_failed" ? t("workflow_validation_failed")
    : code === "output_conflict" ? t("output_conflict")
      : code === "filesystem_io_failed" ? t("filesystem_io_failed")
        : code === "interrupted_without_output" ? t("interrupted_without_output")
          : code === "partial_output_detected" ? t("partial_output_detected")
            : code === "invalid_output_detected" ? t("invalid_output_detected")
              : t("unknown");
  return <>{`${label} (${code})`}</>;
}

export function LifecycleStateValue({ value }: { value: string }) {
  const t = useTranslations("lifecycle.states");
  const label = value === "research_review" ? t("research_review")
    : value === "paper_review" ? t("paper_review")
      : value === "watchlist" ? t("watchlist")
        : value === "on_hold" ? t("on_hold")
          : value === "rejected" ? t("rejected")
            : null;
  const tone: StatusTone = value === "rejected" ? "danger"
    : value === "on_hold" ? "warning"
      : value === "research_review" || value === "paper_review" ? "info"
        : "neutral";
  return <StatusBadge label={label ?? value} rawValue={value} tone={tone} />;
}

export function ReviewOutcomeValue({ value }: { value: string }) {
  const t = useTranslations("lifecycle.outcomes");
  const label = value === "approved" ? t("approved")
    : value === "rejected" ? t("rejected")
      : value === "deferred" ? t("deferred")
        : null;
  const tone: StatusTone = value === "rejected" ? "danger"
    : value === "deferred" ? "warning"
      : value === "approved" ? "info"
        : "neutral";
  return <StatusBadge label={label ?? value} rawValue={value} tone={tone} />;
}
