"use client";

import Link from "next/link";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { SectionNavigation } from "@/components/section-navigation";
import { fetchStrategies } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

export function StrategyListView() {
  const request = useCallback(() => fetchStrategies(), []);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <SectionNavigation />
      <header className="page-heading">
        <p className="eyebrow">Strategies · Built-in catalog</p>
        <h1>Strategy definitions</h1>
        <p>
          Browse the exact built-in definitions exposed by the backend. Parameter metadata is
          descriptive and no strategy is executed or ranked here.
        </p>
      </header>

      {state.status === "loading" ? (
        <LoadingState message="Loading the built-in strategy catalog…" />
      ) : state.status === "error" ? (
        <ErrorState
          title="Strategy catalog unavailable"
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.strategies.length === 0 ? (
        <EmptyState
          title="No built-in strategies are available"
          message="The backend returned a successful empty catalog."
        />
      ) : (
        <ul className="card-list" aria-label="Built-in strategies">
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
                Inspect {strategy.display_name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
