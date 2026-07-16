"use client";

import { useTranslations } from "next-intl";

import { LifecycleStateValue, ReviewOutcomeValue } from "@/components/domain-values";
import { StatusBadge } from "@/components/ui/status-badge";
import { LocalizedTimestamp } from "@/components/localized-values";
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
  const t = useTranslations("lifecycle.inspection");
  const common = useTranslations("common.states");
  return (
    <section className="lifecycle-record" aria-label={title}>
      <p className="eyebrow">{t("immutableSnapshot", { schema: snapshot.schema_version })}</p>
      <h3>{title}</h3>
      <p className="neutral-note">{boundary}</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>{t("snapshotId")}</dt><dd>{snapshot.snapshot_id}</dd></div>
        <div><dt>{t("strategyId")}</dt><dd>{snapshot.strategy_id}</dd></div>
        <div><dt>{t("lifecycleState")}</dt><dd><LifecycleStateValue value={snapshot.lifecycle_state} /></dd></div>
        <div><dt>{t("declaredBy")}</dt><dd>{snapshot.declared_by ?? common("notSupplied")}</dd></div>
        <div><dt>{t("declaredTimestamp")}</dt><dd>{snapshot.declared_timestamp ? <LocalizedTimestamp value={snapshot.declared_timestamp} /> : common("notSupplied")}</dd></div>
        <div><dt>{t("rationale")}</dt><dd>{snapshot.rationale}</dd></div>
      </dl>
      <div className="lifecycle-record__collections">
        <div><h4>{t("notes")}</h4><OrderedValues values={snapshot.notes} empty={t("noSnapshotNotes")} /></div>
        <div><h4>{t("warnings")}</h4><OrderedValues values={snapshot.warnings} empty={t("noSnapshotWarnings")} /></div>
      </div>
    </section>
  );
}

export function ProposalInspection({ proposal }: { proposal: LifecycleTransitionProposalResponse["proposal"] }) {
  const t = useTranslations("lifecycle.inspection");
  const common = useTranslations("common.states");
  return (
    <section className="lifecycle-inspection" aria-labelledby="proposal-inspection-title">
      <div className="section-heading">
        <div><p className="eyebrow">{t("latestResponse")}</p><h2 id="proposal-inspection-title">{t("proposalTitle")}</h2></div>
        <StatusBadge label={t("nonExecuting")} tone="warning" />
      </div>
      <p className="neutral-note">{t("proposalBoundary")}</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>{t("proposalId")}</dt><dd>{proposal.proposal_id}</dd></div>
        <div><dt>{t("schemaVersion")}</dt><dd>{proposal.schema_version}</dd></div>
        <div><dt>{t("sourceState")}</dt><dd><LifecycleStateValue value={proposal.source_snapshot.lifecycle_state} /></dd></div>
        <div><dt>{t("targetState")}</dt><dd><LifecycleStateValue value={proposal.target_state} /></dd></div>
        <div><dt>{t("requestedBy")}</dt><dd>{proposal.requested_by ?? common("notSupplied")}</dd></div>
        <div><dt>{t("requestedTimestamp")}</dt><dd>{proposal.requested_timestamp ? <LocalizedTimestamp value={proposal.requested_timestamp} /> : common("notSupplied")}</dd></div>
        <div><dt>{t("rationale")}</dt><dd>{proposal.rationale}</dd></div>
      </dl>
      <div className="lifecycle-evidence-inspection">
        <h3>{t("evidenceReferences")}</h3>
        {proposal.evidence_references.length === 0 ? <p className="repeatable-empty">{t("noEvidence")}</p> : (
          <ol className="lifecycle-evidence-list">
            {proposal.evidence_references.map((reference, index) => (
              <li key={index}>
                <p className="record-card__meta">{t("reference", { number: index + 1, schema: reference.schema_version })}</p>
                <h4>{reference.label ?? reference.reference_id}</h4>
                <dl className="compact-definitions">
                  <div><dt>{t("type")}</dt><dd>{reference.reference_type}</dd></div>
                  <div><dt>{t("id")}</dt><dd>{reference.reference_id}</dd></div>
                  <div><dt>{t("description")}</dt><dd>{reference.description ?? common("notSupplied")}</dd></div>
                </dl>
              </li>
            ))}
          </ol>
        )}
      </div>
      <div className="lifecycle-record__collections">
        <div><h3>{t("proposalNotes")}</h3><OrderedValues values={proposal.notes} empty={t("noProposalNotes")} /></div>
        <div><h3>{t("proposalWarnings")}</h3><OrderedValues values={proposal.warnings} empty={t("noProposalWarnings")} /></div>
      </div>
    </section>
  );
}

