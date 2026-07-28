"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import { fetchTradingCalendarDetail } from "@/lib/api-client";
import { isIsoDate } from "@/lib/market-time";
import { useApiResource } from "@/lib/use-api-resource";

type Filters = {
  startDate: string | null;
  endDate: string | null;
  sessionType: string | null;
};

export function TradingCalendarDetailView({
  calendarId,
}: {
  calendarId: string;
}) {
  const t = useTranslations("marketTime.calendarDetail");
  const [draftStart, setDraftStart] = useState("");
  const [draftEnd, setDraftEnd] = useState("");
  const [draftType, setDraftType] = useState("");
  const [filters, setFilters] = useState<Filters>({
    startDate: null,
    endDate: null,
    sessionType: null,
  });
  const [validationError, setValidationError] = useState<string | null>(null);
  const request = useCallback(
    () => fetchTradingCalendarDetail(calendarId, filters),
    [calendarId, filters],
  );
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <div className="back-links">
        <Link className="text-link" href="/market-time">{t("back")}</Link>
      </div>
      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="market_time.calendar.detail"
          entityLabel="calendar_id"
          entityId={calendarId}
          onRetry={state.code === "market_time_not_found" ? undefined : retry}
          backHref="/market-time"
          backLabel={t("return")}
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">{t("eyebrow")}</p>
            <h1>{state.data.calendar.market}</h1>
            <p className="identity-line"><code>{state.data.calendar.id}</code></p>
          </header>
          <aside className="boundary-note" aria-label={t("authorityTitle")}>
            <strong>{t("authorityTitle")}</strong>
            <p>{t("authority")}</p>
          </aside>
          <section className="content-panel" aria-labelledby="calendar-identity-title">
            <p className="eyebrow">{t("identityEyebrow")}</p>
            <h2 id="calendar-identity-title">{t("identityTitle")}</h2>
            <dl className="definition-grid definition-grid--wide">
              <div><dt>{t("market")}</dt><dd>{state.data.calendar.market}</dd></div>
              <div><dt>{t("timezone")}</dt><dd>{state.data.calendar.timezone}</dd></div>
              <div><dt>{t("version")}</dt><dd>{state.data.calendar.calendar_version}</dd></div>
              <div><dt>{t("created")}</dt><dd><LocalizedTimestamp value={state.data.calendar.created_at} /></dd></div>
              <div><dt>{t("schemaVersion")}</dt><dd>{state.data.calendar.schema_version}</dd></div>
            </dl>
          </section>
          <section className="content-panel" aria-labelledby="calendar-sessions-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("sessionsEyebrow")}</p>
                <h2 id="calendar-sessions-title">{t("sessionsTitle")}</h2>
              </div>
              <p>{t("sessionsBoundary")}</p>
            </div>
            <form
              className="filter-bar market-time-filter"
              aria-label={t("filtersAria")}
              onSubmit={(event) => {
                event.preventDefault();
                if (
                  (draftStart !== "" && !isIsoDate(draftStart)) ||
                  (draftEnd !== "" && !isIsoDate(draftEnd)) ||
                  (draftStart !== "" && draftEnd !== "" && draftStart > draftEnd)
                ) {
                  setValidationError(t("invalidDates"));
                  return;
                }
                const normalizedType = draftType.trim();
                setDraftType(normalizedType);
                setValidationError(null);
                setFilters({
                  startDate: draftStart || null,
                  endDate: draftEnd || null,
                  sessionType: normalizedType || null,
                });
              }}
            >
              <label>
                {t("startDate")}
                <input
                  type="date"
                  value={draftStart}
                  onChange={(event) => setDraftStart(event.target.value)}
                />
              </label>
              <label>
                {t("endDate")}
                <input
                  type="date"
                  value={draftEnd}
                  onChange={(event) => setDraftEnd(event.target.value)}
                />
              </label>
              <label>
                {t("sessionType")}
                <input
                  value={draftType}
                  onChange={(event) => setDraftType(event.target.value)}
                  placeholder={t("sessionTypePlaceholder")}
                />
              </label>
              <button className="secondary-button" type="submit">{t("apply")}</button>
              <button className="secondary-button" type="button" onClick={retry}>
                {t("refresh")}
              </button>
            </form>
            {validationError ? (
              <p className="field-error" role="alert">{validationError}</p>
            ) : null}
            {state.data.sessions.length === 0 ? (
              <EmptyState title={t("emptyTitle")} message={t("emptyMessage")} />
            ) : (
              <ScrollableTable caption={t("tableCaption")}>
                <thead>
                  <tr>
                    <th scope="col">{t("sessionId")}</th>
                    <th scope="col">{t("tradingDate")}</th>
                    <th scope="col">{t("openTime")}</th>
                    <th scope="col">{t("closeTime")}</th>
                    <th scope="col">{t("sessionType")}</th>
                    <th scope="col">{t("schemaVersion")}</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.sessions.map((session, index) => (
                    <tr key={`${session.id}-${index}`}>
                      <td><code>{session.id}</code></td>
                      <td><code>{session.trading_date}</code></td>
                      <td><LocalizedTimestamp value={session.open_time} /></td>
                      <td><LocalizedTimestamp value={session.close_time} /></td>
                      <td><code>{session.session_type}</code></td>
                      <td>{session.schema_version}</td>
                    </tr>
                  ))}
                </tbody>
              </ScrollableTable>
            )}
          </section>
        </article>
      )}
    </div>
  );
}
