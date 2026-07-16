"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { AttemptErrorValue, PaperJobStatusValue } from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { useErrorPresentation } from "@/i18n/errors";
import { fetchPaperJobs, type PaperJobResponse } from "@/lib/api-client";
import { portfolioRecordLimits } from "@/lib/portfolio-records";
import { useApiResource } from "@/lib/use-api-resource";

function PortfolioRecordCard({ job }: { job: PaperJobResponse }) {
  const t = useTranslations("portfolioRecords.list");
  const common = useTranslations("common.states");
  const encodedJobId = encodeURIComponent(job.job_id);
  return (
    <li className="record-card portfolio-record-card">
      <div>
        <p className="record-card__meta">{job.job_id}</p>
        <h2>{job.run_id}</h2>
        <dl className="compact-definitions compact-definitions--jobs">
          <div><dt>{t("status")}</dt><dd><PaperJobStatusValue value={job.status} /></dd></div>
          <div><dt>{t("submitted")}</dt><dd><LocalizedTimestamp value={job.submitted_timestamp} /></dd></div>
          <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={job.updated_timestamp} /></dd></div>
          <div><dt>{t("attemptCount")}</dt><dd>{job.attempt_count}</dd></div>
          <div><dt>{t("latestAttempt")}</dt><dd>{job.latest_attempt ? `#${job.latest_attempt.attempt_number} ${job.latest_attempt.status}` : common("notAvailable")}</dd></div>
          <div><dt>{t("latestError")}</dt><dd><AttemptErrorValue code={job.latest_attempt?.error_code ?? null} /></dd></div>
          <div><dt>{t("resultAvailable")}</dt><dd>{job.result_available ? common("yes") : common("no")}</dd></div>
        </dl>
        {!job.result_available ? (
          <p className="neutral-note">{t("unavailable")}</p>
        ) : null}
      </div>
      <div className="record-card__actions">
        {job.result_available ? (
          <Link className="primary-link" href={`/portfolio-records/${encodedJobId}`}>
            {t("inspect", { runId: job.run_id })}
          </Link>
        ) : null}
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
          {t("openJob", { jobId: job.job_id })}
        </Link>
      </div>
    </li>
  );
}

export function PortfolioRecordListView() {
  const t = useTranslations("portfolioRecords.list");
  const [draftLimit, setDraftLimit] = useState<(typeof portfolioRecordLimits)[number]>(50);
  const [limit, setLimit] = useState<(typeof portfolioRecordLimits)[number]>(50);
  const request = useCallback(
    () => fetchPaperJobs({ status: "succeeded", limit }),
    [limit],
  );
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
        <div className="record-card__actions">
          <Link className="primary-link" href="/comparisons">{t("compare")}</Link>
          <Link className="text-link" href="/paper-jobs">{t("back")}</Link>
        </div>
      </header>

      <form
        className="filter-bar"
        aria-label={t("limitAria")}
        onSubmit={(event) => {
          event.preventDefault();
          setLimit(draftLimit);
        }}
      >
        <label>
          {t("limit")}
          <select
            value={draftLimit}
            onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof portfolioRecordLimits)[number])}
          >
            {portfolioRecordLimits.map((value) => <option key={value} value={value}>{value}</option>)}
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
          {state.data.map((job, index) => (
            <PortfolioRecordCard key={`${job.job_id}-${index}`} job={job} />
          ))}
        </ol>
      )}
    </div>
  );
}
