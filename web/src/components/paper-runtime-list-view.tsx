"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import {
  ApiClientError,
  fetchPaperRuntimes,
  type PaperRuntimeDesiredState,
  type PaperRuntimeListFilters,
  type PaperRuntimeListResponse,
  type PaperRuntimeObservedState,
} from "@/lib/api-client";

type Failure = Readonly<{ code: string; message: string; requestId: string | null; status: number }>;
const desiredStates: readonly PaperRuntimeDesiredState[] = ["running", "stopped"];
const observedStates: readonly PaperRuntimeObservedState[] = ["ready", "running", "stopped", "completed", "blocked"];

function failure(error: unknown): Failure {
  return error instanceof ApiClientError
    ? { code: error.code, message: error.publicMessage, requestId: error.requestId, status: error.status }
    : { code: "api_unavailable", message: "The local API is unavailable.", requestId: null, status: 0 };
}

export function PaperRuntimeListView() {
  const t = useTranslations("paperRuntimes");
  const [draft, setDraft] = useState({ account_id: "", replay_id: "", trading_session_id: "", desired_state: "", observed_state: "" });
  const [query, setQuery] = useState<PaperRuntimeListFilters>({ limit: 25 });
  const [data, setData] = useState<PaperRuntimeListResponse | null>(null);
  const [error, setError] = useState<Failure | null>(null);
  const [loading, setLoading] = useState(false);
  const sequence = useRef(0);

  const load = useCallback(async (filters: PaperRuntimeListFilters, append: boolean) => {
    const requestSequence = ++sequence.current;
    setLoading(true);
    setError(null);
    try {
      const response = await fetchPaperRuntimes(filters);
      if (requestSequence !== sequence.current) return;
      setData((previous) => append && previous
        ? { ...response.data, items: [...previous.items, ...response.data.items] }
        : response.data);
    } catch (caught) {
      if (requestSequence === sequence.current) setError(failure(caught));
    } finally {
      if (requestSequence === sequence.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load({ limit: 25 }, false);
  }, [load]);

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div><p className="eyebrow">{t("list.eyebrow")}</p><h1>{t("list.title")}</h1><p>{t("list.description")}</p></div>
        <Link className="primary-link" href="/paper-runtimes/new">{t("list.create")}</Link>
      </header>
      <aside className="boundary-note" aria-label={t("common.authorityTitle")}><strong>{t("common.authorityTitle")}</strong><p>{t("common.authority")}</p></aside>
      <form className="filter-bar" aria-label={t("list.filtersAria")} onSubmit={(event) => {
        event.preventDefault();
        const next: PaperRuntimeListFilters = {
          account_id: draft.account_id || null,
          replay_id: draft.replay_id || null,
          trading_session_id: draft.trading_session_id || null,
          desired_state: (draft.desired_state || null) as PaperRuntimeDesiredState | null,
          observed_state: (draft.observed_state || null) as PaperRuntimeObservedState | null,
          limit: 25,
        };
        setQuery(next);
        setData(null);
        void load(next, false);
      }}>
        {(["account_id", "replay_id", "trading_session_id"] as const).map((field) => <label key={field}>{t(`fields.${field}`)}<input value={draft[field]} onChange={(event) => setDraft((current) => ({ ...current, [field]: event.target.value }))} maxLength={512} /></label>)}
        <label>{t("fields.desired_state")}<select value={draft.desired_state} onChange={(event) => setDraft((current) => ({ ...current, desired_state: event.target.value }))}><option value="">{t("list.all")}</option>{desiredStates.map((state) => <option key={state} value={state}>{t(`states.${state}`)} ({state})</option>)}</select></label>
        <label>{t("fields.observed_state")}<select value={draft.observed_state} onChange={(event) => setDraft((current) => ({ ...current, observed_state: event.target.value }))}><option value="">{t("list.all")}</option>{observedStates.map((state) => <option key={state} value={state}>{t(`states.${state}`)} ({state})</option>)}</select></label>
        <button className="secondary-button" type="submit" disabled={loading}>{t("actions.applyFilters")}</button>
      </form>
      {loading && data === null ? <LoadingState message={t("list.loading")} /> : null}
      {error ? <ErrorState title={t("list.errorTitle")} code={error.code} message={error.message} requestId={error.requestId} httpStatus={error.status} operation="paper_runtime.list" onRetry={() => void load(query, false)} /> : null}
      {data?.items.length === 0 ? <EmptyState title={t("list.emptyTitle")} message={t("list.emptyMessage")} /> : null}
      {data && data.items.length > 0 ? <ScrollableTable caption={t("list.caption")}><thead><tr>
        {(["runtime_id", "execution_order_id", "account_id", "replay_id", "trading_session_id", "desired_state", "observed_state", "fencing_token", "owner_id", "row_version", "updated_at", "block_reason_code"] as const).map((field) => <th key={field}>{t(`fields.${field}`)}</th>)}<th>{t("list.inspect")}</th>
      </tr></thead><tbody>{data.items.map((runtime, index) => <tr key={`${runtime.runtime_id}-${index}`}>
        <td><code className="raw-value">{runtime.runtime_id}</code></td><td><code className="raw-value">{runtime.execution_order_id}</code></td><td><code>{runtime.account_id}</code></td><td><code>{runtime.replay_id}</code></td><td><code>{runtime.trading_session_id}</code></td>
        <td><strong>{t("common.requestedState")}</strong><br /><code>{runtime.desired_state}</code></td><td><strong>{t("common.observedRuntime")}</strong><br /><code>{runtime.observed_state}</code></td><td>{runtime.fencing_token}</td><td><code>{runtime.owner_id ?? t("common.unowned")}</code></td><td>{runtime.row_version}</td><td><LocalizedTimestamp value={runtime.updated_at} /></td><td><code>{runtime.block_reason_code ?? t("common.none")}</code></td>
        <td><Link className="text-link" href={`/paper-runtimes/${encodeURIComponent(runtime.runtime_id)}`}>{t("list.inspect")}</Link></td>
      </tr>)}</tbody></ScrollableTable> : null}
      {data?.next_cursor ? <button className="secondary-button" type="button" disabled={loading} onClick={() => {
        const next = { ...query, cursor: data.next_cursor };
        setQuery(next);
        void load(next, true);
      }}>{loading ? t("actions.loadingMore") : t("actions.loadMore")}</button> : null}
    </div>
  );
}
