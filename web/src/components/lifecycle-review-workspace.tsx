"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { RequestId } from "@/components/data-states";
import {
  LifecycleTimeline,
  ProposalInspection,
  ReviewInspection,
  SnapshotInspection,
} from "@/components/lifecycle-review-inspection";
import {
  ApiClientError,
  fetchDemoWorkspace,
  submitLifecycleTransitionProposal,
  submitLifecycleTransitionReview,
  type ApiResult,
  type DemoWorkspaceDescriptorResponse,
  type LifecycleTransitionProposalRequest,
  type LifecycleTransitionProposalResponse,
  type LifecycleTransitionReviewRequest,
  type LifecycleTransitionReviewResponse,
} from "@/lib/api-client";
import {
  lifecycleCommandErrorTitle,
  proposalResponseToRequest,
} from "@/lib/lifecycle-review";

type StringRow = { key: number; value: string };
type EvidenceRow = {
  key: number;
  referenceType: string;
  referenceId: string;
  label: string;
  description: string;
};
type SnapshotDraft = {
  snapshotId: string;
  strategyId: string;
  lifecycleState: string;
  rationale: string;
  declaredBy: string;
  declaredTimestamp: string;
  notes: StringRow[];
  warnings: StringRow[];
};
type ProposalDraft = {
  proposalId: string;
  sourceSnapshot: SnapshotDraft;
  targetState: string;
  rationale: string;
  evidenceReferences: EvidenceRow[];
  requestedBy: string;
  requestedTimestamp: string;
  notes: StringRow[];
  warnings: StringRow[];
};
type ReviewDraft = {
  transitionRecordId: string;
  reviewOutcome: string;
  rationale: string;
  reviewedBy: string;
  reviewedTimestamp: string;
  notes: StringRow[];
  warnings: StringRow[];
  includeResultingSnapshot: boolean;
  resultingSnapshot: SnapshotDraft;
};
type CommandFailure = {
  title: string;
  message: string;
  requestId: string | null;
};

const blankSnapshot = (): SnapshotDraft => ({
  snapshotId: "",
  strategyId: "",
  lifecycleState: "",
  rationale: "",
  declaredBy: "",
  declaredTimestamp: "",
  notes: [],
  warnings: [],
});

const blankProposal = (): ProposalDraft => ({
  proposalId: "",
  sourceSnapshot: blankSnapshot(),
  targetState: "",
  rationale: "",
  evidenceReferences: [],
  requestedBy: "",
  requestedTimestamp: "",
  notes: [],
  warnings: [],
});

const blankReview = (): ReviewDraft => ({
  transitionRecordId: "",
  reviewOutcome: "",
  rationale: "",
  reviewedBy: "",
  reviewedTimestamp: "",
  notes: [],
  warnings: [],
  includeResultingSnapshot: false,
  resultingSnapshot: blankSnapshot(),
});

function snapshotDraftFromRequest(
  snapshot: LifecycleTransitionProposalRequest["source_snapshot"],
  nextKey: () => number,
): SnapshotDraft {
  return {
    snapshotId: snapshot.snapshot_id,
    strategyId: snapshot.strategy_id,
    lifecycleState: snapshot.lifecycle_state,
    rationale: snapshot.rationale,
    declaredBy: snapshot.declared_by ?? "",
    declaredTimestamp: snapshot.declared_timestamp ?? "",
    notes: snapshot.notes.map((value) => ({ key: nextKey(), value })),
    warnings: snapshot.warnings.map((value) => ({ key: nextKey(), value })),
  };
}

function proposalDraftFromRequest(
  proposal: LifecycleTransitionProposalRequest,
  nextKey: () => number,
): ProposalDraft {
  return {
    proposalId: proposal.proposal_id,
    sourceSnapshot: snapshotDraftFromRequest(proposal.source_snapshot, nextKey),
    targetState: proposal.target_state,
    rationale: proposal.rationale,
    evidenceReferences: proposal.evidence_references.map((reference) => ({
      key: nextKey(),
      referenceType: reference.reference_type,
      referenceId: reference.reference_id,
      label: reference.label ?? "",
      description: reference.description ?? "",
    })),
    requestedBy: proposal.requested_by ?? "",
    requestedTimestamp: proposal.requested_timestamp ?? "",
    notes: proposal.notes.map((value) => ({ key: nextKey(), value })),
    warnings: proposal.warnings.map((value) => ({ key: nextKey(), value })),
  };
}

