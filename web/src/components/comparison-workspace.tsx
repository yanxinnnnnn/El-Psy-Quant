"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ComparisonResults,
  type ComparisonResultSlot,
} from "@/components/comparison-results";
import { EmptyState, ErrorState } from "@/components/data-states";
import { AttemptErrorValue, PaperJobStatusValue } from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { useErrorPresentation } from "@/i18n/errors";
import {
  fetchPaperJobResult,
  fetchPaperJobs,
  type PaperJobResponse,
} from "@/lib/api-client";
import {
  comparisonCandidateLimits,
  comparisonFailure,
  comparisonHref,
  comparisonSelectionErrorKey,
  type ComparisonSelectionErrorKey,
} from "@/lib/comparisons";
import { useApiResource } from "@/lib/use-api-resource";

type ComparisonBatchState = Readonly<{
  key: string | null;
  slots: readonly ComparisonResultSlot[];
}>;

function idsFromKey(key: string): string[] {
  return JSON.parse(key) as string[];
}

function reconcileSelection(
  current: ReadonlySet<string>,
  candidates: readonly PaperJobResponse[],
): ReadonlySet<string> {
  const selectableIds = new Set(
    candidates
      .filter((candidate) => candidate.result_available)
      .map((candidate) => candidate.job_id),
  );
  const reconciled = new Set(
    [...current].filter((jobId) => selectableIds.has(jobId)),
  );
  return reconciled.size === current.size ? current : reconciled;
}

function useComparisonResults(queryKey: string, valid: boolean) {
  const [batchState, setBatchState] = useState<ComparisonBatchState>({
    key: null,
    slots: [],
  });
  const batchSequence = useRef(0);
  const slotSequences = useRef<number[]>([]);

  const requestSlot = useCallback(
    (jobId: string, index: number, batch: number, slotSequence: number) => {
      void fetchPaperJobResult(jobId)
        .then((response) => {
          if (
            batch !== batchSequence.current ||
            slotSequence !== slotSequences.current[index]
          ) {
            return;
          }
          setBatchState((current) => {
            if (current.key !== queryKey) {
              return current;
            }
            const slots = [...current.slots];
            slots[index] = {
              jobId,
              status: "success",
              result: response.data,
              requestId: response.requestId,
            };
            return { ...current, slots };
          });
        })
        .catch((error: unknown) => {
          if (
            batch !== batchSequence.current ||
            slotSequence !== slotSequences.current[index]
          ) {
            return;
          }
          setBatchState((current) => {
            if (current.key !== queryKey) {
              return current;
            }
            const slots = [...current.slots];
            slots[index] = {
              jobId,
              status: "error",
              error: comparisonFailure(error),
            };
            return { ...current, slots };
          });
        });
    },
    [queryKey],
  );

  const refresh = useCallback(() => {
    if (!valid) {
      batchSequence.current += 1;
      setBatchState({ key: queryKey, slots: [] });
      return;
    }
    const jobIds = idsFromKey(queryKey);
    const batch = ++batchSequence.current;
    slotSequences.current = jobIds.map(() => 1);
    setBatchState({
      key: queryKey,
      slots: jobIds.map((jobId) => ({ jobId, status: "loading" })),
    });
    jobIds.forEach((jobId, index) => requestSlot(jobId, index, batch, 1));
  }, [queryKey, requestSlot, valid]);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) {
        refresh();
      }
    });
    return () => {
      active = false;
      batchSequence.current += 1;
    };
  }, [refresh]);

  const retry = useCallback(
    (index: number) => {
      if (!valid || batchState.key !== queryKey) {
        return;
      }
      const jobIds = idsFromKey(queryKey);
      const jobId = jobIds[index];
      if (jobId === undefined) {
        return;
      }
      const batch = batchSequence.current;
      const slotSequence = (slotSequences.current[index] ?? 0) + 1;
      slotSequences.current[index] = slotSequence;
      setBatchState((current) => {
        const slots = [...current.slots];
        slots[index] = { jobId, status: "loading" };
        return { ...current, slots };
      });
      requestSlot(jobId, index, batch, slotSequence);
    },
    [batchState.key, queryKey, requestSlot, valid],
  );

  return { batchState, refresh, retry };
}

