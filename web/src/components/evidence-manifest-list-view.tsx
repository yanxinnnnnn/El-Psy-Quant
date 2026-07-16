"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { useErrorPresentation } from "@/i18n/errors";
import { fetchEvidenceManifests } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function EvidenceManifestListView() {
  const t = useTranslations("evidence");
  const common = useTranslations("common.states");
  const request = useCallback(() => fetchEvidenceManifests(), []);
  const { state, retry } = useApiResource(request);
  const error = useErrorPresentation(state.status === "error" ? state.code : null);

  return (
    <div className="business-workspace">
      <header className="page-heading">
        <p className="eyebrow">{t("list.eyebrow")}</p>
        <h1>{t("list.title")}</h1>
        <p>{t("list.description")}</p>
      </header>

      {state.status === "loading" ? (
        <LoadingState message={t("list.loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("list.unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.manifests.length === 0 ? (
        <EmptyState
          title={t("list.emptyTitle")}
          message={t("list.emptyMessage")}
        />
      ) : (
        <ul className="card-list" aria-label={t("list.ariaLabel")}>
          {state.data.manifests.map((manifest) => (
            <li
              className="record-card"
              key={`${manifest.manifest_type}/${manifest.artifact_key}`}
            >
              <div>
                <p className="record-card__meta">
                  {manifest.manifest_type} / {manifest.artifact_key}
                </p>
                <h2>{manifest.manifest_type === "strategy_decision_manifest" ? t("types.strategyDecision") : manifest.manifest_type === "report_artifact_manifest" ? t("types.reportArtifact") : t("types.strategyReviewWorkflow")}</h2>
                <dl className="compact-definitions compact-definitions--evidence">
                  <div><dt>{t("list.manifestId")}</dt><dd>{manifest.manifest_id}</dd></div>
                  <div><dt>{t("list.references")}</dt><dd>{manifest.reference_count}</dd></div>
                  <div><dt>{t("list.createdBy")}</dt><dd>{manifest.created_by ?? common("notAvailable")}</dd></div>
                  <div><dt>{t("list.created")}</dt><dd>{manifest.created_timestamp ?? common("notAvailable")}</dd></div>
                  <div><dt>{t("list.label")}</dt><dd>{manifest.label ?? common("notAvailable")}</dd></div>
                  <div><dt>{t("list.descriptionLabel")}</dt><dd>{manifest.description ?? common("notAvailable")}</dd></div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/evidence-manifests/${encodeURIComponent(manifest.manifest_type)}/${encodeURIComponent(manifest.artifact_key)}`}
              >
                {t("list.inspect")}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