function reviewDraftFromRequest(
  review: LifecycleTransitionReviewRequest,
  nextKey: () => number,
): ReviewDraft {
  const resultingSnapshot = review.resulting_snapshot ?? null;
  return {
    transitionRecordId: review.transition_record_id,
    reviewOutcome: review.review_outcome,
    rationale: review.rationale,
    reviewedBy: review.reviewed_by ?? "",
    reviewedTimestamp: review.reviewed_timestamp ?? "",
    notes: review.notes.map((value) => ({ key: nextKey(), value })),
    warnings: review.warnings.map((value) => ({ key: nextKey(), value })),
    includeResultingSnapshot: resultingSnapshot !== null,
    resultingSnapshot: resultingSnapshot === null
      ? blankSnapshot()
      : snapshotDraftFromRequest(resultingSnapshot, nextKey),
  };
}

function optionalText(value: string): string | null {
  return value === "" ? null : value;
}

function snapshotRequest(draft: SnapshotDraft): LifecycleTransitionProposalRequest["source_snapshot"] {
  return {
    snapshot_id: draft.snapshotId,
    strategy_id: draft.strategyId,
    lifecycle_state: draft.lifecycleState,
    rationale: draft.rationale,
    declared_by: optionalText(draft.declaredBy),
    declared_timestamp: optionalText(draft.declaredTimestamp),
    notes: draft.notes.map((row) => row.value),
    warnings: draft.warnings.map((row) => row.value),
  };
}

function proposalRequest(draft: ProposalDraft): LifecycleTransitionProposalRequest {
  return {
    proposal_id: draft.proposalId,
    source_snapshot: snapshotRequest(draft.sourceSnapshot),
    target_state: draft.targetState,
    rationale: draft.rationale,
    evidence_references: draft.evidenceReferences.map((reference) => ({
      reference_type: reference.referenceType,
      reference_id: reference.referenceId,
      label: optionalText(reference.label),
      description: optionalText(reference.description),
    })),
    requested_by: optionalText(draft.requestedBy),
    requested_timestamp: optionalText(draft.requestedTimestamp),
    notes: draft.notes.map((row) => row.value),
    warnings: draft.warnings.map((row) => row.value),
  };
}

function reviewRequest(
  draft: ReviewDraft,
  proposal: LifecycleTransitionProposalResponse["proposal"],
): LifecycleTransitionReviewRequest {
  return {
    transition_record_id: draft.transitionRecordId,
    proposal: proposalResponseToRequest(proposal),
    review_outcome: draft.reviewOutcome,
    rationale: draft.rationale,
    resulting_snapshot: draft.includeResultingSnapshot
      ? snapshotRequest(draft.resultingSnapshot)
      : null,
    reviewed_by: optionalText(draft.reviewedBy),
    reviewed_timestamp: optionalText(draft.reviewedTimestamp),
    notes: draft.notes.map((row) => row.value),
    warnings: draft.warnings.map((row) => row.value),
  };
}

function commandFailure(error: unknown): CommandFailure {
  if (error instanceof ApiClientError) {
    return {
      title: lifecycleCommandErrorTitle(error.code),
      message: error.publicMessage,
      requestId: error.requestId,
    };
  }
  return {
    title: "Lifecycle command unavailable",
    message: "The local API is unavailable.",
    requestId: null,
  };
}

