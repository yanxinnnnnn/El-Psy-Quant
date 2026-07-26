"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import {
  PaperAccountLifecycleValue,
  PaperAccountProjectionStatusValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import {
  fetchPaperAccounts,
  type PaperAccountLifecycleStatus,
  type PaperAccountListResponse,
} from "@/lib/api-client";
import {
  paperAccountLifecycleStatuses,
  paperAccountLimits,
} from "@/lib/paper-accounts";
import { useApiResource } from "@/lib/use-api-resource";

function AccountCard({
  account,
}: {
  account: PaperAccountListResponse["items"][number];
}) {
  const t = useTranslations("paperAccounts.list");
  const common = useTranslations("paperAccounts.common");
  return (
    <li className="record-card paper-account-card">
      <div>
        <p className="record-card__meta">{account.account_id}</p>
        <h2>{account.display_name}</h2>
        <dl className="compact-definitions">
          <div>
            <dt>{common("baseCurrency")}</dt>
            <dd><code className="raw-value">{account.base_currency}</code></dd>
          </div>
          <div>
            <dt>{common("lifecycleStatus")}</dt>
            <dd><PaperAccountLifecycleValue value={account.lifecycle_status} /></dd>
          </div>
          <div>
            <dt>{common("headVersion")}</dt>
            <dd>{account.head_version}</dd>
          </div>
          <div>
            <dt>{common("projectionStatus")}</dt>
            <dd>
              <PaperAccountProjectionStatusValue value={account.projection_status} />
            </dd>
          </div>
          <div>
            <dt>{common("created")}</dt>
            <dd><LocalizedTimestamp value={account.created_timestamp} /></dd>
          </div>
          <div>
            <dt>{common("updated")}</dt>
            <dd><LocalizedTimestamp value={account.updated_timestamp} /></dd>
          </div>
        </dl>
      </div>
      <Link
        className="primary-link"
        href={`/paper-accounts/${encodeURIComponent(account.account_id)}`}
      >
        {t("inspect")}
      </Link>
    </li>
  );
}

export function PaperAccountListView() {
  const t = useTranslations("paperAccounts.list");
  const statuses = useTranslations("paperAccounts.statuses");
  const common = useTranslations("paperAccounts.common");
  const [draftStatus, setDraftStatus] =
    useState<PaperAccountLifecycleStatus | "all">("all");
  const [draftLimit, setDraftLimit] =
    useState<(typeof paperAccountLimits)[number]>(50);
  const [query, setQuery] = useState<{
    lifecycleStatus: PaperAccountLifecycleStatus | null;
    limit: number;
    cursor: string | null;
  }>({ lifecycleStatus: null, limit: 50, cursor: null });
  const [cursorHistory, setCursorHistory] = useState<(string | null)[]>([]);
  const [retainedPage, setRetainedPage] =
    useState<PaperAccountListResponse | null>(null);
  const request = useCallback(async () => {
    const result = await fetchPaperAccounts(query);
    setRetainedPage(result.data);
    return result;
  }, [query]);
  const { state, retry } = useApiResource(request);
  const page = state.status === "success" ? state.data : retainedPage;
  const refreshPending = state.status === "loading" && page !== null;

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <Link className="primary-link" href="/paper-accounts/new">
          {t("create")}
        </Link>
      </header>

      <aside className="boundary-note" aria-label={common("authorityTitle")}>
        <strong>{common("authorityTitle")}</strong>
        <p>{common("authority")}</p>
      </aside>

      <form
        className="filter-bar"
        aria-label={t("filtersAria")}
        onSubmit={(event) => {
          event.preventDefault();
          setCursorHistory([]);
          setQuery({
            lifecycleStatus: draftStatus === "all" ? null : draftStatus,
            limit: draftLimit,
            cursor: null,
          });
        }}
      >
        <label>
          {t("status")}
          <select
            value={draftStatus}
            onChange={(event) =>
              setDraftStatus(
                event.target.value as PaperAccountLifecycleStatus | "all",
              )
            }
          >
            <option value="all">{t("allStatuses")}</option>
            {paperAccountLifecycleStatuses.map((status) => (
              <option key={status} value={status}>
                {statuses(status)} ({status})
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("limit")}
          <select
            value={draftLimit}
            onChange={(event) =>
              setDraftLimit(
                Number(event.target.value) as
                  (typeof paperAccountLimits)[number],
              )
            }
          >
            {paperAccountLimits.map((limit) => (
              <option key={limit} value={limit}>{limit}</option>
            ))}
          </select>
        </label>
        <button className="secondary-button" type="submit">{t("apply")}</button>
        <button className="secondary-button" type="button" onClick={retry}>
          {t("refresh")}
        </button>
      </form>

      {refreshPending ? (
        <p className="neutral-note" role="status">{common("refreshing")}</p>
      ) : null}
      {state.status === "loading" && page === null ? (
        <LoadingState message={t("loading")} />
      ) : null}
      {state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="paper_account.list"
          onRetry={retry}
        />
      ) : null}
      {page && page.items.length === 0 ? (
        <EmptyState title={t("emptyTitle")} message={t("emptyMessage")} />
      ) : null}
      {page && page.items.length > 0 ? (
        <ol className="card-list" aria-label={t("ariaLabel")}>
          {page.items.map((account, index) => (
            <AccountCard
              key={`${account.account_id}-${index}`}
              account={account}
            />
          ))}
        </ol>
      ) : null}
      {page ? (
        <nav className="pagination-actions" aria-label={t("paginationAria")}>
          <button
            className="secondary-button"
            type="button"
            disabled={cursorHistory.length === 0 || refreshPending}
            onClick={() => {
              const previous = cursorHistory[cursorHistory.length - 1] ?? null;
              setCursorHistory((current) => current.slice(0, -1));
              setQuery((current) => ({ ...current, cursor: previous }));
            }}
          >
            {t("previous")}
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={page.next_cursor === null || refreshPending}
            onClick={() => {
              if (page.next_cursor === null) return;
              setCursorHistory((current) => [...current, query.cursor]);
              setQuery((current) => ({
                ...current,
                cursor: page.next_cursor,
              }));
            }}
          >
            {t("next")}
          </button>
        </nav>
      ) : null}
    </div>
  );
}