export function ReviewInspection({ response }: { response: LifecycleTransitionReviewResponse }) {
  const t = useTranslations("lifecycle.inspection");
  const common = useTranslations("common.states");
  const record = response.transition_record;
  return (
    <section className="lifecycle-inspection" aria-labelledby="review-inspection-title">
      <div className="section-heading">
        <div><p className="eyebrow">{t("latestResponse")}</p><h2 id="review-inspection-title">{t("reviewTitle")}</h2></div>
        <StatusBadge label={t("governanceEvidence")} tone="neutral" />
      </div>
      <p className="neutral-note">{t("reviewBoundary")}</p>
      <dl className="compact-definitions compact-definitions--jobs">
        <div><dt>{t("transitionRecordId")}</dt><dd>{record.transition_record_id}</dd></div>
        <div><dt>{t("schemaVersion")}</dt><dd>{record.schema_version}</dd></div>
        <div><dt>{t("reviewOutcome")}</dt><dd><ReviewOutcomeValue value={record.review_outcome} /></dd></div>
        <div><dt>{t("reviewedBy")}</dt><dd>{record.reviewed_by ?? common("notSupplied")}</dd></div>
        <div><dt>{t("reviewedTimestamp")}</dt><dd>{record.reviewed_timestamp ? <LocalizedTimestamp value={record.reviewed_timestamp} /> : common("notSupplied")}</dd></div>
        <div><dt>{t("rationale")}</dt><dd>{record.rationale}</dd></div>
      </dl>
      <div className="lifecycle-record__collections">
        <div><h3>{t("reviewNotes")}</h3><OrderedValues values={record.notes} empty={t("noReviewNotes")} /></div>
        <div><h3>{t("reviewWarnings")}</h3><OrderedValues values={record.warnings} empty={t("noReviewWarnings")} /></div>
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
  const t = useTranslations("lifecycle.inspection");
  const record = review?.transition_record ?? null;
  return (
    <section className="lifecycle-inspection" aria-labelledby="lifecycle-timeline-title">
      <div className="section-heading">
        <div><p className="eyebrow">{t("timelineEyebrow")}</p><h2 id="lifecycle-timeline-title">{t("timelineTitle")}</h2></div>
      </div>
      <p className="neutral-note">{t("timelineBoundary")}</p>
      <ol className="lifecycle-timeline">
        <li><span>1</span><div><p className="record-card__meta">{t("sourceSnapshot")}</p><h3>{proposal.source_snapshot.snapshot_id}</h3><p>{t("sourceEvent", { state: proposal.source_snapshot.lifecycle_state })}</p><LifecycleStateValue value={proposal.source_snapshot.lifecycle_state} /></div></li>
        <li><span>2</span><div><p className="record-card__meta">{t("proposal")}</p><h3>{proposal.proposal_id}</h3><p>{t("proposalEvent", { state: proposal.target_state })}</p><LifecycleStateValue value={proposal.target_state} /></div></li>
        {record ? <li><span>3</span><div><p className="record-card__meta">{t("reviewRecord")}</p><h3>{record.transition_record_id}</h3><p>{t("reviewEvent", { outcome: record.review_outcome })}</p><ReviewOutcomeValue value={record.review_outcome} /></div></li> : null}
        {record?.resulting_snapshot ? <li><span>4</span><div><p className="record-card__meta">{t("resultingSnapshot")}</p><h3>{record.resulting_snapshot.snapshot_id}</h3><p>{t("resultingEvent", { state: record.resulting_snapshot.lifecycle_state })}</p><LifecycleStateValue value={record.resulting_snapshot.lifecycle_state} /></div></li> : null}
      </ol>
    </section>
  );
}