function CandidateCard({
  job,
  index,
  selected,
  selectionLimitReached,
  onSelectionChange,
}: {
  job: PaperJobResponse;
  index: number;
  selected: boolean;
  selectionLimitReached: boolean;
  onSelectionChange: (jobId: string, checked: boolean) => void;
}) {
  const t = useTranslations("comparisons.workspace");
  const common = useTranslations("common.states");
  const encodedJobId = encodeURIComponent(job.job_id);
  const inputId = `comparison-candidate-${index}`;
  const disabled = !job.result_available || (selectionLimitReached && !selected);
  return (
    <li className="record-card">
      <div>
        <div className="comparison-candidate-select">
          <input
            id={inputId}
            type="checkbox"
            checked={selected}
            disabled={disabled}
            onChange={(event) => onSelectionChange(job.job_id, event.target.checked)}
          />
          <label htmlFor={inputId}>
            {!job.result_available
              ? t("unavailableSelection", { jobId: job.job_id })
              : selectionLimitReached && !selected
                ? t("limitSelection", { jobId: job.job_id })
                : t("select", { jobId: job.job_id })}
          </label>
        </div>
        <p className="record-card__meta">{job.job_id}</p>
        <h2>{job.run_id}</h2>
        <dl className="compact-definitions compact-definitions--jobs">
          <div><dt>{t("status")}</dt><dd><PaperJobStatusValue value={job.status} /></dd></div>
          <div><dt>{t("submitted")}</dt><dd><LocalizedTimestamp value={job.submitted_timestamp} /></dd></div>
          <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={job.updated_timestamp} /></dd></div>
          <div><dt>{t("attemptCount")}</dt><dd>{job.attempt_count}</dd></div>
          <div><dt>{t("latestAttemptNumber")}</dt><dd>{job.latest_attempt?.attempt_number ?? common("notAvailable")}</dd></div>
          <div><dt>{t("latestAttemptId")}</dt><dd>{job.latest_attempt?.attempt_id ?? common("notAvailable")}</dd></div>
          <div><dt>{t("latestAttemptStatus")}</dt><dd>{job.latest_attempt?.status ?? common("notAvailable")}</dd></div>
          <div><dt>{t("latestStarted")}</dt><dd>{job.latest_attempt?.started_timestamp ? <LocalizedTimestamp value={job.latest_attempt.started_timestamp} /> : common("notAvailable")}</dd></div>
          <div><dt>{t("latestCompleted")}</dt><dd>{job.latest_attempt?.completed_timestamp ? <LocalizedTimestamp value={job.latest_attempt.completed_timestamp} /> : common("notAvailable")}</dd></div>
          <div><dt>{t("latestError")}</dt><dd><AttemptErrorValue code={job.latest_attempt?.error_code ?? null} /></dd></div>
          <div><dt>{t("resultAvailable")}</dt><dd>{job.result_available ? common("yes") : common("no")}</dd></div>
        </dl>
        {!job.result_available ? (
          <p className="neutral-note">{t("unavailableResult")}</p>
        ) : null}
      </div>
      <div className="record-card__actions">
        {job.result_available ? (
          <Link className="text-link" href={`/portfolio-records/${encodedJobId}`}>
            {t("openPortfolio", { jobId: job.job_id })}
          </Link>
        ) : null}
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
          {t("openJob", { jobId: job.job_id })}
        </Link>
      </div>
    </li>
  );
}

