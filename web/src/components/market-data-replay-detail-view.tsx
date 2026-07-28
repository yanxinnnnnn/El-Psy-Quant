"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { ReplayStatusValue } from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import {
  fetchMarketDataReplayDetail,
  type MarketDataReplayDetailResponse,
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

function ReplayLifecycle({ status }: { status: ReplayStatus }) {
  const t = useTranslations("marketTime.replayDetail");
  return (
    <ol className="replay-lifecycle" aria-label={t("lifecycleAria")}>
      {replayStatuses.map((candidate) => (
        <li
          className={candidate === status ? "replay-lifecycle__current" : undefined}
          key={candidate}
          aria-current={candidate === status ? "step" : undefined}
        >
          <ReplayStatusValue value={candidate} />
        </li>
      ))}
    </ol>
  );
}

function EventTimeline({
  detail,
}: {
  detail: MarketDataReplayDetailResponse;
}) {
  const t = useTranslations("marketTime.replayDetail");
  if (detail.events.length === 0) {
    return <p className="neutral-note">{t("noEvents")}</p>;
  }
  return (
    <ol className="timeline-list" aria-label={t("eventsAria")}>
      {detail.events.map((event, index) => (
        <li className="timeline-card" key={`${event.event_id}-${index}`}>
          <header>
            <div>
              <p className="eyebrow">{t("eventPosition", { position: index + 1 })}</p>
              <h3>{event.event_type}</h3>
            </div>
            {event.event_id === detail.session.cursor.last_event_id ? (
              <span className="cursor-marker">{t("cursorMarker")}</span>
            ) : null}
          </header>
          <dl className="definition-grid definition-grid--wide">
            <div><dt>{t("eventId")}</dt><dd><code>{event.event_id}</code></dd></div>
            <div><dt>{t("instrument")}</dt><dd><code>{event.instrument_id}</code></dd></div>
            <div><dt>{t("eventTime")}</dt><dd><LocalizedTimestamp value={event.event_time} /></dd></div>
            <div><dt>{t("source")}</dt><dd><code>{event.source}</code></dd></div>
            <div><dt>{t("schemaVersion")}</dt><dd>{event.schema_version}</dd></div>
          </dl>
          <details className="audit-disclosure">
            <summary>{t("payload")}</summary>
            <pre className="json-evidence">{JSON.stringify(event.payload, null, 2)}</pre>
          </details>
        </li>
      ))}
    </ol>
  );
}

export function MarketDataReplayDetailView({
  replayId,
}: {
  replayId: string;
}) {
  const t = useTranslations("marketTime.replayDetail");
  const common = useTranslations("common.states");
  const request = useCallback(
    () => fetchMarketDataReplayDetail(replayId),
    [replayId],
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
          operation="market_time.replay.detail"
          entityLabel="replay_id"
          entityId={replayId}
          onRetry={state.code === "market_time_not_found" ? undefined : retry}
          backHref="/market-time"
          backLabel={t("return")}
        />
      ) : (
        <article>
          <header className="page-heading page-heading--detail">
            <p className="eyebrow">{t("eyebrow")}</p>
            <h1>{t("title")}</h1>
            <p className="identity-line"><code>{state.data.session.replay_id}</code></p>
          </header>
          <aside className="boundary-note" aria-label={t("authorityTitle")}>
            <strong>{t("authorityTitle")}</strong>
            <p>{t("authority")}</p>
          </aside>
          <section className="content-panel" aria-labelledby="replay-status-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("statusEyebrow")}</p>
                <h2 id="replay-status-title">{t("statusTitle")}</h2>
              </div>
              <ReplayStatusValue value={state.data.session.status} />
            </div>
            <ReplayLifecycle status={state.data.session.status} />
            <p className="neutral-note">{t("lifecycleBoundary")}</p>
          </section>
          <section className="content-panel" aria-labelledby="replay-cursor-title">
            <p className="eyebrow">{t("cursorEyebrow")}</p>
            <h2 id="replay-cursor-title">{t("cursorTitle")}</h2>
            {state.data.event_count > 0 ? (
              <progress
                className="replay-progress"
                aria-label={t("progressAria")}
                value={state.data.session.cursor.position}
                max={state.data.event_count}
              />
            ) : null}
            <dl className="definition-grid definition-grid--wide">
              <div><dt>{t("position")}</dt><dd>{state.data.session.cursor.position}</dd></div>
              <div><dt>{t("eventCount")}</dt><dd>{state.data.event_count}</dd></div>
              <div><dt>{t("lastEvent")}</dt><dd>{state.data.session.cursor.last_event_id ?? common("notAvailable")}</dd></div>
              <div><dt>{t("currentEventTime")}</dt><dd><OptionalTimestamp value={state.data.session.cursor.current_event_time} /></dd></div>
              <div><dt>{t("startTime")}</dt><dd><OptionalTimestamp value={state.data.session.start_time} /></dd></div>
              <div><dt>{t("currentTime")}</dt><dd><OptionalTimestamp value={state.data.session.current_time} /></dd></div>
              <div><dt>{t("streamDigest")}</dt><dd><code>{state.data.session.cursor.event_stream_digest}</code></dd></div>
              <div><dt>{t("sessionSchema")}</dt><dd>{state.data.session.schema_version}</dd></div>
              <div><dt>{t("recordSchema")}</dt><dd>{state.data.record_schema_version}</dd></div>
            </dl>
          </section>
          <section className="content-panel" aria-labelledby="replay-events-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{t("eventsEyebrow")}</p>
                <h2 id="replay-events-title">{t("eventsTitle")}</h2>
              </div>
              <p>{t("eventsBoundary")}</p>
            </div>
            <EventTimeline detail={state.data} />
          </section>
        </article>
      )}
    </div>
  );
}
