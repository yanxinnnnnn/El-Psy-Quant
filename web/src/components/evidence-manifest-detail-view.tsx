"use client";

import Link from "next/link";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import {
  fetchEvidenceManifestDetail,
  type EvidenceManifestDetailResponse,
} from "@/lib/api-client";
import {
  evidenceErrorTitle,
  evidenceManifestLabel,
  nullableText,
} from "@/lib/evidence-manifests";
import { useApiResource } from "@/lib/use-api-resource";

type EvidenceReference =
  EvidenceManifestDetailResponse extends infer Detail
    ? Detail extends { manifest_type: string }
      ? Detail extends { summary_references: (infer Reference)[] }
        ? Reference
        : Detail extends { references: (infer Reference)[] }
          ? Reference
          : Detail extends { state_snapshot_references: (infer Reference)[] }
            ? Reference
            : never
      : never
    : never;

function ReferenceGroup({
  title,
  references,
}: {
  title: string;
  references: EvidenceReference[];
}) {
  return (
    <section className="content-panel" aria-labelledby={`${title.replaceAll(" ", "-").toLowerCase()}-title`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ordered unresolved pointers</p>
          <h2 id={`${title.replaceAll(" ", "-").toLowerCase()}-title`}>{title}</h2>
        </div>
        <p>API order and duplicate references are preserved.</p>
      </div>
      {references.length === 0 ? (
        <p className="reference-empty">No references in this group.</p>
      ) : (
        <ol className="reference-list">
          {references.map((reference, index) => (
            <li key={index}>
              <dl className="definition-grid definition-grid--wide">
                <div><dt>Schema version</dt><dd>{reference.schema_version}</dd></div>
                <div><dt>Reference type</dt><dd>{reference.reference_type}</dd></div>
                <div><dt>Reference ID</dt><dd>{reference.reference_id}</dd></div>
                <div><dt>Label</dt><dd>{nullableText(reference.label)}</dd></div>
                <div><dt>Description</dt><dd>{nullableText(reference.description)}</dd></div>
              </dl>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function ManifestReferences({ detail }: { detail: EvidenceManifestDetailResponse }) {
  if (detail.manifest_type === "strategy_decision_manifest") {
    return (
      <>
        <ReferenceGroup title="Summary references" references={detail.summary_references} />
        <ReferenceGroup title="Record references" references={detail.record_references} />
      </>
    );
  }
  if (detail.manifest_type === "report_artifact_manifest") {
    return (
      <>
        <section className="content-panel" aria-labelledby="report-fields-title">
          <p className="eyebrow">Report manifest fields</p>
          <h2 id="report-fields-title">Report details</h2>
          <dl className="definition-grid">
            <div><dt>Label</dt><dd>{nullableText(detail.label)}</dd></div>
            <div><dt>Notes</dt><dd>{nullableText(detail.notes)}</dd></div>
          </dl>
        </section>
        <ReferenceGroup title="References" references={detail.references} />
      </>
    );
  }
  return (
    <>
      <ReferenceGroup
        title="State snapshot references"
        references={detail.state_snapshot_references}
      />
      <ReferenceGroup
        title="Transition proposal references"
        references={detail.transition_proposal_references}
      />
      <ReferenceGroup
        title="Transition record references"
        references={detail.transition_record_references}
      />
    </>
  );
}

export function EvidenceManifestDetailView({
  manifestType,
  artifactKey,
}: {
  manifestType: string;
  artifactKey: string;
}) {
  const request = useCallback(
    () => fetchEvidenceManifestDetail(manifestType, artifactKey),
    [manifestType, artifactKey],
  );
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <div className="back-links">
        <Link className="text-link" href="/evidence-manifests">
          ← Back to evidence manifests
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message="Loading the selected evidence manifest…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={evidenceErrorTitle(state.code)}
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "evidence_manifest_not_found" ? undefined : retry}
          backHref="/evidence-manifests"
          backLabel="Return to evidence manifests"
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">Governance and report evidence</p>
            <h1>{evidenceManifestLabel(state.data.manifest_type)}</h1>
            <p className="identity-line">
              {state.data.manifest_type} / {state.data.artifact_key}
            </p>
          </header>

          <section className="content-panel" aria-labelledby="manifest-identity-title">
            <p className="eyebrow">Manifest identity</p>
            <h2 id="manifest-identity-title">Backend-owned metadata</h2>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>Manifest type</dt><dd>{state.data.manifest_type}</dd></div>
              <div><dt>Artifact key</dt><dd>{state.data.artifact_key}</dd></div>
              <div><dt>Schema version</dt><dd>{state.data.schema_version}</dd></div>
              <div><dt>Manifest ID</dt><dd>{state.data.manifest_id}</dd></div>
              <div><dt>Created by</dt><dd>{nullableText(state.data.created_by)}</dd></div>
              <div><dt>Created</dt><dd>{nullableText(state.data.created_timestamp)}</dd></div>
              <div><dt>Description</dt><dd>{nullableText(state.data.description)}</dd></div>
            </dl>
          </section>

          <ManifestReferences detail={state.data} />
        </article>
      )}
    </div>
  );
}
