"use client";

import { useTranslations } from "next-intl";

import type { PaperJobStatus } from "@/lib/api-client";

export function PaperJobStatusValue({ value }: { value: PaperJobStatus }) {
  const t = useTranslations("paperJobs.statuses");
  const label = value === "queued" ? t("queued")
    : value === "running" ? t("running")
      : value === "succeeded" ? t("succeeded")
        : value === "failed" ? t("failed")
          : t("canceled");
  return <span className={`job-status job-status--${value}`}><span>{label}</span> <code>{value}</code></span>;
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
  return <>{label ? <span>{label} </span> : null}<code>{value}</code></>;
}

export function ReviewOutcomeValue({ value }: { value: string }) {
  const t = useTranslations("lifecycle.outcomes");
  const label = value === "approved" ? t("approved")
    : value === "rejected" ? t("rejected")
      : value === "deferred" ? t("deferred")
        : null;
  return <>{label ? <span>{label} </span> : null}<code>{value}</code></>;
}
