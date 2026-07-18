"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";

import { ErrorState, RequestId } from "@/components/data-states";
import { useErrorPresentation } from "@/i18n/errors";
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
import { proposalResponseToRequest } from "@/lib/lifecycle-review";

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
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number | null;
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
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
      httpStatus: error.status > 0 ? error.status : null,
    };
  }
  return {
    code: "api_unavailable",
    message: "The local API is unavailable.",
    requestId: null,
    httpStatus: null,
  };
}

function LifecycleFailureNotice({
  failure,
  operation,
}: {
  failure: CommandFailure;
  operation: string;
}) {
  const error = useErrorPresentation(failure.code);
  return (
    <ErrorState
      className="mutation-notice mutation-notice--error"
      title={error.title}
      code={failure.code}
      message={failure.message}
      requestId={failure.requestId}
      httpStatus={failure.httpStatus}
      operation={operation}
    />
  );
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
  const t = useTranslations("lifecycle.editor");
  return (
    <div className="repeatable-editor">
      <div className="repeatable-heading">
        <div>
          <h3>{title}</h3>
          <p>{t("optionalValues")}</p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setRows([...rows, { key: nextKey(), value: "" }])}
        >
          {t("add", { item: singular })}
        </button>
      </div>
      {rows.length === 0 ? (
        <p className="repeatable-empty">{t("none", { title })}</p>
      ) : (
        <div className="repeatable-list">
          {rows.map((row, index) => (
            <div className="repeatable-row repeatable-row--lifecycle-string" key={row.key}>
              <span className="row-number">{t("numbered", { item: singular, number: index + 1 })}</span>
              <label htmlFor={`${idPrefix}-${row.key}`}>
                {t("value")}
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
                {t("remove", { item: singular, number: index + 1 })}
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
  const t = useTranslations("lifecycle.editor");
  const workspace = useTranslations("lifecycle.workspace");
  const update = <Field extends keyof SnapshotDraft>(field: Field, value: SnapshotDraft[Field]) =>
    setDraft({ ...draft, [field]: value });
  return (
    <fieldset className="form-section">
      <legend>{legend}</legend>
      <p className="form-section__description">
        {t("snapshotDescription")}
      </p>
      <div className="form-grid">
        <label htmlFor={`${idPrefix}-snapshot-id`}>
          {t("snapshotId")}
          <input id={`${idPrefix}-snapshot-id`} required value={draft.snapshotId} onChange={(event) => update("snapshotId", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-strategy-id`}>
          {t("strategyId")}
          <input id={`${idPrefix}-strategy-id`} required value={draft.strategyId} onChange={(event) => update("strategyId", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-lifecycle-state`}>
          {t("lifecycleState")}
          <input id={`${idPrefix}-lifecycle-state`} required value={draft.lifecycleState} onChange={(event) => update("lifecycleState", event.target.value)} />
          <span className="field-guidance">{workspace("rulesBoundary")}</span>
        </label>
        <label className="form-grid__wide" htmlFor={`${idPrefix}-rationale`}>
          {t("snapshotRationale")}
          <textarea id={`${idPrefix}-rationale`} required value={draft.rationale} onChange={(event) => update("rationale", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-declared-by`}>
          {t("declaredBy")} <span className="optional-label">({workspace("optional")})</span>
          <input id={`${idPrefix}-declared-by`} value={draft.declaredBy} onChange={(event) => update("declaredBy", event.target.value)} />
        </label>
        <label htmlFor={`${idPrefix}-declared-timestamp`}>
          {t("declaredTimestamp")} <span className="optional-label">({workspace("optional")})</span>
          <input id={`${idPrefix}-declared-timestamp`} value={draft.declaredTimestamp} onChange={(event) => update("declaredTimestamp", event.target.value)} />
          <span className="field-guidance">{t("timestampGuidance")}</span>
        </label>
      </div>
      <StringListEditor title={t("snapshotNotes")} singular={t("snapshotNote")} idPrefix={`${idPrefix}-note`} rows={draft.notes} setRows={(notes) => update("notes", notes)} nextKey={nextKey} />
      <StringListEditor title={t("snapshotWarnings")} singular={t("snapshotWarning")} idPrefix={`${idPrefix}-warning`} rows={draft.warnings} setRows={(warnings) => update("warnings", warnings)} nextKey={nextKey} />
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
  const t = useTranslations("lifecycle.editor");
  const workspace = useTranslations("lifecycle.workspace");
  return (
    <fieldset className="form-section">
      <legend>{t("evidenceLegend")}</legend>
      <p className="form-section__description">
        {t("evidenceDescription")}
      </p>
      <div className="repeatable-heading">
        <div><h3>{t("callerReferences")}</h3><p>{t("orderBoundary")}</p></div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setRows([...rows, { key: nextKey(), referenceType: "", referenceId: "", label: "", description: "" }])}
        >
          {t("addEvidence")}
        </button>
      </div>
      {rows.length === 0 ? <p className="repeatable-empty">{t("noEvidence")}</p> : (
        <div className="repeatable-list">
          {rows.map((row, index) => {
            const update = (field: keyof Omit<EvidenceRow, "key">, value: string) =>
              setRows(rows.map((candidate) => candidate.key === row.key ? { ...candidate, [field]: value } : candidate));
            return (
              <div className="repeatable-row lifecycle-evidence-row" key={row.key}>
                <span className="row-number">{t("evidenceNumber", { number: index + 1 })}</span>
                <label>{t("referenceType")}<input required value={row.referenceType} onChange={(event) => update("referenceType", event.target.value)} /></label>
                <label>{t("referenceId")}<input required value={row.referenceId} onChange={(event) => update("referenceId", event.target.value)} /></label>
                <label>{t("label")} <span className="optional-label">({workspace("optional")})</span><input value={row.label} onChange={(event) => update("label", event.target.value)} /></label>
                <label>{t("description")} <span className="optional-label">({workspace("optional")})</span><input value={row.description} onChange={(event) => update("description", event.target.value)} /></label>
                <button className="remove-button" type="button" onClick={() => setRows(rows.filter((candidate) => candidate.key !== row.key))}>{t("removeEvidence", { number: index + 1 })}</button>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

export function LifecycleReviewWorkspace() {
  const t = useTranslations("lifecycle.workspace");
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
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <div className="record-card__actions">
          <button className="secondary-button" type="button" onClick={() => void loadDemoLifecycleExample()}>{t("loadDemo")}</button>
          <Link className="text-link" href="/strategies">{t("browseStrategies")}</Link>
          <Link className="text-link" href="/evidence-manifests">{t("inspectEvidence")}</Link>
        </div>
      </header>

      {demoLoadFailure ? <LifecycleFailureNotice failure={demoLoadFailure} operation="demo_workspace.read" /> : null}

      <section className="boundary-card lifecycle-boundary" aria-labelledby="lifecycle-boundary-title">
        <p className="eyebrow">{t("boundaryEyebrow")}</p>
        <h2 id="lifecycle-boundary-title">{t("boundaryTitle")}</h2>
        <p>{t("boundaryDescription")}</p>
      </section>

      <form className="paper-job-form lifecycle-command-form" onSubmit={(event) => { event.preventDefault(); void submitProposal(); }}>
        <div className="section-heading"><div><p className="eyebrow">{t("stepOne")}</p><h2>{t("createProposal")}</h2></div></div>
        <SnapshotEditor legend={t("sourceSnapshot")} idPrefix="source" draft={proposalDraft.sourceSnapshot} setDraft={(sourceSnapshot) => setProposalDraft({ ...proposalDraft, sourceSnapshot })} nextKey={nextKey} />
        <fieldset className="form-section">
          <legend>{t("proposalLegend")}</legend>
          <p className="form-section__description">{t("proposalDescription")}</p>
          <div className="form-grid">
            <label>{t("proposalId")}<input required value={proposalDraft.proposalId} onChange={(event) => setProposalDraft({ ...proposalDraft, proposalId: event.target.value })} /></label>
            <label>{t("targetState")}<input required value={proposalDraft.targetState} onChange={(event) => setProposalDraft({ ...proposalDraft, targetState: event.target.value })} /><span className="field-guidance">{t("rulesBoundary")}</span></label>
            <label>{t("requestedBy")} <span className="optional-label">({t("optional")})</span><input value={proposalDraft.requestedBy} onChange={(event) => setProposalDraft({ ...proposalDraft, requestedBy: event.target.value })} /></label>
            <label>{t("requestedTimestamp")} <span className="optional-label">({t("optional")})</span><input value={proposalDraft.requestedTimestamp} onChange={(event) => setProposalDraft({ ...proposalDraft, requestedTimestamp: event.target.value })} /></label>
            <label className="form-grid__wide">{t("proposalRationale")}<textarea required value={proposalDraft.rationale} onChange={(event) => setProposalDraft({ ...proposalDraft, rationale: event.target.value })} /></label>
          </div>
          <StringListEditor title={t("proposalNotes")} singular={t("proposalNote")} idPrefix="proposal-note" rows={proposalDraft.notes} setRows={(notes) => setProposalDraft({ ...proposalDraft, notes })} nextKey={nextKey} />
          <StringListEditor title={t("proposalWarnings")} singular={t("proposalWarning")} idPrefix="proposal-warning" rows={proposalDraft.warnings} setRows={(warnings) => setProposalDraft({ ...proposalDraft, warnings })} nextKey={nextKey} />
        </fieldset>
        <EvidenceEditor rows={proposalDraft.evidenceReferences} setRows={(evidenceReferences) => setProposalDraft({ ...proposalDraft, evidenceReferences })} nextKey={nextKey} />
        {proposalFailure ? <LifecycleFailureNotice failure={proposalFailure} operation="lifecycle.propose" /> : null}
        <div className="submission-actions">
          <button className="primary-button" type="submit" disabled={proposalPending}>{proposalPending ? t("creatingProposal") : t("createNonExecuting")}</button>
          <p>{t("proposalCommandBoundary")}</p>
        </div>
      </form>

      {proposalResult ? (
        <div className="lifecycle-response-stack">
          <div className="mutation-notice mutation-notice--recorded" role="status"><h2>{t("proposalResponseTitle")}</h2><p>{t("proposalResponseDescription")}</p><RequestId value={proposalResult.requestId} /></div>
          <SnapshotInspection title={t("sourceSnapshot")} snapshot={proposalResult.data.proposal.source_snapshot} boundary={t("sourceSnapshotBoundary")} />
          <ProposalInspection proposal={proposalResult.data.proposal} />

          <form className="paper-job-form lifecycle-command-form" onSubmit={(event) => { event.preventDefault(); void submitReview(); }}>
            <div className="section-heading"><div><p className="eyebrow">{t("stepTwo")}</p><h2>{t("recordReview")}</h2></div></div>
            <fieldset className="form-section">
              <legend>{t("reviewLegend")}</legend>
              <p className="form-section__description">{t("reviewDescription")}</p>
              <div className="form-grid">
                <label>{t("transitionRecordId")}<input required value={reviewDraft.transitionRecordId} onChange={(event) => setReviewDraft({ ...reviewDraft, transitionRecordId: event.target.value })} /></label>
                <label>{t("reviewOutcome")}<input required value={reviewDraft.reviewOutcome} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewOutcome: event.target.value })} /><span className="field-guidance">{t("humanRulesBoundary")}</span></label>
                <label>{t("reviewedBy")} <span className="optional-label">({t("optional")})</span><input value={reviewDraft.reviewedBy} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewedBy: event.target.value })} /></label>
                <label>{t("reviewedTimestamp")} <span className="optional-label">({t("optional")})</span><input value={reviewDraft.reviewedTimestamp} onChange={(event) => setReviewDraft({ ...reviewDraft, reviewedTimestamp: event.target.value })} /></label>
                <label className="form-grid__wide">{t("reviewRationale")}<textarea required value={reviewDraft.rationale} onChange={(event) => setReviewDraft({ ...reviewDraft, rationale: event.target.value })} /></label>
              </div>
              <StringListEditor title={t("reviewNotes")} singular={t("reviewNote")} idPrefix="review-note" rows={reviewDraft.notes} setRows={(notes) => setReviewDraft({ ...reviewDraft, notes })} nextKey={nextKey} />
              <StringListEditor title={t("reviewWarnings")} singular={t("reviewWarning")} idPrefix="review-warning" rows={reviewDraft.warnings} setRows={(warnings) => setReviewDraft({ ...reviewDraft, warnings })} nextKey={nextKey} />
            </fieldset>
            <fieldset className="form-section">
              <legend>{t("resultingLegend")}</legend>
              <label className="lifecycle-snapshot-toggle"><input type="checkbox" checked={reviewDraft.includeResultingSnapshot} onChange={(event) => setReviewDraft({ ...reviewDraft, includeResultingSnapshot: event.target.checked })} />{t("includeResulting")}</label>
              <p className="form-section__description">{t("resultingBoundary")}</p>
            </fieldset>
            {reviewDraft.includeResultingSnapshot ? <SnapshotEditor legend={t("callerResulting")} idPrefix="resulting" draft={reviewDraft.resultingSnapshot} setDraft={(resultingSnapshot) => setReviewDraft({ ...reviewDraft, resultingSnapshot })} nextKey={nextKey} /> : null}
            {reviewFailure ? <LifecycleFailureNotice failure={reviewFailure} operation="lifecycle.review" /> : null}
            <div className="submission-actions">
              <button className="primary-button" type="submit" disabled={reviewPending}>{reviewPending ? t("recordingReview") : t("recordReviewEvidence")}</button>
              <p>{t("reviewCommandBoundary")}</p>
            </div>
          </form>
        </div>
      ) : null}

      {reviewResult ? <div className="lifecycle-response-stack"><div className="mutation-notice mutation-notice--recorded" role="status"><h2>{t("reviewResponseTitle")}</h2><p>{t("reviewResponseDescription")}</p><RequestId value={reviewResult.requestId} /></div><ReviewInspection response={reviewResult.data} />{reviewResult.data.transition_record.resulting_snapshot ? <SnapshotInspection title={t("callerResulting")} snapshot={reviewResult.data.transition_record.resulting_snapshot} boundary={t("resultingSnapshotBoundary")} /> : null}</div> : null}

      {displayedProposal ? <LifecycleTimeline proposal={displayedProposal} review={reviewResult?.data ?? null} /> : (
        <section className="state-panel state-panel--empty lifecycle-empty-timeline"><p className="eyebrow">{t("timelineEyebrow")}</p><h2>{t("timelineEmptyTitle")}</h2><p>{t("timelineEmptyDescription")}</p></section>
      )}
    </div>
  );
}
