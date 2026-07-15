"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ComparisonResults,
  type ComparisonResultSlot,
} from "@/components/comparison-results";
import { EmptyState, ErrorState } from "@/components/data-states";
import {
  fetchPaperJobResult,
  fetchPaperJobs,
  type PaperJobResponse,
} from "@/lib/api-client";
import { attemptErrorDescription } from "@/lib/paper-jobs";
import {
  comparisonCandidateErrorTitle,
  comparisonCandidateLimits,
  comparisonFailure,
  comparisonHref,
  comparisonSelectionError,
} from "@/lib/comparisons";
import { useApiResource } from "@/lib/use-api-resource";

type ComparisonBatchState = Readonly<{
  key: string | null;
  slots: readonly ComparisonResultSlot[];
}>;

function idsFromKey(key: string): string[] {
  return JSON.parse(key) as string[];
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
  const encodedJobId = encodeURIComponent(job.job_id);
  const inputId = `comparison-candidate-${index}`;
  const disabled = !job.result_available || (selectionLimitReached && !selected);
  return (
    <li className="record-card comparison-candidate-card">
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
              ? `Result ${job.job_id} is unavailable and cannot be selected`
              : selectionLimitReached && !selected
                ? `Result ${job.job_id} cannot be selected because four results are already selected`
                : `Select result ${job.job_id}`}
          </label>
        </div>
        <p className="record-card__meta">{job.job_id}</p>
        <h2>{job.run_id}</h2>
        <dl className="compact-definitions compact-definitions--jobs">
          <div><dt>Status</dt><dd>{job.status}</dd></div>
          <div><dt>Submitted</dt><dd>{job.submitted_timestamp}</dd></div>
          <div><dt>Updated</dt><dd>{job.updated_timestamp}</dd></div>
          <div><dt>Attempt count</dt><dd>{job.attempt_count}</dd></div>
          <div><dt>Latest attempt number</dt><dd>{job.latest_attempt?.attempt_number ?? "Not available"}</dd></div>
          <div><dt>Latest attempt ID</dt><dd>{job.latest_attempt?.attempt_id ?? "Not available"}</dd></div>
          <div><dt>Latest attempt status</dt><dd>{job.latest_attempt?.status ?? "Not available"}</dd></div>
          <div><dt>Latest attempt started</dt><dd>{job.latest_attempt?.started_timestamp ?? "Not available"}</dd></div>
          <div><dt>Latest attempt completed</dt><dd>{job.latest_attempt?.completed_timestamp ?? "Not available"}</dd></div>
          <div><dt>Latest attempt error</dt><dd>{attemptErrorDescription(job.latest_attempt?.error_code ?? null)}</dd></div>
          <div><dt>Result available</dt><dd>{job.result_available ? "Yes" : "No"}</dd></div>
        </dl>
        {!job.result_available ? (
          <p className="neutral-note">This succeeded job remains visible, but the backend reports no result available for comparison.</p>
        ) : null}
      </div>
      <div className="record-card__actions">
        {job.result_available ? (
          <Link className="text-link" href={`/portfolio-records/${encodedJobId}`}>
            Open Portfolio Record {job.job_id}
          </Link>
        ) : null}
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
          Open Paper Job {job.job_id}
        </Link>
      </div>
    </li>
  );
}

export function ComparisonWorkspace({ jobIds }: { jobIds: readonly string[] }) {
  const router = useRouter();
  const [draftLimit, setDraftLimit] = useState<(typeof comparisonCandidateLimits)[number]>(50);
  const [limit, setLimit] = useState<(typeof comparisonCandidateLimits)[number]>(50);
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());
  const [selectionMessage, setSelectionMessage] = useState<string | null>(null);
  const queryKey = JSON.stringify(jobIds);
  const directValidation = comparisonSelectionError(jobIds);
  const comparisonValid = jobIds.length >= 2 && directValidation === null;

  const candidateRequest = useCallback(
    () => fetchPaperJobs({ status: "succeeded", limit }),
    [limit],
  );
  const candidates = useApiResource(candidateRequest);
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
      .filter((job) => job.result_available && selected.has(job.job_id))
      .map((job) => job.job_id);
    const validation = comparisonSelectionError(orderedSelection);
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
          <p className="eyebrow">Comparisons · S157</p>
          <h1>Paper run comparison workspace</h1>
          <p>
            Explicitly select two to four backend-available completed results, then inspect their authoritative facts side by side in selected order.
          </p>
        </div>
        <Link className="text-link" href="/portfolio-records">Browse Portfolio Records</Link>
      </header>

      {primaryLoading ? (
        <section className="state-panel comparison-primary-loading" role="status" aria-busy="true">
          <p className="eyebrow">Loading</p>
          <h2>Retrieving comparison workspace data</h2>
          <p>Loading candidates or selected authoritative results…</p>
        </section>
      ) : null}

      <section className="comparison-chooser" aria-labelledby="comparison-chooser-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Explicit selection</p>
            <h2 id="comparison-chooser-title">Succeeded paper jobs</h2>
          </div>
          <p className="selected-count" aria-live="polite">Selected {selected.size} of 4 maximum</p>
        </div>
        <form
          className="filter-bar"
          aria-label="Comparison candidate controls"
          onSubmit={(event) => {
            event.preventDefault();
            setLimit(draftLimit);
          }}
        >
          <label>
            Limit
            <select
              value={draftLimit}
              onChange={(event) => setDraftLimit(Number(event.target.value) as (typeof comparisonCandidateLimits)[number])}
            >
              {comparisonCandidateLimits.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          <button className="secondary-button" type="submit">Apply limit</button>
          <button className="secondary-button" type="button" onClick={candidates.retry}>Refresh candidates</button>
          <button className="primary-button" type="button" onClick={applySelection}>
            Compare selected results
          </button>
        </form>
        {selectionMessage ? <p className="form-error" role="alert">{selectionMessage}</p> : null}

        {candidates.state.status === "error" ? (
          <ErrorState
            title={comparisonCandidateErrorTitle(candidates.state.code)}
            message={candidates.state.message}
            requestId={candidates.state.requestId}
            onRetry={candidates.retry}
          />
        ) : candidates.state.status === "success" && candidates.state.data.length === 0 ? (
          <EmptyState
            title="No succeeded paper jobs"
            message="The product database request succeeded and returned no succeeded jobs within the selected limit."
          />
        ) : candidates.state.status === "success" ? (
          <ol className="card-list" aria-label="Succeeded comparison candidates in exact API order">
            {candidates.state.data.map((job, index) => (
              <CandidateCard
                key={`${job.job_id}-${index}`}
                job={job}
                index={index}
                selected={selected.has(job.job_id)}
                selectionLimitReached={selected.size >= 4}
                onSelectionChange={updateSelection}
              />
            ))}
          </ol>
        ) : null}
      </section>

      {jobIds.length > 0 && directValidation !== null ? (
        <section className="state-panel state-panel--error comparison-query-error" role="alert">
          <p className="eyebrow">Invalid comparison selection</p>
          <h2>Comparison selection is invalid</h2>
          <p>{directValidation}</p>
        </section>
      ) : null}

      {comparisonValid && comparison.batchState.key === queryKey ? (
        <ComparisonResults
          slots={comparisonSlots}
          onRetry={comparison.retry}
          onRefresh={comparison.refresh}
        />
      ) : null}
    </div>
  );
}
