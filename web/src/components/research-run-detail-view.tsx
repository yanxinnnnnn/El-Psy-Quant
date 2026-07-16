"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { LocalizedNumber } from "@/components/localized-values";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchResearchRunDetail } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function ResearchRunDetailView({
  experimentSlug,
  runId,
}: {
  experimentSlug: string;
  runId: string;
}) {
  const t = useTranslations("research.detail");
  const request = useCallback(
    () => fetchResearchRunDetail(experimentSlug, runId),
    [experimentSlug, runId],
  );
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <div className="back-links">
        <Link className="text-link" href="/research-runs">
          {t("back")}
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={
            state.code === "research_run_not_found"
              ? t("notFound")
              : t("unavailable")
          }
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "research_run_not_found" ? undefined : retry}
          backHref="/research-runs"
          backLabel={t("return")}
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">{t("eyebrow")}</p>
            <h1>{state.data.experiment_name}</h1>
            <p className="identity-line">
              {state.data.experiment_slug} / {state.data.run_id}
            </p>
            <div className="detail-actions">
              <Link
                className="text-link"
                href={`/strategies/${encodeURIComponent(state.data.strategy)}`}
              >
                {t("strategyLink", { strategy: state.data.strategy })}
              </Link>
            </div>
          </header>

          <div className="detail-grid">
            <section className="content-panel" aria-labelledby="run-identity-title">
              <p className="eyebrow">{t("manifestEyebrow")}</p>
              <h2 id="run-identity-title">{t("definitionTitle")}</h2>
              <dl className="definition-grid">
                <div><dt>{t("dataSource")}</dt><dd>{state.data.data.source}</dd></div>
                <div><dt>{t("symbols")}</dt><dd>{state.data.data.symbols.join(", ")}</dd></div>
                <div><dt>{t("manifestSchema")}</dt><dd>{state.data.manifest_schema_version}</dd></div>
                <div><dt>{t("metricsSchema")}</dt><dd>{state.data.metrics_schema_version}</dd></div>
              </dl>
            </section>

            <section className="content-panel" aria-labelledby="evaluation-title">
              <p className="eyebrow">{t("settingsEyebrow")}</p>
              <h2 id="evaluation-title">{t("evaluationTitle")}</h2>
              <dl className="definition-grid">
                <div>
                  <dt>{t("periodsPerYear")}</dt>
                  <dd><LocalizedNumber value={state.data.evaluation.periods_per_year} /></dd>
                </div>
                <div>
                  <dt>{t("riskFreeRate")}</dt>
                  <dd><LocalizedNumber value={state.data.evaluation.annual_risk_free_rate} percentage /></dd>
                </div>
              </dl>
            </section>
          </div>

          <section className="content-panel" aria-labelledby="run-parameters-title">
            <p className="eyebrow">{t("settingsEyebrow")}</p>
            <h2 id="run-parameters-title">{t("parametersTitle")}</h2>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>{t("fastWindow")}</dt><dd><LocalizedNumber value={state.data.parameters.fast_window} /></dd></div>
              <div><dt>{t("slowWindow")}</dt><dd><LocalizedNumber value={state.data.parameters.slow_window} /></dd></div>
              <div><dt>{t("initialCapital")}</dt><dd><LocalizedNumber value={state.data.parameters.initial_capital} /></dd></div>
              <div><dt>{t("transactionCost")}</dt><dd><LocalizedNumber value={state.data.parameters.transaction_cost_rate} percentage /></dd></div>
              <div><dt>{t("slippage")}</dt><dd><LocalizedNumber value={state.data.parameters.slippage_rate} percentage /></dd></div>
            </dl>
          </section>

          <section className="content-panel" aria-labelledby="artifact-references-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("referencesEyebrow")}</p>
                <h2 id="artifact-references-title">{t("artifactsTitle")}</h2>
              </div>
              <p>{t("referencesBoundary")}</p>
            </div>
            <dl className="artifact-list">
              <div><dt>{t("config")}</dt><dd><code>{state.data.artifacts.config}</code></dd></div>
              <div><dt>{t("metadata")}</dt><dd><code>{state.data.artifacts.metadata}</code></dd></div>
              <div><dt>{t("summary")}</dt><dd><code>{state.data.artifacts.summary}</code></dd></div>
              <div><dt>{t("metrics")}</dt><dd><code>{state.data.artifacts.metrics}</code></dd></div>
              <div><dt>{t("logsDirectory")}</dt><dd><code>{state.data.artifacts.logs_dir}</code></dd></div>
            </dl>
          </section>

          <section className="content-panel" aria-labelledby="saved-metrics-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("metricsEyebrow")}</p>
                <h2 id="saved-metrics-title">{t("metricsTitle")}</h2>
              </div>
              <p>{t("metricsBoundary")}</p>
            </div>
            <div className="table-scroll">
              <table>
                <caption>{t("metricsCaption", { experimentName: state.data.experiment_name })}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("symbol")}</th>
                    <th scope="col">{t("initialEquity")}</th>
                    <th scope="col">{t("finalEquity")}</th>
                    <th scope="col">{t("totalReturn")}</th>
                    <th scope="col">{t("maxDrawdown")}</th>
                    <th scope="col">{t("periods")}</th>
                    <th scope="col">{t("cagr")}</th>
                    <th scope="col">{t("volatility")}</th>
                    <th scope="col">{t("sharpe")}</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.metrics.map((metric, index) => (
                    <tr key={`${metric.symbol}-${index}`}>
                      <th scope="row">{metric.symbol}</th>
                      <td><LocalizedNumber value={metric.initial_equity} /></td>
                      <td><LocalizedNumber value={metric.final_equity} /></td>
                      <td><LocalizedNumber value={metric.total_return} percentage /></td>
                      <td><LocalizedNumber value={metric.max_drawdown} percentage /></td>
                      <td><LocalizedNumber value={metric.periods} /></td>
                      <td><LocalizedNumber value={metric.cagr} percentage /></td>
                      <td><LocalizedNumber value={metric.annualized_volatility} percentage /></td>
                      <td><LocalizedNumber value={metric.sharpe_ratio} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="related-panel" aria-labelledby="research-evidence-next-title">
            <div>
              <p className="eyebrow">{t("relatedEyebrow")}</p>
              <h2 id="research-evidence-next-title">{t("relatedTitle")}</h2>
              <p>{t("relatedDescription")}</p>
            </div>
            <Link className="primary-link" href="/evidence-manifests">{t("browseEvidence")}</Link>
          </section>
        </article>
      )}
    </div>
  );
}
