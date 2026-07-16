"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";

import { ErrorState, LoadingState, RequestId } from "@/components/data-states";
import {
  ApiClientError,
  cancelPaperJob,
  fetchPaperJobAttempts,
  fetchPaperJobDetail,
  recoverPaperJob,
  retryPaperJob,
  runPaperJob,
  type ApiResult,
  type PaperJobResponse,
} from "@/lib/api-client";
import {
  attemptErrorDescription,
  isExplicitUtcTimestamp,
  paperJobErrorGuidance,
  paperJobErrorTitle,
} from "@/lib/paper-jobs";
import { useApiResource } from "@/lib/use-api-resource";

type JobAction = "run" | "cancel" | "retry" | "recover";
type MutationState =
  | { status: "idle" }
  | { status: "confirming"; action: JobAction }
  | { status: "pending"; action: JobAction }
  | { status: "success"; action: JobAction; message: string; requestId: string | null }
  | { status: "error"; action: JobAction; title: string; message: string; requestId: string | null };

const actionLabels: Readonly<Record<JobAction, string>> = {
  run: "Run",
  cancel: "Cancel",
  retry: "Retry",
  recover: "Recover",
};

function allowedActions(status: PaperJobResponse["status"]): readonly JobAction[] {
  if (status === "queued") return ["run", "cancel"];
  if (status === "running") return ["recover"];
  if (status === "failed") return ["retry"];
  return [];
}

function actionSuccessMessage(action: JobAction, job: PaperJobResponse): string {
  if (action === "run") return "Execution was accepted, not completed. Use Refresh status manually to observe later state.";
  if (action === "retry") return "The failed job returned to queued. It has not run; use the separate Run action when ready.";
  if (action === "recover") return `Recovery inspection returned the current backend status: ${job.status}. No further action was chained.`;
  return "The queued job was canceled. Nothing was run.";
}

