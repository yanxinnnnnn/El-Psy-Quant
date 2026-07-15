"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { fetchPaperJobs, type PaperJobResponse } from "@/lib/api-client";
import { attemptErrorDescription } from "@/lib/paper-jobs";
import {
  portfolioRecordErrorTitle,
  portfolioRecordLimits,
} from "@/lib/portfolio-records";
import { useApiResource } from "@/lib/use-api-resource";

function PortfolioRecordCard({ job }: { job: PaperJobResponse }) {
  const encodedJobId = encodeURIComponent(job.job_id);
  return (
    <li className="record-card portfolio-record-card">
      <div>
        <p className="record-card__meta">{job.job_id}</p>
        <h2>{job.run_id}</h2>
        <dl className="compact-definitions compact-definitions--jobs">
          <div><dt>Status</dt><dd><span className={`job-status job-status--${job.status}`}>{job.status}</span></dd></div>
          <div><dt>Submitted</dt><dd>{job.submitted_timestamp}</dd></div>
          <div><dt>Updated</dt><dd>{job.updated_timestamp}</dd></div>
          <div><dt>Attempt count</dt><dd>{job.attempt_count}</dd></div>
          <div><dt>Latest attempt</dt><dd>{job.latest_attempt ? `#${job.latest_attempt.attempt_number} ${job.latest_attempt.status}` : "Not available"}</dd></div>
          <div><dt>Latest error</dt><dd>{attemptErrorDescription(job.latest_attempt?.error_code ?? null)}</dd></div>
          <div><dt>Result available</dt><dd>{job.result_available ? "Yes" : "No"}</dd></div>
        </dl>
        {!job.result_available ? (
          <p className="neutral-note">This succeeded job has no backend-owned result available for inspection.</p>
        ) : null}
      </div>
      <div className="record-card__actions">
        {job.result_available ? (
          <Link className="primary-link" href={`/portfolio-records/${encodedJobId}`}>
            Inspect result for {job.run_id}
          </Link>
        ) : null}
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
          Open paper job {job.job_id}
        </Link>
      </div>
    </li>
  );
}

export function PortfolioRecordListView() {
  const [draftLimit, setDraftLimit] = useState<(typeof portfolioRecordLimits)[number]>(50);
  const [limit, setLimit] = useState<(typeof portfolioRecordLimits)[number]>(50);
  const request = useCallback(
    () => fetchPaperJobs({ status: "succeeded", limit }),
    [limit],
  );
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">Portfolio records · Succeeded paper results</p>
          <h1>Paper result availability</h1>
          <p>
            Browse succeeded durable jobs in exact API order and open only results
            the backend marks available.
          </p>
        </div>
        <Link className="text-link" href="/paper-jobs">Back to paper jobs</Link>
      </header>

      <form
        className="filter-bar"
        aria-label="Portfolio record limit"
        onSubmit={(event) => {
          event.preventDefault();
          setLimit(draftLimit);
        }}
      >
        <label>
          Limit
          <select
            value={draftLimit}
            onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof portfolioRecordLimits)[number])}
          >
            {portfolioRecordLimits.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <button className="secondary-button" type="submit">Apply limit</button>
        <button className="secondary-button" type="button" onClick={retry}>Refresh</button>
      </form>

      {state.status === "loading" ? (
        <LoadingState message="Loading succeeded paper jobs…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={portfolioRecordErrorTitle(state.code, true)}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.length === 0 ? (
        <EmptyState
          title="No succeeded paper jobs"
          message="The product database request succeeded and returned no succeeded jobs within the selected limit."
        />
      ) : (
        <ol className="card-list" aria-label="Succeeded paper jobs in exact API order">
          {state.data.map((job, index) => (
            <PortfolioRecordCard key={`${job.job_id}-${index}`} job={job} />
          ))}
        </ol>
      )}
    </div>
  );
}
