"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { ErrorState, LoadingState, RequestId } from "@/components/data-states";
import {
  AttemptErrorValue,
  PaperJobAttemptStatusValue,
  PaperJobAttemptSummary,
  PaperJobStatusValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import { useErrorPresentation } from "@/i18n/errors";
import {
  ApiClientError,
  cancelPaperJob,
  fetchPaperJobAttempts,
  fetchPaperJobDetail,
  recoverPaperJob,
  retryPaperJob,
  runPaperJob,
  type ApiResult,
  type PaperJobAttemptListResponse,
  type PaperJobResponse,
} from "@/lib/api-client";
import {
  isExplicitUtcTimestampAtOrAfter,
  paperJobActionsForStatus,
  reconcilePaperJobAttempts,
  type PaperJobAction,
} from "@/lib/paper-jobs";
import { useApiResource } from "@/lib/use-api-resource";

type MutationState =
  | { status: "idle" }
  | { status: "confirming"; action: PaperJobAction }
  | { status: "pending"; action: PaperJobAction }
  | { status: "success"; action: PaperJobAction; message: string; requestId: string | null }
  | { status: "error"; action: PaperJobAction; code: string; message: string; requestId: string | null };

type AttemptsOverride = {
  mutationAttempts: PaperJobAttemptListResponse;
  settledThroughSequence: number;
};

function actionClassName(action: PaperJobAction): string {
  if (action === "cancel") return "danger-button";
  if (action === "recover") return "warning-button";
  if (action === "retry") return "secondary-button";
  return "primary-button";
}

function MutationErrorNotice({ code, message, requestId }: { code: string; message: string; requestId: string | null }) {
  const error = useErrorPresentation(code);
  const common = useTranslations("common");
  return <div className="mutation-notice mutation-notice--error" role="alert"><strong>{error.title}</strong><p>{error.explanation}</p><p>{message}</p><p>{error.recovery}</p><p className="request-id">{common("errorCode", { code })}</p><RequestId value={requestId} /></div>;
}

export function PaperJobDetailView({ jobId }: { jobId: string }) {
  const t = useTranslations("paperJobs.detail");
  const common = useTranslations("common.states");
  const actionLabel = (action: PaperJobAction) => action === "run" ? t("run") : action === "cancel" ? t("cancel") : action === "retry" ? t("retry") : t("recover");
  const successMessage = (
    action: PaperJobAction,
    nextJob: PaperJobResponse,
    recoveryOutcome: "requeued" | "succeeded" | "failed" | null,
  ) => action === "run"
    ? t("runSuccess", {
        attemptId: nextJob.latest_attempt?.attempt_id ?? common("notAvailable"),
        attemptNumber: nextJob.latest_attempt?.attempt_number ?? common("notAvailable"),
      })
    : action === "retry"
      ? t("retrySuccess")
      : action === "recover"
        ? t("recoverSuccess", {
            outcome: recoveryOutcome ?? common("notAvailable"),
            status: nextJob.status,
          })
        : t("cancelSuccess");
  const jobRequest = useCallback(() => fetchPaperJobDetail(jobId), [jobId]);
  const attemptsRequest = useCallback(() => fetchPaperJobAttempts(jobId), [jobId]);
  const jobResource = useApiResource(jobRequest);
  const attemptsResource = useApiResource(attemptsRequest);
  const jobError = useErrorPresentation(jobResource.state.status === "error" ? jobResource.state.code : null);
  const [mutationJob, setMutationJob] = useState<PaperJobResponse | null>(null);
  const [mutation, setMutation] = useState<MutationState>({ status: "idle" });
  const [staleBefore, setStaleBefore] = useState("");
  const [recoveryFieldError, setRecoveryFieldError] = useState<string | null>(null);
  const [runRefreshRequired, setRunRefreshRequired] = useState(false);
  const [runRefreshSequence, setRunRefreshSequence] = useState<number | null>(null);
  const [attemptsOverride, setAttemptsOverride] = useState<AttemptsOverride | null>(null);
  const pendingRef = useRef(false);
  const attemptsStateRef = useRef(attemptsResource.state);
  useEffect(() => {
    attemptsStateRef.current = attemptsResource.state;
  }, [attemptsResource.state]);
  const runRefreshSatisfied = runRefreshRequired
    && runRefreshSequence !== null
    && jobResource.state.status === "success"
    && jobResource.state.sequence === runRefreshSequence;
  const runRefreshLocked = runRefreshRequired && !runRefreshSatisfied;
  const refreshedRunJob = runRefreshSatisfied && jobResource.state.status === "success"
    ? jobResource.state.data
    : null;
  const job = refreshedRunJob ?? mutationJob ?? (jobResource.state.status === "success" ? jobResource.state.data : null);
  const resourceAttempts = attemptsResource.state.status === "success"
    ? attemptsResource.state.data
    : attemptsResource.state.status === "loading"
      && attemptsResource.state.previous?.status === "success"
      ? attemptsResource.state.previous.data
      : null;
  const attemptsOverrideSuperseded = attemptsOverride !== null
    && attemptsResource.state.status === "success"
    && attemptsResource.state.sequence > attemptsOverride.settledThroughSequence;
  const visibleAttempts = attemptsOverride !== null && !attemptsOverrideSuperseded
    ? reconcilePaperJobAttempts(
        resourceAttempts ?? [],
        attemptsOverride.mutationAttempts,
      )
    : resourceAttempts;

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

  function confirm(action: PaperJobAction) {
    if (pendingRef.current || runRefreshLocked || mutation.status === "confirming" || mutation.status === "pending") {
      return;
    }
    setRecoveryFieldError(null);
    setMutation({ status: "confirming", action });
  }

  function execute(action: PaperJobAction) {
    if (pendingRef.current || runRefreshLocked || job === null) return;
    if (
      action === "recover" &&
      !isExplicitUtcTimestampAtOrAfter(staleBefore, job.updated_timestamp)
    ) {
      setRecoveryFieldError(t("staleError", { updated: job.updated_timestamp }));
      return;
    }
    pendingRef.current = true;
    setMutation({ status: "pending", action });
    let request: Promise<{
      job: PaperJobResponse;
      recoveryOutcome: "requeued" | "succeeded" | "failed" | null;
      requestId: string | null;
    }>;
    if (action === "recover") {
      request = recoverPaperJob(jobId, { stale_before: staleBefore }).then(
        (result) => ({
          job: result.data.job,
          recoveryOutcome: result.data.recovery_outcome,
          requestId: result.requestId,
        }),
      );
    } else {
      let mutationRequest: Promise<ApiResult<PaperJobResponse>>;
      if (action === "run") mutationRequest = runPaperJob(jobId);
      else if (action === "cancel") mutationRequest = cancelPaperJob(jobId);
      else mutationRequest = retryPaperJob(jobId);
      request = mutationRequest.then((result) => ({
        job: result.data,
        recoveryOutcome: null,
        requestId: result.requestId,
      }));
    }
    void request.then((result) => {
      setMutationJob(result.job);
      if (action === "run" || action === "recover") {
        const attemptsState = attemptsStateRef.current;
        setAttemptsOverride((current) => {
          const currentIsSuperseded = current !== null
            && attemptsState.status === "success"
            && attemptsState.sequence > current.settledThroughSequence;
          const latestAttempt = result.job.latest_attempt;
          return {
            mutationAttempts: reconcilePaperJobAttempts(
              current !== null && !currentIsSuperseded
                ? current.mutationAttempts
                : [],
              latestAttempt === null ? [] : [latestAttempt],
            ),
            settledThroughSequence: attemptsState.sequence,
          };
        });
      }
      if (action === "run") {
        setRunRefreshRequired(true);
        setRunRefreshSequence(null);
      } else {
        setRunRefreshRequired(false);
        setRunRefreshSequence(null);
      }
      setMutation({
        status: "success",
        action,
        message: successMessage(action, result.job, result.recoveryOutcome),
        requestId: result.requestId,
      });
    }).catch((error: unknown) => {
      if (error instanceof ApiClientError) {
        setMutation({ status: "error", action, code: error.code, message: error.publicMessage, requestId: error.requestId });
      } else {
        setMutation({ status: "error", action, code: "api_unavailable", message: "The local API is unavailable.", requestId: null });
      }
    }).finally(() => { pendingRef.current = false; });
  }

  const initialNotFound = job === null && jobResource.state.status === "error" && jobResource.state.code === "paper_job_not_found";

  return (
    <div className="business-workspace">
      <div className="back-links"><Link className="text-link" href="/paper-jobs">{t("back")}</Link></div>
      {job === null && jobResource.state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : job === null && jobResource.state.status === "error" ? (
        <ErrorState
          code={jobResource.state.code}
          title={jobError.useContextTitle ? t("unavailableTitle") : jobError.title}
          message={jobResource.state.message}
          requestId={jobResource.state.requestId}
          onRetry={initialNotFound ? undefined : jobResource.retry}
          backHref="/paper-jobs"
          backLabel={t("return")}
        />
      ) : job ? (
        <article>
          <header className="page-heading page-heading--with-action page-heading--detail">
            <div>
              <p className="eyebrow">{t("eyebrow")}</p>
              <h1>{job.run_id}</h1>
              <p className="identity-line">{job.job_id}</p>
            </div>
            <button className="secondary-button" type="button" onClick={refresh}>{t("refresh")}</button>
          </header>

          <section className="content-panel" aria-labelledby="job-status-title">
            <div className="section-heading"><div><p className="eyebrow">{runRefreshLocked ? t("acceptedEyebrow") : t("representationEyebrow")}</p><h2 id="job-status-title">{t("statusTitle")}</h2></div><PaperJobStatusValue value={job.status} /></div>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>{t("jobId")}</dt><dd>{job.job_id}</dd></div>
              <div><dt>{t("runId")}</dt><dd>{job.run_id}</dd></div>
              <div><dt>{t("status")}</dt><dd><PaperJobStatusValue value={job.status} /></dd></div>
              <div><dt>{t("submitted")}</dt><dd><LocalizedTimestamp value={job.submitted_timestamp} /></dd></div>
              <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={job.updated_timestamp} /></dd></div>
              <div><dt>{t("attemptCount")}</dt><dd>{job.attempt_count}</dd></div>
              <div><dt>{t("latestAttempt")}</dt><dd>{job.latest_attempt ? <PaperJobAttemptSummary attemptNumber={job.latest_attempt.attempt_number} status={job.latest_attempt.status} /> : common("notAvailable")}</dd></div>
              <div><dt>{t("latestAttemptId")}</dt><dd>{job.latest_attempt?.attempt_id ?? common("notAvailable")}</dd></div>
              <div><dt>{t("latestStarted")}</dt><dd>{job.latest_attempt?.started_timestamp ? <LocalizedTimestamp value={job.latest_attempt.started_timestamp} /> : common("notAvailable")}</dd></div>
              <div><dt>{t("latestCompleted")}</dt><dd>{job.latest_attempt?.completed_timestamp ? <LocalizedTimestamp value={job.latest_attempt.completed_timestamp} /> : common("notAvailable")}</dd></div>
              <div><dt>{t("latestError")}</dt><dd><AttemptErrorValue code={job.latest_attempt?.error_code ?? null} /></dd></div>
              <div><dt>{t("resultAvailable")}</dt><dd>{job.result_available ? common("yes") : common("no")}</dd></div>
              <div><dt>{t("resultInspection")}</dt><dd>{job.result_available ? <Link className="text-link" href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>{t("inspectPortfolio", { runId: job.run_id })}</Link> : common("notAvailable")}</dd></div>
            </dl>
            {runRefreshLocked ? <p className="neutral-note" role="status"><strong>{t("staleTitle")}</strong> {t("staleDescription")}</p> : null}
            <p className="neutral-note">{t("resultBoundary")}</p>
          </section>

          <section className="content-panel" aria-labelledby="manual-controls-title">
            <p className="eyebrow">{t("controlsEyebrow")}</p>
            <h2 id="manual-controls-title">{t("controlsTitle")}</h2>
            {runRefreshLocked ? (
              <p className="reference-empty">{t("acceptedDescription")}</p>
            ) : mutation.status === "confirming" || mutation.status === "pending" ? null : paperJobActionsForStatus(job.status).length === 0 ? (
              <p className="reference-empty">{t("noControl", { status: job.status })}</p>
            ) : (
              <div className="control-actions">{paperJobActionsForStatus(job.status).map((action) => <button className={actionClassName(action)} type="button" key={action} onClick={() => confirm(action)}>{actionLabel(action)}</button>)}</div>
            )}

            {(mutation.status === "confirming" || mutation.status === "pending") ? (
              <div className="confirmation-panel" role="group" aria-labelledby="confirmation-title" aria-busy={mutation.status === "pending"}>
                <p className="eyebrow">{t("confirmationEyebrow")}</p>
                <h3 id="confirmation-title">{t("confirmTitle", { action: actionLabel(mutation.action), runId: job.run_id })}</h3>
                <p>{t("oneCommand", { jobId: job.job_id })}</p>
                {mutation.action === "run" ? <p>{t("runConfirmation")}</p> : null}
                {mutation.action === "retry" ? <p>{t("retryConfirmation")}</p> : null}
                {mutation.action === "recover" ? <div className="recovery-input"><p>{t("loadedUpdated")} <code>{job.updated_timestamp}</code></p><label htmlFor="stale-before">{t("staleBefore")}</label><input id="stale-before" value={staleBefore} onChange={(event) => { setStaleBefore(event.target.value); setRecoveryFieldError(null); }} placeholder="2026-07-15T10:00:00Z" aria-describedby={recoveryFieldError ? "stale-before-guidance stale-before-error" : "stale-before-guidance"} aria-invalid={recoveryFieldError ? true : undefined} /><span className="field-guidance" id="stale-before-guidance">{t("staleGuidance")}</span>{recoveryFieldError ? <span className="field-error" id="stale-before-error">{recoveryFieldError}</span> : null}</div> : null}
                <div className="control-actions"><button className={actionClassName(mutation.action)} type="button" disabled={mutation.status === "pending"} onClick={() => execute(mutation.action)}>{mutation.status === "pending" ? t("pending", { action: actionLabel(mutation.action) }) : t("confirm", { action: actionLabel(mutation.action) })}</button><button className="quiet-button" type="button" disabled={mutation.status === "pending"} onClick={() => setMutation({ status: "idle" })}>{t("keep")}</button></div>
              </div>
            ) : null}
            {mutation.status === "success" ? <div className="mutation-notice mutation-notice--success" role="status"><strong>{t("response", { action: actionLabel(mutation.action) })}</strong><p>{mutation.message}</p><RequestId value={mutation.requestId} /></div> : null}
            {mutation.status === "error" ? <MutationErrorNotice code={mutation.code} message={mutation.message} requestId={mutation.requestId} /> : null}
          </section>

          <section className="content-panel" aria-labelledby="attempts-title">
            <div className="section-heading"><div><p className="eyebrow">{t("attemptsEyebrow")}</p><h2 id="attempts-title">{t("attemptsTitle")}</h2></div><p>{t("attemptsBoundary")}</p></div>
            {attemptsResource.state.status === "loading" && visibleAttempts === null ? <div className="inline-loading" role="status" aria-busy="true">{t("loadingAttempts")}</div> : null}
            {attemptsResource.state.status === "error" ? <MutationErrorNotice code={attemptsResource.state.code} message={attemptsResource.state.message} requestId={attemptsResource.state.requestId} /> : null}
            {visibleAttempts?.length === 0 ? <p className="reference-empty">{t("emptyAttempts")}</p> : visibleAttempts ? <ScrollableTable caption={t("attemptsCaption")} tableClassName="attempts-table"><thead><tr><th scope="col">{t("attemptId")}</th><th scope="col">{t("number")}</th><th scope="col">{t("status")}</th><th scope="col">{t("started")}</th><th scope="col">{t("completed")}</th><th scope="col">{t("errorCode")}</th></tr></thead><tbody>{visibleAttempts.map((attempt) => <tr key={attempt.attempt_id}><th scope="row">{attempt.attempt_id}</th><td>{attempt.attempt_number}</td><td><PaperJobAttemptStatusValue value={attempt.status} /></td><td><LocalizedTimestamp value={attempt.started_timestamp} /></td><td>{attempt.completed_timestamp ? <LocalizedTimestamp value={attempt.completed_timestamp} /> : common("notAvailable")}</td><td><AttemptErrorValue code={attempt.error_code} /></td></tr>)}</tbody></ScrollableTable> : null}
          </section>
          <section className="related-panel" aria-labelledby="paper-comparison-next-title">
            <div><p className="eyebrow">{t("relatedEyebrow")}</p><h2 id="paper-comparison-next-title">{t("relatedTitle")}</h2><p>{t("relatedDescription")}</p></div>
            <Link className="primary-link" href="/comparisons">{t("openComparison")}</Link>
          </section>
        </article>
      ) : null}
    </div>
  );
}
