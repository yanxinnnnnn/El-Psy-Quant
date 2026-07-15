import type {
  LifecycleTransitionProposalResponse,
  LifecycleTransitionReviewResponse,
} from "@/lib/api-client";

function OrderedValues({ values, empty }: { values: readonly string[]; empty: string }) {
  return values.length === 0 ? <p className="repeatable-empty">{empty}</p> : (
    <ol className="ordered-values">{values.map((value, index) => <li key={index}>{value}</li>)}</ol>
  );
}

type SnapshotResponse = LifecycleTransitionProposalResponse["proposal"]["source_snapshot"];

export function SnapshotInspection({ title, snapshot, boundary }: { title: string; snapshot: SnapshotResponse; boundary: string }) {
  return (
    <section className="lifecycle-record" aria-label={title}>
      <p className="eyebrow">Immutable snapshot · Schema {snapshot.schema_version}</p>
      <h3>{title}</h3>
      <p className="neutral-note">{boundary}</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>Snapshot ID</dt><dd>{snapshot.snapshot_id}</dd></div>
        <div><dt>Strategy ID</dt><dd>{snapshot.strategy_id}</dd></div>
        <div><dt>Lifecycle state</dt><dd>{snapshot.lifecycle_state}</dd></div>
        <div><dt>Declared by</dt><dd>{snapshot.declared_by ?? "Not supplied"}</dd></div>
        <div><dt>Declared timestamp</dt><dd>{snapshot.declared_timestamp ?? "Not supplied"}</dd></div>
        <div><dt>Rationale</dt><dd>{snapshot.rationale}</dd></div>
      </dl>
      <div className="lifecycle-record__collections">
        <div><h4>Notes</h4><OrderedValues values={snapshot.notes} empty="No snapshot notes supplied." /></div>
        <div><h4>Warnings</h4><OrderedValues values={snapshot.warnings} empty="No snapshot warnings supplied." /></div>
      </div>
    </section>
  );
}

export function ProposalInspection({ proposal }: { proposal: LifecycleTransitionProposalResponse["proposal"] }) {
  return (
    <section className="lifecycle-inspection" aria-labelledby="proposal-inspection-title">
      <div className="section-heading">
        <div><p className="eyebrow">Latest successful normalized response</p><h2 id="proposal-inspection-title">Lifecycle proposal</h2></div>
        <span className="job-status job-status--queued">Non-executing</span>
      </div>
      <p className="neutral-note">This proposal is a request for human review. It is not approval, execution, promotion, or a current-state change.</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>Proposal ID</dt><dd>{proposal.proposal_id}</dd></div>
        <div><dt>Schema version</dt><dd>{proposal.schema_version}</dd></div>
        <div><dt>Source state</dt><dd>{proposal.source_snapshot.lifecycle_state}</dd></div>
        <div><dt>Target state</dt><dd>{proposal.target_state}</dd></div>
        <div><dt>Requested by</dt><dd>{proposal.requested_by ?? "Not supplied"}</dd></div>
        <div><dt>Requested timestamp</dt><dd>{proposal.requested_timestamp ?? "Not supplied"}</dd></div>
        <div><dt>Rationale</dt><dd>{proposal.rationale}</dd></div>
      </dl>
      <div className="lifecycle-evidence-inspection">
        <h3>Evidence references</h3>
        {proposal.evidence_references.length === 0 ? <p className="repeatable-empty">No evidence references returned.</p> : (
          <ol className="lifecycle-evidence-list">
            {proposal.evidence_references.map((reference, index) => (
              <li key={index}>
                <p className="record-card__meta">Reference {index + 1} · Schema {reference.schema_version}</p>
                <h4>{reference.label ?? reference.reference_id}</h4>
                <dl className="compact-definitions">
                  <div><dt>Type</dt><dd>{reference.reference_type}</dd></div>
                  <div><dt>ID</dt><dd>{reference.reference_id}</dd></div>
                  <div><dt>Description</dt><dd>{reference.description ?? "Not supplied"}</dd></div>
                </dl>
              </li>
            ))}
          </ol>
        )}
      </div>
      <div className="lifecycle-record__collections">
        <div><h3>Proposal notes</h3><OrderedValues values={proposal.notes} empty="No proposal notes supplied." /></div>
        <div><h3>Proposal warnings</h3><OrderedValues values={proposal.warnings} empty="No proposal warnings supplied." /></div>
      </div>
    </section>
  );
}

export function ReviewInspection({ response }: { response: LifecycleTransitionReviewResponse }) {
  const record = response.transition_record;
  return (
    <section className="lifecycle-inspection" aria-labelledby="review-inspection-title">
      <div className="section-heading">
        <div><p className="eyebrow">Latest successful normalized response</p><h2 id="review-inspection-title">Human review record</h2></div>
        <span className="job-status">Governance evidence</span>
      </div>
      <p className="neutral-note">The outcome below is a human-controlled record. It does not prove execution, automatically promote the strategy, or make any snapshot current.</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>Transition record ID</dt><dd>{record.transition_record_id}</dd></div>
        <div><dt>Schema version</dt><dd>{record.schema_version}</dd></div>
        <div><dt>Review outcome</dt><dd>{record.review_outcome}</dd></div>
        <div><dt>Reviewed by</dt><dd>{record.reviewed_by ?? "Not supplied"}</dd></div>
        <div><dt>Reviewed timestamp</dt><dd>{record.reviewed_timestamp ?? "Not supplied"}</dd></div>
        <div><dt>Rationale</dt><dd>{record.rationale}</dd></div>
      </dl>
      <div className="lifecycle-record__collections">
        <div><h3>Review notes</h3><OrderedValues values={record.notes} empty="No review notes supplied." /></div>
        <div><h3>Review warnings</h3><OrderedValues values={record.warnings} empty="No review warnings supplied." /></div>
      </div>
    </section>
  );
}

export function LifecycleTimeline({
  proposal,
  review,
}: {
  proposal: LifecycleTransitionProposalResponse["proposal"];
  review: LifecycleTransitionReviewResponse | null;
}) {
  const record = review?.transition_record ?? null;
  return (
    <section className="lifecycle-inspection" aria-labelledby="lifecycle-timeline-title">
      <div className="section-heading">
        <div><p className="eyebrow">Immutable evidence sequence</p><h2 id="lifecycle-timeline-title">Lifecycle timeline</h2></div>
      </div>
      <p className="neutral-note">This in-session sequence is assembled only from the command responses shown on this page. It is not a persisted current-state read model.</p>
      <ol className="lifecycle-timeline">
        <li><span>1</span><div><p className="record-card__meta">Source snapshot</p><h3>{proposal.source_snapshot.snapshot_id}</h3><p>Caller-supplied state: {proposal.source_snapshot.lifecycle_state}. No current-state claim is inferred.</p></div></li>
        <li><span>2</span><div><p className="record-card__meta">Proposal</p><h3>{proposal.proposal_id}</h3><p>Requested transition to {proposal.target_state}. Proposal creation is non-executing.</p></div></li>
        {record ? <li><span>3</span><div><p className="record-card__meta">Human review record</p><h3>{record.transition_record_id}</h3><p>Recorded outcome: {record.review_outcome}. This is governance evidence, not execution evidence.</p></div></li> : null}
        {record?.resulting_snapshot ? <li><span>4</span><div><p className="record-card__meta">Caller-supplied resulting snapshot</p><h3>{record.resulting_snapshot.snapshot_id}</h3><p>Returned state: {record.resulting_snapshot.lifecycle_state}. The workspace does not mark this snapshot current.</p></div></li> : null}
      </ol>
    </section>
  );
}
