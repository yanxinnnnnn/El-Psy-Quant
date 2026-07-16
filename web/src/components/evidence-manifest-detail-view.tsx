"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { useErrorPresentation } from "@/i18n/errors";
import {
  fetchEvidenceManifestDetail,
  type EvidenceManifestDetailResponse,
} from "@/lib/api-client";
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
  id,
  references,
}: {
  title: string;
  id: string;
  references: EvidenceReference[];
}) {
  const t = useTranslations("evidence.detail");
  const common = useTranslations("common.states");
  return (
    <section className="content-panel" aria-labelledby={`${id}-title`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("orderedEyebrow")}</p>
          <h2 id={`${id}-title`}>{title}</h2>
        </div>
        <p>{t("orderBoundary")}</p>
      </div>
      {references.length === 0 ? (
        <p className="reference-empty">{t("emptyGroup")}</p>
      ) : (
        <ol className="reference-list">
          {references.map((reference, index) => (
            <li key={index}>
              <dl className="definition-grid definition-grid--wide">
                <div><dt>{t("schemaVersion")}</dt><dd>{reference.schema_version}</dd></div>
                <div><dt>{t("referenceType")}</dt><dd>{reference.reference_type}</dd></div>
                <div><dt>{t("referenceId")}</dt><dd>{reference.reference_id}</dd></div>
                <div><dt>{t("label")}</dt><dd>{reference.label ?? common("notAvailable")}</dd></div>
                <div><dt>{t("description")}</dt><dd>{reference.description ?? common("notAvailable")}</dd></div>
              </dl>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function ManifestReferences({ detail }: { detail: EvidenceManifestDetailResponse }) {
  const t = useTranslations("evidence.detail");
  const common = useTranslations("common.states");
  if (detail.manifest_type === "strategy_decision_manifest") {
    return (
      <>
        <ReferenceGroup id="summary-references" title={t("summaryReferences")} references={detail.summary_references} />
        <ReferenceGroup id="record-references" title={t("recordReferences")} references={detail.record_references} />
      </>
    );
  }
  if (detail.manifest_type === "report_artifact_manifest") {
    return (
      <>
        <section className="content-panel" aria-labelledby="report-fields-title">
          <p className="eyebrow">{t("reportEyebrow")}</p>
          <h2 id="report-fields-title">{t("reportTitle")}</h2>
          <dl className="definition-grid">
            <div><dt>{t("label")}</dt><dd>{detail.label ?? common("notAvailable")}</dd></div>
            <div><dt>{t("notes")}</dt><dd>{detail.notes ?? common("notAvailable")}</dd></div>
          </dl>
        </section>
        <ReferenceGroup id="references" title={t("references")} references={detail.references} />
      </>
    );
  }
  return (
    <>
      <ReferenceGroup
        id="state-snapshot-references"
        title={t("stateSnapshotReferences")}
        references={detail.state_snapshot_references}
      />
      <ReferenceGroup
        id="transition-proposal-references"
        title={t("proposalReferences")}
        references={detail.transition_proposal_references}
      />
      <ReferenceGroup
        id="transition-record-references"
        title={t("recordTransitionReferences")}
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
  const t = useTranslations("evidence.detail");
  const typeT = useTranslations("evidence.types");
  const common = useTranslations("common.states");
  const request = useCallback(
    () => fetchEvidenceManifestDetail(manifestType, artifactKey),
    [manifestType, artifactKey],
  );
  const { state, retry } = useApiResource(request);
  const error = useErrorPresentation(state.status === "error" ? state.code : null);

  return (
    <div className="business-workspace">
      <div className="back-links">
        <Link className="text-link" href="/evidence-manifests">
          {t("back")}
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailableTitle") : error.title}
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "evidence_manifest_not_found" ? undefined : retry}
          backHref="/evidence-manifests"
          backLabel={t("return")}
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">{t("eyebrow")}</p>
            <h1>{state.data.manifest_type === "strategy_decision_manifest" ? typeT("strategyDecision") : state.data.manifest_type === "report_artifact_manifest" ? typeT("reportArtifact") : typeT("strategyReviewWorkflow")}</h1>
            <p className="identity-line">
              {state.data.manifest_type} / {state.data.artifact_key}
            </p>
          </header>

          <section className="content-panel" aria-labelledby="manifest-identity-title">
            <p className="eyebrow">{t("identityEyebrow")}</p>
            <h2 id="manifest-identity-title">{t("metadataTitle")}</h2>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>{t("manifestType")}</dt><dd>{state.data.manifest_type}</dd></div>
              <div><dt>{t("artifactKey")}</dt><dd>{state.data.artifact_key}</dd></div>
              <div><dt>{t("schemaVersion")}</dt><dd>{state.data.schema_version}</dd></div>
              <div><dt>{t("manifestId")}</dt><dd>{state.data.manifest_id}</dd></div>
              <div><dt>{t("createdBy")}</dt><dd>{state.data.created_by ?? common("notAvailable")}</dd></div>
              <div><dt>{t("created")}</dt><dd>{state.data.created_timestamp ?? common("notAvailable")}</dd></div>
              <div><dt>{t("description")}</dt><dd>{state.data.description ?? common("notAvailable")}</dd></div>
            </dl>
          </section>

          <ManifestReferences detail={state.data} />

          <section className="related-panel" aria-labelledby="evidence-paper-next-title">
            <div>
              <p className="eyebrow">{t("relatedEyebrow")}</p>
              <h2 id="evidence-paper-next-title">{t("relatedTitle")}</h2>
              <p>{t("relatedDescription")}</p>
            </div>
            <Link className="primary-link" href="/paper-jobs">{t("browsePaperJobs")}</Link>
          </section>
        </article>
      )}
    </div>
  );
}
