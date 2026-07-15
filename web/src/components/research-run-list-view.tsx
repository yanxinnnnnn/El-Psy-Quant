"use client";

import Link from "next/link";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchResearchRuns } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

function errorTitle(code: string): string {
  if (code === "research_artifact_root_unavailable") {
    return "Research root unavailable";
  }
  if (code === "research_artifact_invalid") {
    return "Research artifacts are invalid";
  }
  return "Research runs unavailable";
}

export function ResearchRunListView() {
  const request = useCallback(() => fetchResearchRuns(), []);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <header className="page-heading">
        <p className="eyebrow">Research · Configured artifact root</p>
        <h1>Saved research runs</h1>
        <p>
          Browse configured manifests in backend order. An unavailable or invalid artifact
          root is reported as an error, not an empty result.
        </p>
      </header>

      {state.status === "loading" ? (
        <LoadingState message="Loading configured research-run manifests…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={errorTitle(state.code)}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.runs.length === 0 ? (
        <EmptyState
          title="The configured research root is empty"
          message="The backend reached the configured root successfully and found no supported runs."
        />
      ) : (
        <ul className="card-list" aria-label="Saved research runs">
          {state.data.runs.map((run) => (
            <li className="record-card" key={`${run.experiment_slug}/${run.run_id}`}>
              <div>
                <p className="record-card__meta">
                  {run.experiment_slug} / {run.run_id}
                </p>
                <h2>{run.experiment_name}</h2>
                <dl className="compact-definitions">
                  <div>
                    <dt>Strategy</dt>
                    <dd>{run.strategy}</dd>
                  </div>
                  <div>
                    <dt>Data source</dt>
                    <dd>{run.data_source}</dd>
                  </div>
                  <div>
                    <dt>Symbols</dt>
                    <dd>{run.symbols.join(", ")}</dd>
                  </div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/research-runs/${encodeURIComponent(run.experiment_slug)}/${encodeURIComponent(run.run_id)}`}
              >
                Inspect saved result
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
