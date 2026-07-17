"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import { fetchStrategyDetail } from "@/lib/api-client";
import { formatDefault } from "@/lib/formatters";
import { parseLocale } from "@/i18n/config";
import { useApiResource } from "@/lib/use-api-resource";

export function StrategyDetailView({ strategyName }: { strategyName: string }) {
  const t = useTranslations("strategies.detail");
  const locale = parseLocale(useLocale()) ?? "en";
  const request = useCallback(() => fetchStrategyDetail(strategyName), [strategyName]);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <div className="back-links">
        <Link className="text-link" href="/strategies">
          {t("back")}
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={state.code === "not_found" ? t("notFound") : t("unavailable")}
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "not_found" ? undefined : retry}
          backHref="/strategies"
          backLabel={t("return")}
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">{t("eyebrow")}</p>
            <h1>{state.data.display_name}</h1>
            <p className="identity-line">{t("exactName", { name: state.data.name })}</p>
            <p>{state.data.description}</p>
          </header>

          <section className="content-panel" aria-labelledby="strategy-parameters-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("metadataEyebrow")}</p>
                <h2 id="strategy-parameters-title">{t("parametersTitle")}</h2>
              </div>
              <p>{t("parametersBoundary")}</p>
            </div>
            <ScrollableTable caption={t("caption", { displayName: state.data.display_name })}>
                <thead>
                  <tr>
                    <th scope="col">{t("name")}</th>
                    <th scope="col">{t("valueType")}</th>
                    <th scope="col">{t("required")}</th>
                    <th scope="col">{t("defaultValue")}</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.parameters.map((parameter) => (
                    <tr key={parameter.name}>
                      <th scope="row">{parameter.name}</th>
                      <td>{parameter.value_type}</td>
                      <td>{parameter.required ? t("yes") : t("no")}</td>
                      <td>{formatDefault(parameter.default, locale)}</td>
                    </tr>
                  ))}
                </tbody>
            </ScrollableTable>
          </section>

          <section className="related-panel" aria-labelledby="strategy-research-title">
            <div>
              <p className="eyebrow">{t("relatedEyebrow")}</p>
              <h2 id="strategy-research-title">{t("relatedTitle")}</h2>
              <p>{t("relatedDescription")}</p>
            </div>
            <Link className="primary-link" href="/research-runs">
              {t("browseResearch")}
            </Link>
          </section>
        </article>
      )}
    </div>
  );
}