export function ComparisonWorkspace({ jobIds }: { jobIds: readonly string[] }) {
  const t = useTranslations("comparisons.workspace");
  const selectionErrors = useTranslations("comparisons.selectionErrors");
  const router = useRouter();
  const [draftLimit, setDraftLimit] = useState<(typeof comparisonCandidateLimits)[number]>(50);
  const [limit, setLimit] = useState<(typeof comparisonCandidateLimits)[number]>(50);
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [selectionMessage, setSelectionMessage] = useState<ComparisonSelectionErrorKey | null>(null);
  const queryKey = JSON.stringify(jobIds);
  const directValidation = comparisonSelectionErrorKey(jobIds);
  const comparisonValid = jobIds.length >= 2 && directValidation === null;

  const candidateRequest = useCallback(
    () => fetchPaperJobs({ status: "succeeded", limit }),
    [limit],
  );
  const candidates = useApiResource(candidateRequest);
  const candidateError = useErrorPresentation(candidates.state.status === "error" ? candidates.state.code : null);

  useEffect(() => {
    if (candidates.state.status !== "success") {
      return;
    }
    let active = true;
    const latestCandidates = candidates.state.data;
    queueMicrotask(() => {
      if (!active) {
        return;
      }
      setSelected((current) => reconcileSelection(current, latestCandidates));
    });
    return () => {
      active = false;
    };
  }, [candidates.state]);

  const representedSelection =
    candidates.state.status === "success"
      ? reconcileSelection(selected, candidates.state.data)
      : selected;

  const comparison = useComparisonResults(queryKey, comparisonValid);
  const comparisonSlots =
    comparison.batchState.key === queryKey ? comparison.batchState.slots : [];
  const comparisonLoading =
    comparisonValid &&
    (comparison.batchState.key !== queryKey ||
      comparisonSlots.some((slot) => slot.status === "loading"));
  const primaryLoading = candidates.state.status === "loading" || comparisonLoading;

  const updateSelection = (jobId: string, checked: boolean) => {
    setSelectionMessage(null);
    setSelected((current) => {
      const next = new Set(current);
      if (checked) {
        next.add(jobId);
      } else {
        next.delete(jobId);
      }
      return next;
    });
  };

  const applySelection = () => {
    if (candidates.state.status !== "success") {
      return;
    }
    const orderedSelection = candidates.state.data
      .filter((job) => job.result_available && representedSelection.has(job.job_id))
      .map((job) => job.job_id);
    const validation = comparisonSelectionErrorKey(orderedSelection);
    if (validation !== null) {
      setSelectionMessage(validation);
      return;
    }
    setSelectionMessage(null);
    router.push(comparisonHref(orderedSelection));
  };

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <Link className="text-link" href="/portfolio-records">{t("browse")}</Link>
      </header>

      {primaryLoading ? (
        <section className="state-panel comparison-primary-loading" role="status" aria-busy="true">
          <p className="eyebrow">{t("loadingEyebrow")}</p>
          <h2>{t("loadingTitle")}</h2>
          <p>{t("loadingMessage")}</p>
        </section>
      ) : null}

      <section className="comparison-chooser" aria-labelledby="comparison-chooser-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t("chooserEyebrow")}</p>
            <h2 id="comparison-chooser-title">{t("chooserTitle")}</h2>
          </div>
          <p className="selected-count" aria-live="polite">{t("selectedCount", { count: representedSelection.size })}</p>
        </div>
        <form
          className="filter-bar"
          aria-label={t("controlsAria")}
          onSubmit={(event) => {
            event.preventDefault();
            setLimit(draftLimit);
          }}
        >
          <label>
            {t("limit")}
            <select
              value={draftLimit}
              onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof comparisonCandidateLimits)[number])}
            >
              {comparisonCandidateLimits.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          <button className="secondary-button" type="submit">{t("apply")}</button>
          <button className="secondary-button" type="button" onClick={candidates.retry}>{t("refreshCandidates")}</button>
          <button className="primary-button" type="button" onClick={applySelection}>
            {t("compare")}
          </button>
        </form>
        {selectionMessage ? <p className="form-error" role="alert">{selectionErrors(selectionMessage)}</p> : null}

        {candidates.state.status === "error" ? (
          <ErrorState
            code={candidates.state.code}
            title={candidateError.useContextTitle ? t("candidateUnavailableTitle") : candidateError.title}
            message={candidates.state.message}
            requestId={candidates.state.requestId}
            onRetry={candidates.retry}
          />
        ) : candidates.state.status === "success" && candidates.state.data.length === 0 ? (
          <EmptyState
            title={t("emptyTitle")}
            message={t("emptyMessage")}
          />
        ) : candidates.state.status === "success" ? (
          <ol className="card-list" aria-label={t("candidatesAria")}>
            {candidates.state.data.map((job, index) => (
              <CandidateCard
                key={`${job.job_id}-${index}`}
                job={job}
                index={index}
                selected={representedSelection.has(job.job_id)}
                selectionLimitReached={representedSelection.size >= 4}
                onSelectionChange={updateSelection}
              />
            ))}
          </ol>
        ) : null}
      </section>

      {jobIds.length > 0 && directValidation !== null ? (
        <section className="state-panel state-panel--error comparison-query-error" role="alert">
          <p className="eyebrow">{t("invalidEyebrow")}</p>
          <h2>{t("invalidTitle")}</h2>
          <p>{selectionErrors(directValidation)}</p>
        </section>
      ) : null}

      {comparisonValid && comparison.batchState.key === queryKey ? (
        <ComparisonResults
          slots={comparisonSlots}
          onRetry={comparison.retry}
          onRefresh={comparison.refresh}
        />
      ) : null}

      <section className="related-panel" aria-labelledby="comparison-lifecycle-next-title">
        <div><p className="eyebrow">{t("relatedEyebrow")}</p><h2 id="comparison-lifecycle-next-title">{t("relatedTitle")}</h2><p>{t("relatedDescription")}</p></div>
        <Link className="primary-link" href="/lifecycle-review">{t("openLifecycle")}</Link>
      </section>
    </div>
  );
}
