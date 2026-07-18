"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchStrategies } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function StrategyListView() {
  const t = useTranslations("strategies.list");
  const request = useCallback(() => fetchStrategies(), []);
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
          title={t("errorTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="strategy.list"
          onRetry={retry}
        />
      ) : state.data.strategies.length === 0 ? (
        <EmptyState
          title={t("emptyTitle")}
          message={t("emptyMessage")}
        />
      ) : (
        <ul className="card-list" aria-label={t("ariaLabel")}>
          {state.data.strategies.map((strategy) => (
            <li className="record-card" key={strategy.name}>
              <div>
                <p className="record-card__meta">{strategy.name}</p>
                <h2>{strategy.display_name}</h2>
                <p>{strategy.description}</p>
              </div>
              <Link
                className="primary-link"
                href={`/strategies/${encodeURIComponent(strategy.name)}`}
              >
                {t("inspect", { displayName: strategy.display_name })}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
