"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { ReplayStatusValue } from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import {
  fetchMarketDataReplays,
  fetchTradingCalendars,
  type ReplayStatus,
} from "@/lib/api-client";
import { replayStatuses } from "@/lib/market-time";
import { useApiResource } from "@/lib/use-api-resource";

function OptionalTimestamp({ value }: { value: string | null }) {
  const common = useTranslations("common.states");
  return value === null
    ? <>{common("notAvailable")}</>
    : <LocalizedTimestamp value={value} />;
}

function ReplayCollection() {
  const t = useTranslations("marketTime.replays");
  const common = useTranslations("marketTime.common");
  const statuses = useTranslations("marketTime.statuses");
  const [draftStatus, setDraftStatus] = useState<ReplayStatus | "all">("all");
  const [status, setStatus] = useState<ReplayStatus | null>(null);
  const request = useCallback(
    () => fetchMarketDataReplays({ status }),
    [status],
  );
  const { state, retry } = useApiResource(request);

  return (
    <section className="content-panel" aria-labelledby="replay-collection-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h2 id="replay-collection-title">{t("title")}</h2>
        </div>
        <p>{t("description")}</p>
      </div>
      <form
        className="filter-bar market-time-filter"
        aria-label={t("filtersAria")}
        onSubmit={(event) => {
          event.preventDefault();
          setStatus(draftStatus === "all" ? null : draftStatus);
        }}
      >
        <label>
          {t("status")}
          <select
            value={draftStatus}
            onChange={(event) =>
              setDraftStatus(event.target.value as ReplayStatus | "all")
            }
          >
            <option value="all">{t("allStatuses")}</option>
            {replayStatuses.map((value) => (
              <option key={value} value={value}>
                {statuses(value)} ({value})
              </option>
            ))}
          </select>
        </label>
        <button className="secondary-button" type="submit">{t("apply")}</button>
        <button className="secondary-button" type="button" onClick={retry}>
          {common("refresh")}
        </button>
      </form>
      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="market_time.replay.list"
          onRetry={retry}
        />
      ) : state.data.length === 0 ? (
        <EmptyState title={t("emptyTitle")} message={t("emptyMessage")} />
      ) : (
        <ol className="card-list" aria-label={t("ariaLabel")}>
          {state.data.map((replay) => (
            <li className="record-card" key={replay.replay_id}>
              <div>
                <p className="record-card__meta">
                  <code className="raw-value">{replay.replay_id}</code>
                </p>
                <h3><ReplayStatusValue value={replay.status} /></h3>
                <dl className="compact-definitions">
                  <div>
                    <dt>{t("cursorPosition")}</dt>
                    <dd>{replay.cursor.position}</dd>
                  </div>
                  <div>
                    <dt>{t("currentTime")}</dt>
                    <dd><OptionalTimestamp value={replay.current_time} /></dd>
                  </div>
                  <div>
                    <dt>{t("lastEvent")}</dt>
                    <dd>{replay.cursor.last_event_id ?? common("notAvailable")}</dd>
                  </div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/market-time/replays/${encodeURIComponent(replay.replay_id)}`}
              >
                {t("inspect")}
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function CalendarCollection() {
  const t = useTranslations("marketTime.calendars");
  const common = useTranslations("marketTime.common");
  const [draftMarket, setDraftMarket] = useState("");
  const [market, setMarket] = useState<string | null>(null);
  const request = useCallback(
    () => fetchTradingCalendars({ market }),
    [market],
  );
  const { state, retry } = useApiResource(request);

  return (
    <section className="content-panel" aria-labelledby="calendar-collection-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h2 id="calendar-collection-title">{t("title")}</h2>
        </div>
        <p>{t("description")}</p>
      </div>
      <form
        className="filter-bar market-time-filter"
        aria-label={t("filtersAria")}
        onSubmit={(event) => {
          event.preventDefault();
          const normalized = draftMarket.trim();
          setDraftMarket(normalized);
          setMarket(normalized.length === 0 ? null : normalized);
        }}
      >
        <label>
          {t("market")}
          <input
            value={draftMarket}
            onChange={(event) => setDraftMarket(event.target.value)}
            placeholder={t("marketPlaceholder")}
          />
        </label>
        <button className="secondary-button" type="submit">{t("apply")}</button>
        <button className="secondary-button" type="button" onClick={retry}>
          {common("refresh")}
        </button>
      </form>
      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="market_time.calendar.list"
          onRetry={retry}
        />
      ) : state.data.length === 0 ? (
        <EmptyState title={t("emptyTitle")} message={t("emptyMessage")} />
      ) : (
        <ol className="card-list" aria-label={t("ariaLabel")}>
          {state.data.map((calendar) => (
            <li className="record-card" key={calendar.id}>
              <div>
                <p className="record-card__meta">
                  <code className="raw-value">{calendar.id}</code>
                </p>
                <h3>{calendar.market}</h3>
                <dl className="compact-definitions">
                  <div><dt>{t("timezone")}</dt><dd>{calendar.timezone}</dd></div>
                  <div><dt>{t("version")}</dt><dd>{calendar.calendar_version}</dd></div>
                  <div>
                    <dt>{t("created")}</dt>
                    <dd><LocalizedTimestamp value={calendar.created_at} /></dd>
                  </div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/market-time/calendars/${encodeURIComponent(calendar.id)}`}
              >
                {t("inspect")}
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export function MarketTimeWorkspace() {
  const t = useTranslations("marketTime.workspace");
  const common = useTranslations("marketTime.common");
  return (
    <div className="business-workspace">
      <header className="page-heading">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </header>
      <aside className="boundary-note" aria-label={common("authorityTitle")}>
        <strong>{common("authorityTitle")}</strong>
        <p>{common("authority")}</p>
      </aside>
      <div className="market-time-collections">
        <ReplayCollection />
        <CalendarCollection />
      </div>
    </div>
  );
}
