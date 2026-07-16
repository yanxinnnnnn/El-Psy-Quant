"use client";

import Link from "next/link";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchResearchRunDetail } from "@/lib/api-client";
import { formatNumber, formatPercentage } from "@/lib/formatters";
import { useApiResource } from "@/lib/use-api-resource";

export function ResearchRunDetailView({
  experimentSlug,
  runId,
}: {
  experimentSlug: string;
  runId: string;
}) {
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
          ← Back to research runs
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message="Loading the selected manifest and saved metrics…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={
            state.code === "research_run_not_found"
              ? "Research run not found"
              : "Research result unavailable"
          }
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "research_run_not_found" ? undefined : retry}
          backHref="/research-runs"
          backLabel="Return to research runs"
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">Saved research result</p>
            <h1>{state.data.experiment_name}</h1>
            <p className="identity-line">
              {state.data.experiment_slug} / {state.data.run_id}
            </p>
            <div className="detail-actions">
              <Link
                className="text-link"
                href={`/strategies/${encodeURIComponent(state.data.strategy)}`}
              >
                Strategy: {state.data.strategy}
              </Link>
            </div>
          </header>

          <div className="detail-grid">
            <section className="content-panel" aria-labelledby="run-identity-title">
              <p className="eyebrow">Manifest identity</p>
              <h2 id="run-identity-title">Run definition</h2>
              <dl className="definition-grid">
                <div><dt>Data source</dt><dd>{state.data.data.source}</dd></div>
                <div><dt>Symbols</dt><dd>{state.data.data.symbols.join(", ")}</dd></div>
                <div><dt>Manifest schema</dt><dd>{state.data.manifest_schema_version}</dd></div>
                <div><dt>Metrics schema</dt><dd>{state.data.metrics_schema_version}</dd></div>
              </dl>
            </section>

            <section className="content-panel" aria-labelledby="evaluation-title">
              <p className="eyebrow">Backend-owned settings</p>
              <h2 id="evaluation-title">Evaluation</h2>
              <dl className="definition-grid">
                <div>
                  <dt>Periods per year</dt>
                  <dd>{formatNumber(state.data.evaluation.periods_per_year)}</dd>
                </div>
                <div>
                  <dt>Annual risk-free rate</dt>
                  <dd>{formatPercentage(state.data.evaluation.annual_risk_free_rate)}</dd>
                </div>
              </dl>
            </section>
          </div>

          <section className="content-panel" aria-labelledby="run-parameters-title">
            <p className="eyebrow">Backend-owned settings</p>
            <h2 id="run-parameters-title">Strategy parameters</h2>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>Fast window</dt><dd>{formatNumber(state.data.parameters.fast_window)}</dd></div>
              <div><dt>Slow window</dt><dd>{formatNumber(state.data.parameters.slow_window)}</dd></div>
              <div><dt>Initial capital</dt><dd>{formatNumber(state.data.parameters.initial_capital)}</dd></div>
              <div><dt>Transaction cost rate</dt><dd>{formatPercentage(state.data.parameters.transaction_cost_rate)}</dd></div>
              <div><dt>Slippage rate</dt><dd>{formatPercentage(state.data.parameters.slippage_rate)}</dd></div>
            </dl>
          </section>

          <section className="content-panel" aria-labelledby="artifact-references-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Read-only references</p>
                <h2 id="artifact-references-title">Artifacts</h2>
              </div>
              <p>References are displayed as bounded text and are not downloadable links.</p>
            </div>
            <dl className="artifact-list">
              <div><dt>Config</dt><dd><code>{state.data.artifacts.config}</code></dd></div>
              <div><dt>Metadata</dt><dd><code>{state.data.artifacts.metadata}</code></dd></div>
              <div><dt>Summary</dt><dd><code>{state.data.artifacts.summary}</code></dd></div>
              <div><dt>Metrics</dt><dd><code>{state.data.artifacts.metrics}</code></dd></div>
              <div><dt>Logs directory</dt><dd><code>{state.data.artifacts.logs_dir}</code></dd></div>
            </dl>
          </section>

          <section className="content-panel" aria-labelledby="saved-metrics-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Saved values · API order</p>
                <h2 id="saved-metrics-title">Per-symbol metrics</h2>
              </div>
              <p>Displayed from the saved artifact without recomputation or aggregation.</p>
            </div>
            <div className="table-scroll">
              <table>
                <caption>Saved per-symbol metrics for {state.data.experiment_name}</caption>
                <thead>
                  <tr>
                    <th scope="col">Symbol</th>
                    <th scope="col">Initial equity</th>
                    <th scope="col">Final equity</th>
                    <th scope="col">Total return</th>
                    <th scope="col">Maximum drawdown</th>
                    <th scope="col">Periods</th>
                    <th scope="col">CAGR</th>
                    <th scope="col">Annualized volatility</th>
                    <th scope="col">Sharpe ratio</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.metrics.map((metric, index) => (
                    <tr key={`${metric.symbol}-${index}`}>
                      <th scope="row">{metric.symbol}</th>
                      <td>{formatNumber(metric.initial_equity)}</td>
                      <td>{formatNumber(metric.final_equity)}</td>
                      <td>{formatPercentage(metric.total_return)}</td>
                      <td>{formatPercentage(metric.max_drawdown)}</td>
                      <td>{formatNumber(metric.periods)}</td>
                      <td>{formatPercentage(metric.cagr)}</td>
                      <td>{formatPercentage(metric.annualized_volatility)}</td>
                      <td>{formatNumber(metric.sharpe_ratio)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="related-panel" aria-labelledby="research-evidence-next-title">
            <div>
              <p className="eyebrow">Your next review choice</p>
              <h2 id="research-evidence-next-title">Inspect governance or report evidence</h2>
              <p>Choose a saved evidence manifest explicitly. This generic research page does not infer that unrelated records are connected.</p>
            </div>
            <Link className="primary-link" href="/evidence-manifests">Browse evidence manifests</Link>
          </section>
        </article>
      )}
    </div>
  );
}