export function PaperJobDetailView({ jobId }: { jobId: string }) {
  const jobRequest = useCallback(() => fetchPaperJobDetail(jobId), [jobId]);
  const attemptsRequest = useCallback(() => fetchPaperJobAttempts(jobId), [jobId]);
  const jobResource = useApiResource(jobRequest);
  const attemptsResource = useApiResource(attemptsRequest);
  const [mutationJob, setMutationJob] = useState<PaperJobResponse | null>(null);
  const [mutation, setMutation] = useState<MutationState>({ status: "idle" });
  const [staleBefore, setStaleBefore] = useState("");
  const [recoveryFieldError, setRecoveryFieldError] = useState<string | null>(null);
  const [runRefreshRequired, setRunRefreshRequired] = useState(false);
  const [runRefreshSequence, setRunRefreshSequence] = useState<number | null>(null);
  const pendingRef = useRef(false);
  const runRefreshSatisfied = runRefreshRequired
    && runRefreshSequence !== null
    && jobResource.state.status === "success"
    && jobResource.state.sequence === runRefreshSequence;
  const runRefreshLocked = runRefreshRequired && !runRefreshSatisfied;
  const refreshedRunJob = runRefreshSatisfied && jobResource.state.status === "success"
    ? jobResource.state.data
    : null;
  const job = refreshedRunJob ?? mutationJob ?? (jobResource.state.status === "success" ? jobResource.state.data : null);

  function refresh() {
    if (runRefreshLocked) {
      setRunRefreshSequence(jobResource.retry());
    } else {
      setRunRefreshRequired(false);
      setRunRefreshSequence(null);
      setMutationJob(null);
      jobResource.retry();
    }
    setMutation({ status: "idle" });
    attemptsResource.retry();
  }

  function confirm(action: JobAction) {
    if (pendingRef.current || runRefreshLocked || mutation.status === "confirming" || mutation.status === "pending") {
      return;
    }
    setRecoveryFieldError(null);
    setMutation({ status: "confirming", action });
  }

  function execute(action: JobAction) {
    if (pendingRef.current || runRefreshLocked) return;
    if (action === "recover" && !isExplicitUtcTimestamp(staleBefore)) {
      setRecoveryFieldError("Enter a full UTC date and time ending in Z or +00:00.");
      return;
    }
    pendingRef.current = true;
    setMutation({ status: "pending", action });
    let request: Promise<ApiResult<PaperJobResponse>>;
    if (action === "run") request = runPaperJob(jobId);
    else if (action === "cancel") request = cancelPaperJob(jobId);
    else if (action === "retry") request = retryPaperJob(jobId);
    else request = recoverPaperJob(jobId, { stale_before: staleBefore });
    void request.then((result) => {
      setMutationJob(result.data);
      if (action === "run") {
        setRunRefreshRequired(true);
        setRunRefreshSequence(null);
      } else {
        setRunRefreshRequired(false);
        setRunRefreshSequence(null);
      }
      setMutation({ status: "success", action, message: actionSuccessMessage(action, result.data), requestId: result.requestId });
    }).catch((error: unknown) => {
      if (error instanceof ApiClientError) {
        setMutation({ status: "error", action, title: paperJobErrorTitle(error.code), message: paperJobErrorGuidance(error.code, error.publicMessage), requestId: error.requestId });
      } else {
        setMutation({ status: "error", action, title: "Paper job operation failed", message: "The local API is unavailable.", requestId: null });
      }
    }).finally(() => { pendingRef.current = false; });
  }

  const initialNotFound = job === null && jobResource.state.status === "error" && jobResource.state.code === "paper_job_not_found";

  return (
    <div className="business-workspace">
      <div className="back-links"><Link className="text-link" href="/paper-jobs">← Back to paper jobs</Link></div>
      {job === null && jobResource.state.status === "loading" ? (
        <LoadingState message="Loading the selected paper job…" />
      ) : job === null && jobResource.state.status === "error" ? (
        <ErrorState
          title={paperJobErrorTitle(jobResource.state.code)}
          message={jobResource.state.message}
          requestId={jobResource.state.requestId}
          onRetry={initialNotFound ? undefined : jobResource.retry}
          backHref="/paper-jobs"
          backLabel="Return to paper jobs"
        />
      ) : job ? (
        <article>
          <header className="page-heading page-heading--with-action page-heading--detail">
            <div>
              <p className="eyebrow">Paper job · Manual operational control</p>
              <h1>{job.run_id}</h1>
              <p className="identity-line">{job.job_id}</p>
            </div>
            <button className="secondary-button" type="button" onClick={refresh}>Refresh status</button>
          </header>

          <section className="content-panel" aria-labelledby="job-status-title">
            <div className="section-heading"><div><p className="eyebrow">{runRefreshLocked ? "Accepted Run response · Awaiting manual refresh" : "Last successful backend representation"}</p><h2 id="job-status-title">Job status</h2></div><span className={`job-status job-status--${job.status}`}>{job.status}</span></div>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>Job ID</dt><dd>{job.job_id}</dd></div>
              <div><dt>Run ID</dt><dd>{job.run_id}</dd></div>
              <div><dt>Status</dt><dd>{job.status}</dd></div>
              <div><dt>Submitted</dt><dd>{job.submitted_timestamp}</dd></div>
              <div><dt>Updated</dt><dd>{job.updated_timestamp}</dd></div>
              <div><dt>Attempt count</dt><dd>{job.attempt_count}</dd></div>
              <div><dt>Latest attempt</dt><dd>{job.latest_attempt ? `#${job.latest_attempt.attempt_number} ${job.latest_attempt.status}` : "Not available"}</dd></div>
              <div><dt>Latest attempt ID</dt><dd>{job.latest_attempt?.attempt_id ?? "Not available"}</dd></div>
              <div><dt>Latest attempt started</dt><dd>{job.latest_attempt?.started_timestamp ?? "Not available"}</dd></div>
              <div><dt>Latest attempt completed</dt><dd>{job.latest_attempt?.completed_timestamp ?? "Not available"}</dd></div>
              <div><dt>Latest attempt error</dt><dd>{attemptErrorDescription(job.latest_attempt?.error_code ?? null)}</dd></div>
              <div><dt>Result available</dt><dd>{job.result_available ? "Yes" : "No"}</dd></div>
              <div><dt>Detailed result inspection</dt><dd>{job.result_available ? <Link className="text-link" href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>Inspect portfolio record for {job.run_id}</Link> : "Not available"}</dd></div>
            </dl>
            {runRefreshLocked ? <p className="neutral-note" role="status"><strong>Displayed job state is stale.</strong> Refresh status is required before another action can be selected.</p> : null}
            <p className="neutral-note">Result inspection is offered only from the backend-owned availability flag. This page never follows the returned result URL or loads result contents automatically.</p>
          </section>

          <section className="content-panel" aria-labelledby="manual-controls-title">
            <p className="eyebrow">No automatic chaining or polling</p>
            <h2 id="manual-controls-title">Manual controls</h2>
            {runRefreshLocked ? (
              <p className="reference-empty">Run was accepted, not completed. Use Refresh status before selecting any mutation.</p>
            ) : mutation.status === "confirming" || mutation.status === "pending" ? null : allowedActions(job.status).length === 0 ? (
              <p className="reference-empty">No mutating control is available for a {job.status} job.</p>
            ) : (
              <div className="control-actions">{allowedActions(job.status).map((action) => <button className={action === "cancel" ? "danger-button" : "primary-button"} type="button" key={action} onClick={() => confirm(action)}>{actionLabels[action]}</button>)}</div>
            )}

            {(mutation.status === "confirming" || mutation.status === "pending") ? (
              <div className="confirmation-panel" role="group" aria-labelledby="confirmation-title">
                <p className="eyebrow">Explicit confirmation</p>
                <h3 id="confirmation-title">Confirm {actionLabels[mutation.action]} for {job.run_id}</h3>
                <p>Job {job.job_id}. This sends one command only.</p>
                {mutation.action === "run" ? <p>Accepted execution still requires manual refresh to observe claim or completion.</p> : null}
                {mutation.action === "retry" ? <p>Retry returns a failed job to queued and does not run it.</p> : null}
                {mutation.action === "recover" ? <div className="recovery-input"><label htmlFor="stale-before">Stale before (exact UTC)</label><input id="stale-before" value={staleBefore} onChange={(event) => setStaleBefore(event.target.value)} placeholder="2026-07-15T10:00:00Z" aria-describedby={recoveryFieldError ? "stale-before-guidance stale-before-error" : "stale-before-guidance"} aria-invalid={recoveryFieldError ? true : undefined} /><span className="field-guidance" id="stale-before-guidance">Supply the exact UTC threshold; the browser never generates one silently.</span>{recoveryFieldError ? <span className="field-error" id="stale-before-error">{recoveryFieldError}</span> : null}</div> : null}
                <div className="control-actions"><button className="primary-button" type="button" disabled={mutation.status === "pending"} onClick={() => execute(mutation.action)}>{mutation.status === "pending" ? `${actionLabels[mutation.action]} pending…` : `Confirm ${actionLabels[mutation.action]}`}</button><button className="secondary-button" type="button" disabled={mutation.status === "pending"} onClick={() => setMutation({ status: "idle" })}>Keep job unchanged</button></div>
              </div>
            ) : null}
            {mutation.status === "success" ? <div className="mutation-notice mutation-notice--success" role="status"><strong>{actionLabels[mutation.action]} response received</strong><p>{mutation.message}</p><RequestId value={mutation.requestId} /></div> : null}
            {mutation.status === "error" ? <div className="mutation-notice mutation-notice--error" role="alert"><strong>{mutation.title}</strong><p>{mutation.message}</p><RequestId value={mutation.requestId} /></div> : null}
          </section>

          <section className="content-panel" aria-labelledby="attempts-title">
            <div className="section-heading"><div><p className="eyebrow">Numbered operational audit</p><h2 id="attempts-title">Attempts</h2></div><p>Order and approved error codes come from the backend.</p></div>
            {attemptsResource.state.status === "loading" ? <div className="inline-loading" role="status" aria-busy="true">Loading attempts…</div> : attemptsResource.state.status === "error" ? <div className="mutation-notice mutation-notice--error" role="alert"><strong>{paperJobErrorTitle(attemptsResource.state.code)}</strong><p>{attemptsResource.state.message}</p><RequestId value={attemptsResource.state.requestId} /><button className="secondary-button" type="button" onClick={attemptsResource.retry}>Retry attempts</button></div> : attemptsResource.state.data.length === 0 ? <p className="reference-empty">The attempts request succeeded. No attempts exist for this job.</p> : <div className="table-scroll"><table className="attempts-table"><caption>Attempts in exact API order</caption><thead><tr><th>Attempt ID</th><th>Number</th><th>Status</th><th>Started</th><th>Completed</th><th>Error code</th></tr></thead><tbody>{attemptsResource.state.data.map((attempt) => <tr key={attempt.attempt_id}><th scope="row">{attempt.attempt_id}</th><td>{attempt.attempt_number}</td><td>{attempt.status}</td><td>{attempt.started_timestamp}</td><td>{attempt.completed_timestamp ?? "Not available"}</td><td>{attemptErrorDescription(attempt.error_code)}</td></tr>)}</tbody></table></div>}
          </section>
          <section className="related-panel" aria-labelledby="paper-comparison-next-title">
            <div><p className="eyebrow">Your next review choice</p><h2 id="paper-comparison-next-title">Compare available paper results</h2><p>Choose two to four backend-available results. No ranking or recommendation is produced.</p></div>
            <Link className="primary-link" href="/comparisons">Open comparison workspace</Link>
          </section>
        </article>
      ) : null}
    </div>
  );
}
