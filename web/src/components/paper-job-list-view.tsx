"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import {
  AttemptErrorValue,
  PaperJobAttemptSummary,
  PaperJobStatusValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { useErrorPresentation } from "@/i18n/errors";
import {
  fetchPaperJobs,
  type PaperJobResponse,
  type PaperJobStatus,
} from "@/lib/api-client";
import { paperJobLimits, paperJobStatuses } from "@/lib/paper-jobs";
import { useApiResource } from "@/lib/use-api-resource";

function JobCard({ job }: { job: PaperJobResponse }) {
  const t = useTranslations("paperJobs.list");
  const common = useTranslations("common.states");
  return (
    <li className="record-card">
      <div>
        <p className="record-card__meta">{job.job_id}</p>
        <h2>{job.run_id}</h2>
        <dl className="compact-definitions compact-definitions--jobs">
          <div><dt>{t("status")}</dt><dd><PaperJobStatusValue value={job.status} /></dd></div>
          <div><dt>{t("submitted")}</dt><dd><LocalizedTimestamp value={job.submitted_timestamp} /></dd></div>
          <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={job.updated_timestamp} /></dd></div>
          <div><dt>{t("attemptCount")}</dt><dd>{job.attempt_count}</dd></div>
          <div><dt>{t("latestAttempt")}</dt><dd>{job.latest_attempt ? <PaperJobAttemptSummary attemptNumber={job.latest_attempt.attempt_number} status={job.latest_attempt.status} /> : common("notAvailable")}</dd></div>
          <div><dt>{t("latestError")}</dt><dd><AttemptErrorValue code={job.latest_attempt?.error_code ?? null} /></dd></div>
          <div><dt>{t("resultAvailable")}</dt><dd>{job.result_available ? common("yes") : common("no")}</dd></div>
        </dl>
      </div>
      <Link
        className="primary-link"
        href={`/paper-jobs/${encodeURIComponent(job.job_id)}`}
      >
        {t("inspect")}
      </Link>
    </li>
  );
}

export function PaperJobListView() {
  const t = useTranslations("paperJobs.list");
  const statuses = useTranslations("paperJobs.statuses");
  const [draftStatus, setDraftStatus] = useState<PaperJobStatus | "all">("all");
  const [draftLimit, setDraftLimit] = useState<(typeof paperJobLimits)[number]>(50);
  const [filters, setFilters] = useState<{
    status: PaperJobStatus | null;
    limit: (typeof paperJobLimits)[number];
  }>({ status: null, limit: 50 });
  const request = useCallback(() => fetchPaperJobs(filters), [filters]);
  const { state, retry } = useApiResource(request);
  const error = useErrorPresentation(state.status === "error" ? state.code : null);

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <Link className="primary-link" href="/paper-jobs/new">
          {t("submit")}
        </Link>
      </header>

      <form
        className="filter-bar"
        aria-label={t("filtersAria")}
        onSubmit={(event) => {
          event.preventDefault();
          setFilters({
            status: draftStatus === "all" ? null : draftStatus,
            limit: draftLimit,
          });
        }}
      >
        <label>
          {t("status")}
          <select
            value={draftStatus}
            onChange={(event) => setDraftStatus(event.target.value as PaperJobStatus | "all")}
          >
            <option value="all">{t("allStatuses")}</option>
            {paperJobStatuses.map((status) => <option key={status} value={status}>{status === "queued" ? statuses("queued") : status === "running" ? statuses("running") : status === "succeeded" ? statuses("succeeded") : status === "failed" ? statuses("failed") : statuses("canceled")} ({status})</option>)}
          </select>
        </label>
        <label>
          {t("limit")}
          <select
            value={draftLimit}
            onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof paperJobLimits)[number])}
          >
            {paperJobLimits.map((limit) => <option key={limit} value={limit}>{limit}</option>)}
          </select>
        </label>
        <button className="secondary-button" type="submit">{t("apply")}</button>
        <button className="secondary-button" type="button" onClick={retry}>{t("refresh")}</button>
      </form>

      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailableTitle") : error.title}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.length === 0 ? (
        <EmptyState
          title={t("emptyTitle")}
          message={t("emptyMessage")}
        />
      ) : (
        <ol className="card-list" aria-label={t("ariaLabel")}>
          {state.data.map((job) => <JobCard key={job.job_id} job={job} />)}
        </ol>
      )}
    </div>
  );
}
