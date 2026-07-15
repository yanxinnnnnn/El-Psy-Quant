"use client";

import Link from "next/link";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchStrategyDetail } from "@/lib/api-client";
import { formatDefault } from "@/lib/formatters";
import { useApiResource } from "@/lib/use-api-resource";

export function StrategyDetailView({ strategyName }: { strategyName: string }) {
  const request = useCallback(() => fetchStrategyDetail(strategyName), [strategyName]);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <div className="back-links">
        <Link className="text-link" href="/strategies">
          ← Back to strategies
        </Link>
      </div>

      {state.status === "loading" ? (
        <LoadingState message="Loading the exact strategy definition…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={state.code === "not_found" ? "Strategy not found" : "Strategy unavailable"}
          message={state.message}
          requestId={state.requestId}
          onRetry={state.code === "not_found" ? undefined : retry}
          backHref="/strategies"
          backLabel="Return to strategy list"
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">Strategy definition</p>
            <h1>{state.data.display_name}</h1>
            <p className="identity-line">Exact name: {state.data.name}</p>
            <p>{state.data.description}</p>
          </header>

          <section className="content-panel" aria-labelledby="strategy-parameters-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Descriptive metadata</p>
                <h2 id="strategy-parameters-title">Parameters</h2>
              </div>
              <p>Values remain read-only; backend and domain validation stay authoritative.</p>
            </div>
            <div className="table-scroll">
              <table>
                <caption>Parameter metadata for {state.data.display_name}</caption>
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Value type</th>
                    <th scope="col">Required</th>
                    <th scope="col">Default value</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.parameters.map((parameter) => (
                    <tr key={parameter.name}>
                      <th scope="row">{parameter.name}</th>
                      <td>{parameter.value_type}</td>
                      <td>{parameter.required ? "Yes" : "No"}</td>
                      <td>{formatDefault(parameter.default)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="related-panel" aria-labelledby="strategy-research-title">
            <div>
              <p className="eyebrow">Separate inspection workspace</p>
              <h2 id="strategy-research-title">Review saved research runs</h2>
              <p>Inspect backend-owned manifests and saved metrics without starting a run.</p>
            </div>
            <Link className="primary-link" href="/research-runs">
              Browse research runs
            </Link>
          </section>
        </article>
      )}
    </div>
  );
}
