"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import {
  fetchPaperJobs,
  type PaperJobResponse,
  type PaperJobStatus,
} from "@/lib/api-client";
import {
  attemptErrorDescription,
  paperJobErrorTitle,
  paperJobLimits,
  paperJobStatuses,
} from "@/lib/paper-jobs";
import { useApiResource } from "@/lib/use-api-resource";

function JobCard({ job }: { job: PaperJobResponse }) {
  return (
    <li className="record-card paper-job-card">
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
      </div>
      <Link
        className="primary-link"
        href={`/paper-jobs/${encodeURIComponent(job.job_id)}`}
      >
        Inspect job
      </Link>
    </li>
  );
}

export function PaperJobListView() {
  const [draftStatus, setDraftStatus] = useState<PaperJobStatus | "all">("all");
  const [draftLimit, setDraftLimit] = useState<(typeof paperJobLimits)[number]>(50);
  const [filters, setFilters] = useState<{
    status: PaperJobStatus | null;
    limit: (typeof paperJobLimits)[number];
  }>({ status: null, limit: 50 });
  const request = useCallback(() => fetchPaperJobs(filters), [filters]);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">Paper runs · Durable operational jobs</p>
          <h1>Paper job status</h1>
          <p>
            Browse backend-owned durable state in API order. Status changes appear only
            after an explicit command or manual refresh.
          </p>
        </div>
        <Link className="primary-link" href="/paper-jobs/new">
          Submit a queued job
        </Link>
      </header>

      <form
        className="filter-bar"
        aria-label="Paper job filters"
        onSubmit={(event) => {
          event.preventDefault();
          setFilters({
            status: draftStatus === "all" ? null : draftStatus,
            limit: draftLimit,
          });
        }}
      >
        <label>
          Status
          <select
            value={draftStatus}
            onChange={(event) => setDraftStatus(event.target.value as PaperJobStatus | "all")}
          >
            <option value="all">All statuses</option>
            {paperJobStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
        </label>
        <label>
          Limit
          <select
            value={draftLimit}
            onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof paperJobLimits)[number])}
          >
            {paperJobLimits.map((limit) => <option key={limit} value={limit}>{limit}</option>)}
          </select>
        </label>
        <button className="secondary-button" type="submit">Apply filters</button>
        <button className="secondary-button" type="button" onClick={retry}>Refresh</button>
      </form>

      {state.status === "loading" ? (
        <LoadingState message="Loading durable paper jobs…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={paperJobErrorTitle(state.code, true)}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.length === 0 ? (
        <EmptyState
          title="No paper jobs match this filter"
          message="The product database request succeeded and returned no durable jobs for the selected status."
        />
      ) : (
        <ol className="card-list" aria-label="Durable paper jobs">
          {state.data.map((job) => <JobCard key={job.job_id} job={job} />)}
        </ol>
      )}
    </div>
  );
}
