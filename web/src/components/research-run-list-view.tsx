"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchResearchRuns } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function ResearchRunListView() {
  const t = useTranslations("research.list");
  const request = useCallback(() => fetchResearchRuns(), []);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <header className="page-heading">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </header>

      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={state.code === "research_artifact_root_unavailable" ? t("rootUnavailable") : state.code === "research_artifact_invalid" ? t("invalid") : t("unavailable")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="research_run.list"
          onRetry={retry}
        />
      ) : state.data.runs.length === 0 ? (
        <EmptyState
          title={t("emptyTitle")}
          message={t("emptyMessage")}
        />
      ) : (
        <ul className="card-list" aria-label={t("ariaLabel")}>
          {state.data.runs.map((run) => (
            <li className="record-card" key={`${run.experiment_slug}/${run.run_id}`}>
              <div>
                <p className="record-card__meta">
                  {run.experiment_slug} / {run.run_id}
                </p>
                <h2>{run.experiment_name}</h2>
                <dl className="compact-definitions">
                  <div>
                    <dt>{t("strategy")}</dt>
                    <dd>{run.strategy}</dd>
                  </div>
                  <div>
                    <dt>{t("dataSource")}</dt>
                    <dd>{run.data_source}</dd>
                  </div>
                  <div>
                    <dt>{t("symbols")}</dt>
                    <dd>{run.symbols.join(", ")}</dd>
                  </div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/research-runs/${encodeURIComponent(run.experiment_slug)}/${encodeURIComponent(run.run_id)}`}
              >
                {t("inspect")}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