function StringListEditor({
  title,
  singular,
  idPrefix,
  rows,
  setRows,
  nextKey,
}: {
  title: string;
  singular: string;
  idPrefix: string;
  rows: StringRow[];
  setRows: (rows: StringRow[]) => void;
  nextKey: () => number;
}) {
  return (
    <div className="repeatable-editor">
      <div className="repeatable-heading">
        <div>
          <h3>{title}</h3>
          <p>Optional caller-supplied values; order and duplicates are preserved.</p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setRows([...rows, { key: nextKey(), value: "" }])}
        >
          Add {singular.toLowerCase()}
        </button>
      </div>
      {rows.length === 0 ? (
        <p className="repeatable-empty">No {title.toLowerCase()} supplied.</p>
      ) : (
        <div className="repeatable-list">
          {rows.map((row, index) => (
            <div className="repeatable-row repeatable-row--lifecycle-string" key={row.key}>
              <span className="row-number">{singular} {index + 1}</span>
              <label htmlFor={`${idPrefix}-${row.key}`}>
                Value
                <input
                  id={`${idPrefix}-${row.key}`}
                  required
                  value={row.value}
                  onChange={(event) =>
                    setRows(rows.map((candidate) =>
                      candidate.key === row.key
                        ? { ...candidate, value: event.target.value }
                        : candidate,
                    ))
                  }
                />
              </label>
              <button
                className="remove-button"
                type="button"
                onClick={() => setRows(rows.filter((candidate) => candidate.key !== row.key))}
              >
                Remove {singular.toLowerCase()} {index + 1}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SnapshotEditor({
  legend,
  idPrefix,
  draft,
  setDraft,
  nextKey,
}: {
  legend: string;
  idPrefix: string;
  draft: SnapshotDraft;
  setDraft: (draft: SnapshotDraft) => void;
  nextKey: () => number;
}) {
  const update = <Field extends keyof SnapshotDraft>(field: Field, value: SnapshotDraft[Field]) =>
    setDraft({ ...draft, [field]: value });
  return (
    <fieldset className="form-section lifecycle-snapshot-form">
      <legend>{legend}</legend>
      <p className="form-section__description">
        This is an explicit caller-supplied snapshot. The browser does not declare it current or derive it from another record.
      </p>
      <div className="form-grid">
        <label htmlFor={`${idPrefix}-snapshot-id`}>
          Snapshot ID
          <input id={`${idPrefix}-snapshot-id`} required value={draft.snapshotId} onChange={(event) => update("snapshotId", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-strategy-id`}>
          Strategy ID
          <input id={`${idPrefix}-strategy-id`} required value={draft.strategyId} onChange={(event) => update("strategyId", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-lifecycle-state`}>
          Lifecycle state
          <input id={`${idPrefix}-lifecycle-state`} required value={draft.lifecycleState} onChange={(event) => update("lifecycleState", event.target.value)} />
          <span className="field-guidance">Backend lifecycle rules are authoritative.</span>
        </label>
        <label className="form-grid__wide" htmlFor={`${idPrefix}-rationale`}>
          Snapshot rationale
          <textarea id={`${idPrefix}-rationale`} required value={draft.rationale} onChange={(event) => update("rationale", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-declared-by`}>
          Declared by <span className="optional-label">(optional)</span>
          <input id={`${idPrefix}-declared-by`} value={draft.declaredBy} onChange={(event) => update("declaredBy", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-declared-timestamp`}>
          Declared timestamp <span className="optional-label">(optional)</span>
          <input id={`${idPrefix}-declared-timestamp`} value={draft.declaredTimestamp} onChange={(event) => update("declaredTimestamp", event.target.value)} />
          <span className="field-guidance">Supply an explicit timestamp accepted by the backend.</span>
        </label>
      </div>
      <StringListEditor title="Snapshot notes" singular="Snapshot note" idPrefix={`${idPrefix}-note`} rows={draft.notes} setRows={(notes) => update("notes", notes)} nextKey={nextKey} />
      <StringListEditor title="Snapshot warnings" singular="Snapshot warning" idPrefix={`${idPrefix}-warning`} rows={draft.warnings} setRows={(warnings) => update("warnings", warnings)} nextKey={nextKey} />
    </fieldset>
  );
}

function EvidenceEditor({
  rows,
  setRows,
  nextKey,
}: {
  rows: EvidenceRow[];
  setRows: (rows: EvidenceRow[]) => void;
  nextKey: () => number;
}) {
  return (
    <fieldset className="form-section">
      <legend>Evidence references</legend>
      <p className="form-section__description">
        References remain unresolved pointers. The backend decides whether the supplied evidence types satisfy the requested transition.
      </p>
      <div className="repeatable-heading">
        <div><h3>Caller-supplied references</h3><p>Order and duplicates remain visible.</p></div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setRows([...rows, { key: nextKey(), referenceType: "", referenceId: "", label: "", description: "" }])}
        >
          Add evidence reference
        </button>
      </div>
      {rows.length === 0 ? <p className="repeatable-empty">No evidence references supplied. The backend will validate this proposal.</p> : (
        <div className="repeatable-list">
          {rows.map((row, index) => {
            const update = (field: keyof Omit<EvidenceRow, "key">, value: string) =>
              setRows(rows.map((candidate) => candidate.key === row.key ? { ...candidate, [field]: value } : candidate));
            return (
              <div className="repeatable-row lifecycle-evidence-row" key={row.key}>
                <span className="row-number">Evidence reference {index + 1}</span>
                <label>Reference type<input required value={row.referenceType} onChange={(event) => update("referenceType", event.target.value)} /></label>
                <label>Reference ID<input required value={row.referenceId} onChange={(event) => update("referenceId", event.target.value)} /></label>
                <label>Label <span className="optional-label">(optional)</span><input value={row.label} onChange={(event) => update("label", event.target.value)} /></label>
                <label>Description <span className="optional-label">(optional)</span><input value={row.description} onChange={(event) => update("description", event.target.value)} /></label>
                <button className="remove-button" type="button" onClick={() => setRows(rows.filter((candidate) => candidate.key !== row.key))}>Remove evidence reference {index + 1}</button>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

export function LifecycleReviewWorkspace() {
  const keyRef = useRef(0);
  const nextKey = () => ++keyRef.current;
  const [proposalDraft, setProposalDraft] = useState<ProposalDraft>(blankProposal);
  const [reviewDraft, setReviewDraft] = useState<ReviewDraft>(blankReview);
  const [proposalPending, setProposalPending] = useState(false);
  const [reviewPending, setReviewPending] = useState(false);
  const [proposalResult, setProposalResult] = useState<ApiResult<LifecycleTransitionProposalResponse> | null>(null);
  const [reviewResult, setReviewResult] = useState<ApiResult<LifecycleTransitionReviewResponse> | null>(null);
  const [proposalFailure, setProposalFailure] = useState<CommandFailure | null>(null);
  const [reviewFailure, setReviewFailure] = useState<CommandFailure | null>(null);
  const [demoReviewDraft, setDemoReviewDraft] = useState<ReviewDraft | null>(null);
  const [demoLoadFailure, setDemoLoadFailure] = useState<CommandFailure | null>(null);

  const loadDemoLifecycleExample = async () => {
    setDemoLoadFailure(null);
    try {
      const result = await fetchDemoWorkspace();
      const descriptor: DemoWorkspaceDescriptorResponse = result.data;
      setProposalDraft(
        proposalDraftFromRequest(descriptor.lifecycle_proposal_example, nextKey),
      );
      setDemoReviewDraft(
        reviewDraftFromRequest(descriptor.lifecycle_review_example, nextKey),
      );
      setProposalResult(null);
      setReviewResult(null);
      setProposalFailure(null);
      setReviewFailure(null);
    } catch (error) {
      setDemoLoadFailure(commandFailure(error));
    }
  };

  const submitProposal = async () => {
    if (proposalPending) return;
    setProposalPending(true);
    setProposalFailure(null);
    try {
      const result = await submitLifecycleTransitionProposal(proposalRequest(proposalDraft));
      setProposalResult(result);
      setReviewResult(null);
      setReviewFailure(null);
      setReviewDraft(demoReviewDraft ?? blankReview());
    } catch (error) {
      setProposalFailure(commandFailure(error));
    } finally {
      setProposalPending(false);
    }
  };

  const submitReview = async () => {
    if (reviewPending || proposalResult === null) return;
    setReviewPending(true);
    setReviewFailure(null);
    try {
      const result = await submitLifecycleTransitionReview(
        reviewRequest(reviewDraft, proposalResult.data.proposal),
      );
      setReviewResult(result);
    } catch (error) {
      setReviewFailure(commandFailure(error));
    } finally {
      setReviewPending(false);
    }
  };

  const displayedProposal = reviewResult?.data.transition_record.proposal ?? proposalResult?.data.proposal ?? null;

  return (
    <div className="business-workspace lifecycle-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">Lifecycle Review · S158</p>
          <h1>Lifecycle proposal, human review, and timeline</h1>
          <p>Create explicit governance commands and inspect the normalized immutable evidence returned by the existing backend-owned lifecycle contracts.</p>
        </div>
        <div className="record-card__actions">
          <button className="secondary-button" type="button" onClick={() => void loadDemoLifecycleExample()}>Load demo lifecycle example</button>
          <Link className="text-link" href="/strategies">Browse strategies</Link>
          <Link className="text-link" href="/evidence-manifests">Inspect governance evidence</Link>
        </div>
      </header>

      {demoLoadFailure ? <div className="mutation-notice mutation-notice--error" role="alert"><h3>{demoLoadFailure.title}</h3><p>{demoLoadFailure.message}</p><RequestId value={demoLoadFailure.requestId} /></div> : null}

      <section className="boundary-card lifecycle-boundary" aria-labelledby="lifecycle-boundary-title">
        <p className="eyebrow">Human-control boundary</p>
        <h2 id="lifecycle-boundary-title">No command on this page applies a lifecycle transition.</h2>
        <p>The browser submits generated OpenAPI request shapes only. Backend domain factories validate lifecycle states, permitted transitions, evidence requirements, review outcomes, and resulting-snapshot rules.</p>
      </section>

      <form className="paper-job-form lifecycle-command-form" onSubmit={(event) => { event.preventDefault(); void submitProposal(); }}>
        <div className="section-heading"><div><p className="eyebrow">Step 1</p><h2>Create an explicit proposal</h2></div></div>
        <SnapshotEditor legend="Source lifecycle snapshot" idPrefix="source" draft={proposalDraft.sourceSnapshot} setDraft={(sourceSnapshot) => setProposalDraft({ ...proposalDraft, sourceSnapshot })} nextKey={nextKey} />
        <fieldset className="form-section">
          <legend>Transition proposal</legend>
          <p className="form-section__description">Enter the requested transition. The browser does not infer a target, approve the request, or validate domain eligibility.</p>
          <div className="form-grid">
            <label>Proposal ID<input required value={proposalDraft.proposalId} onChange={(event) => setProposalDraft({ ...proposalDraft, proposalId: event.target.value })} /></label>
            <label>Target state<input required value={proposalDraft.targetState} onChange={(event) => setProposalDraft({ ...proposalDraft, targetState: event.target.value })} /><span className="field-guidance">Backend lifecycle rules are authoritative.</span></label>
            <label>Requested by <span className="optional-label">(optional)</span><input value={proposalDraft.requestedBy} onChange={(event) => setProposalDraft({ ...proposalDraft, requestedBy: event.target.value })} /></label>
            <label>Requested timestamp <span className="optional-label">(optional)</span><input value={proposalDraft.requestedTimestamp} onChange={(event) => setProposalDraft({ ...proposalDraft, requestedTimestamp: event.target.value })} /></label>
            <label className="form-grid__wide">Proposal rationale<textarea required value={proposalDraft.rationale} onChange={(event) => setProposalDraft({ ...proposalDraft, rationale: event.target.value })} /></label>
          </div>
          <StringListEditor title="Proposal notes" singular="Proposal note" idPrefix="proposal-note" rows={proposalDraft.notes} setRows={(notes) => setProposalDraft({ ...proposalDraft, notes })} nextKey={nextKey} />
          <StringListEditor title="Proposal warnings" singular="Proposal warning" idPrefix="proposal-warning" rows={proposalDraft.warnings} setRows={(warnings) => setProposalDraft({ ...proposalDraft, warnings })} nextKey={nextKey} />
        </fieldset>
        <EvidenceEditor rows={proposalDraft.evidenceReferences} setRows={(evidenceReferences) => setProposalDraft({ ...proposalDraft, evidenceReferences })} nextKey={nextKey} />
        {proposalFailure ? <div className="mutation-notice mutation-notice--error" role="alert"><h3>{proposalFailure.title}</h3><p>{proposalFailure.message}</p><RequestId value={proposalFailure.requestId} /></div> : null}
        <div className="submission-actions">
          <button className="primary-button" type="submit" disabled={proposalPending}>{proposalPending ? "Creating proposal…" : "Create non-executing proposal"}</button>
          <p>One synchronous command. No persistence, promotion, paper run, or automatic follow-up.</p>
        </div>
      </form>

      {proposalResult ? (
        <div className="lifecycle-response-stack">
          <div className="mutation-notice mutation-notice--success" role="status"><h2>Proposal response received</h2><p>The normalized proposal is available for inspection and an explicit human review command.</p><RequestId value={proposalResult.requestId} /></div>
          <SnapshotInspection title="Source lifecycle snapshot" snapshot={proposalResult.data.proposal.source_snapshot} boundary="This immutable source snapshot remains distinct from any proposal or review outcome." />
          <ProposalInspection proposal={proposalResult.data.proposal} />

          <form className="paper-job-form lifecycle-command-form" onSubmit={(event) => { event.preventDefault(); void submitReview(); }}>
            <div className="section-heading"><div><p className="eyebrow">Step 2</p><h2>Record an explicit human review</h2></div></div>
            <fieldset className="form-section">
              <legend>Human review record</legend>
              <p className="form-section__description">The review carries the latest successful normalized proposal response. Enter the outcome explicitly; the browser does not infer it from proposal or evidence fields.</p>
              <div className="form-grid">
                <label>Transition record ID<input required value={reviewDraft.transitionRecordId} onChange={(event) => setReviewDraft({ ...reviewDraft, transitionRecordId: event.target.value })} /></label>
                <label>Review outcome<input required value={reviewDraft.reviewOutcome} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewOutcome: event.target.value })} /><span className="field-guidance">Backend human-control rules are authoritative.</span></label>
                <label>Reviewed by <span className="optional-label">(optional)</span><input value={reviewDraft.reviewedBy} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewedBy: event.target.value })} /></label>
                <label>Reviewed timestamp <span className="optional-label">(optional)</span><input value={reviewDraft.reviewedTimestamp} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewedTimestamp: event.target.value })} /></label>
                <label className="form-grid__wide">Review rationale<textarea required value={reviewDraft.rationale} onChange={(event) => setReviewDraft({ ...reviewDraft, rationale: event.target.value })} /></label>
              </div>
              <StringListEditor title="Review notes" singular="Review note" idPrefix="review-note" rows={reviewDraft.notes} setRows={(notes) => setReviewDraft({ ...reviewDraft, notes })} nextKey={nextKey} />
              <StringListEditor title="Review warnings" singular="Review warning" idPrefix="review-warning" rows={reviewDraft.warnings} setRows={(warnings) => setReviewDraft({ ...reviewDraft, warnings })} nextKey={nextKey} />
            </fieldset>
            <fieldset className="form-section">
              <legend>Optional resulting snapshot</legend>
              <label className="lifecycle-snapshot-toggle"><input type="checkbox" checked={reviewDraft.includeResultingSnapshot} onChange={(event) => setReviewDraft({ ...reviewDraft, includeResultingSnapshot: event.target.checked })} />Include an explicit caller-supplied resulting snapshot</label>
              <p className="form-section__description">The backend validates whether a resulting snapshot is allowed or required for the supplied outcome. Inclusion never makes the snapshot current or proves execution.</p>
            </fieldset>
            {reviewDraft.includeResultingSnapshot ? <SnapshotEditor legend="Caller-supplied resulting snapshot" idPrefix="resulting" draft={reviewDraft.resultingSnapshot} setDraft={(resultingSnapshot) => setReviewDraft({ ...reviewDraft, resultingSnapshot })} nextKey={nextKey} /> : null}
            {reviewFailure ? <div className="mutation-notice mutation-notice--error" role="alert"><h3>{reviewFailure.title}</h3><p>{reviewFailure.message}</p><RequestId value={reviewFailure.requestId} /></div> : null}
            <div className="submission-actions">
              <button className="primary-button" type="submit" disabled={reviewPending}>{reviewPending ? "Recording human review…" : "Record human review evidence"}</button>
              <p>This command records governance evidence only. It does not apply the requested transition.</p>
            </div>
          </form>
        </div>
      ) : null}

      {reviewResult ? <div className="lifecycle-response-stack"><div className="mutation-notice mutation-notice--success" role="status"><h2>Human review response received</h2><p>The normalized record is available for inspection. No lifecycle execution is inferred.</p><RequestId value={reviewResult.requestId} /></div><ReviewInspection response={reviewResult.data} />{reviewResult.data.transition_record.resulting_snapshot ? <SnapshotInspection title="Caller-supplied resulting snapshot" snapshot={reviewResult.data.transition_record.resulting_snapshot} boundary="This returned snapshot is immutable evidence. The workspace does not identify it as globally current or executed." /> : null}</div> : null}

      {displayedProposal ? <LifecycleTimeline proposal={displayedProposal} review={reviewResult?.data ?? null} /> : (
        <section className="state-panel lifecycle-empty-timeline"><p className="eyebrow">Timeline evidence</p><h2>No lifecycle command response yet</h2><p>Create a proposal to inspect its immutable source snapshot, unresolved evidence references, and non-executing proposal event in order.</p></section>
      )}
    </div>
  );
}
