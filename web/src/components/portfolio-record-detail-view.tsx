"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { LocalizedNumber, LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import { useErrorPresentation } from "@/i18n/errors";
import {
  fetchPaperJobResult,
  type PaperJobResultResponse,
} from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

type PaperPosition = PaperJobResultResponse["artifact"]["starting_account_state"]["positions"][number];
type PaperPositionChange = PaperJobResultResponse["artifact"]["session_summary"]["position_changes"][number];

function PositionTable({
  caption,
  positions,
  emptyMessage,
}: {
  caption: string;
  positions: readonly PaperPosition[];
  emptyMessage: string;
}) {
  const t = useTranslations("portfolioRecords.detail");
  if (positions.length === 0) {
    return <p className="reference-empty">{emptyMessage}</p>;
  }
  return (
    <ScrollableTable caption={caption}>
        <thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("quantity")}</th></tr></thead>
        <tbody>
          {positions.map((position, index) => (
            <tr key={`${position.symbol}-${position.quantity}-${index}`}>
              <th scope="row">{index + 1}</th>
              <td>{position.symbol}</td>
              <td><LocalizedNumber value={position.quantity} /></td>
            </tr>
          ))}
        </tbody>
    </ScrollableTable>
  );
}

function PositionChangeTable({ changes }: { changes: readonly PaperPositionChange[] }) {
  const t = useTranslations("portfolioRecords.detail");
  if (changes.length === 0) {
    return <p className="reference-empty">{t("noChanges")}</p>;
  }
  return (
    <ScrollableTable caption={t("changesCaption")}>
        <thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("startingQuantity")}</th><th scope="col">{t("endingQuantity")}</th><th scope="col">{t("quantityChange")}</th></tr></thead>
        <tbody>
          {changes.map((change, index) => (
            <tr key={`${change.symbol}-${change.starting_quantity}-${change.ending_quantity}-${change.quantity_change}-${index}`}>
              <th scope="row">{index + 1}</th>
              <td>{change.symbol}</td>
              <td><LocalizedNumber value={change.starting_quantity} /></td>
              <td><LocalizedNumber value={change.ending_quantity} /></td>
              <td><LocalizedNumber value={change.quantity_change} /></td>
            </tr>
          ))}
        </tbody>
    </ScrollableTable>
  );
}

function ResultContent({ result }: { result: PaperJobResultResponse }) {
  const t = useTranslations("portfolioRecords.detail");
  const common = useTranslations("common.states");
  const { artifact, result_reference: reference, result_summary: summary } = result;
  const { session_summary: session } = artifact;
  const encodedJobId = encodeURIComponent(result.job_id);

  return (
    <article>
      <div className="back-links">
        <Link className="text-link" href="/portfolio-records">{t("back")}</Link>
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>{t("openJob", { jobId: result.job_id })}</Link>
      </div>

      <header className="page-heading page-heading--detail">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{result.run_id}</h1>
        <p className="identity-line">{result.job_id}</p>
      </header>

      <section className="content-panel" aria-labelledby="result-identity-title">
        <p className="eyebrow">{t("identityEyebrow")}</p>
        <h2 id="result-identity-title">{t("identityTitle")}</h2>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{t("jobId")}</dt><dd>{result.job_id}</dd></div>
          <div><dt>{t("runId")}</dt><dd>{result.run_id}</dd></div>
          <div><dt>{t("recordSchema")}</dt><dd>{reference.record_schema_version}</dd></div>
          <div><dt>{t("rootType")}</dt><dd>{reference.root_type}</dd></div>
          <div><dt>{t("artifactSchemaReference")}</dt><dd>{reference.artifact_schema_version}</dd></div>
          <div><dt>{t("summarySchemaReference")}</dt><dd>{reference.result_summary_schema_version}</dd></div>
          <div><dt>{t("referenceCreated")}</dt><dd><LocalizedTimestamp value={reference.created_timestamp} /></dd></div>
          <div><dt>{t("artifactSchema")}</dt><dd>{artifact.schema_version}</dd></div>
          <div><dt>{t("artifactCreated")}</dt><dd><LocalizedTimestamp value={artifact.created_timestamp} /></dd></div>
          <div><dt>{t("summarySchema")}</dt><dd>{summary.schema_version}</dd></div>
          <div><dt>{t("summaryRunId")}</dt><dd>{summary.run_id}</dd></div>
          <div><dt>{t("requestSchema")}</dt><dd>{summary.request_schema_version}</dd></div>
          <div><dt>{t("requestCreated")}</dt><dd><LocalizedTimestamp value={summary.request_created_timestamp} /></dd></div>
          <div><dt>{t("summaryArtifactSchema")}</dt><dd>{summary.artifact_schema_version}</dd></div>
          <div><dt>{t("summaryArtifactCreated")}</dt><dd><LocalizedTimestamp value={summary.artifact_created_timestamp} /></dd></div>
        </dl>
      </section>

      <section className="content-panel" aria-labelledby="account-cash-title">
        <p className="eyebrow">{t("cashEyebrow")}</p>
        <h2 id="account-cash-title">{t("cashTitle")}</h2>
        <p className="neutral-note">{t("cashBoundary")}</p>
        <div className="account-snapshot-grid">
          <section aria-labelledby="starting-account-title">
            <h3 id="starting-account-title">{t("startingAccount")}</h3>
            <dl className="definition-grid">
              <div><dt>{t("timestamp")}</dt><dd><LocalizedTimestamp value={artifact.starting_account_state.timestamp} /></dd></div>
              <div><dt>{t("accountStartingCash")}</dt><dd><LocalizedNumber value={artifact.starting_account_state.starting_cash} /></dd></div>
              <div><dt>{t("accountCurrentCash")}</dt><dd><LocalizedNumber value={artifact.starting_account_state.current_cash} /></dd></div>
            </dl>
          </section>
          <section aria-labelledby="ending-account-title">
            <h3 id="ending-account-title">{t("endingAccount")}</h3>
            <dl className="definition-grid">
              <div><dt>{t("timestamp")}</dt><dd><LocalizedTimestamp value={artifact.ending_account_state.timestamp} /></dd></div>
              <div><dt>{t("accountStartingCash")}</dt><dd><LocalizedNumber value={artifact.ending_account_state.starting_cash} /></dd></div>
              <div><dt>{t("accountCurrentCash")}</dt><dd><LocalizedNumber value={artifact.ending_account_state.current_cash} /></dd></div>
            </dl>
          </section>
        </div>
        <section className="subsection" aria-labelledby="session-summary-title">
          <h3 id="session-summary-title">{t("sessionTitle")}</h3>
          <dl className="definition-grid definition-grid--wide">
            <div><dt>{t("sessionStart")}</dt><dd><LocalizedTimestamp value={session.session_start_timestamp} /></dd></div>
            <div><dt>{t("sessionEnd")}</dt><dd><LocalizedTimestamp value={session.session_end_timestamp} /></dd></div>
            <div><dt>{t("startingCash")}</dt><dd><LocalizedNumber value={session.starting_cash} /></dd></div>
            <div><dt>{t("endingCash")}</dt><dd><LocalizedNumber value={session.ending_cash} /></dd></div>
            <div><dt>{t("cashChange")}</dt><dd><LocalizedNumber value={session.cash_change} /></dd></div>
            <div><dt>{t("orderCount")}</dt><dd>{session.order_count}</dd></div>
            <div><dt>{t("fillCount")}</dt><dd>{session.fill_count}</dd></div>
          </dl>
          <p className="neutral-note">{t("sessionBoundary")}</p>
        </section>
      </section>

      <section className="content-panel" aria-labelledby="positions-title">
        <p className="eyebrow">{t("positionsEyebrow")}</p>
        <h2 id="positions-title">{t("positionsTitle")}</h2>
        <PositionTable
          caption={t("startingPositionsCaption")}
          positions={artifact.starting_account_state.positions}
          emptyMessage={t("noStartingPositions")}
        />
        <PositionTable
          caption={t("endingPositionsCaption")}
          positions={artifact.ending_account_state.positions}
          emptyMessage={t("noEndingPositions")}
        />
        <PositionTable
          caption={t("sessionStartingCaption")}
          positions={session.starting_positions}
          emptyMessage={t("noSessionStarting")}
        />
        <PositionTable
          caption={t("sessionEndingCaption")}
          positions={session.ending_positions}
          emptyMessage={t("noSessionEnding")}
        />
      </section>

      <section className="content-panel" aria-labelledby="position-changes-title">
        <p className="eyebrow">{t("changesEyebrow")}</p>
        <h2 id="position-changes-title">{t("changesTitle")}</h2>
        <PositionChangeTable changes={session.position_changes} />
      </section>

      <section className="content-panel" aria-labelledby="orders-title">
        <p className="eyebrow">{t("artifactOrderEyebrow")}</p>
        <h2 id="orders-title">{t("ordersTitle")}</h2>
        {artifact.orders.length === 0 ? (
          <p className="reference-empty">{t("noOrders")}</p>
        ) : (
          <ScrollableTable caption={t("ordersCaption")}><thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("orderId")}</th><th scope="col">{t("timestamp")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("side")}</th><th scope="col">{t("quantity")}</th><th scope="col">{t("status")}</th></tr></thead><tbody>{artifact.orders.map((order, index) => <tr key={`${order.order_id}-${index}`}><th scope="row">{index + 1}</th><td>{order.order_id}</td><td><LocalizedTimestamp value={order.timestamp} /></td><td>{order.symbol}</td><td>{order.side}</td><td><LocalizedNumber value={order.quantity} /></td><td>{order.status}</td></tr>)}</tbody></ScrollableTable>
        )}
      </section>

      <section className="content-panel" aria-labelledby="fills-title">
        <p className="eyebrow">{t("artifactOrderEyebrow")}</p>
        <h2 id="fills-title">{t("fillsTitle")}</h2>
        {artifact.fills.length === 0 ? (
          <p className="reference-empty">{t("noFills")}</p>
        ) : (
          <ScrollableTable caption={t("fillsCaption")}><thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("timestamp")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("side")}</th><th scope="col">{t("quantity")}</th><th scope="col">{t("price")}</th><th scope="col">{t("orderId")}</th></tr></thead><tbody>{artifact.fills.map((fill, index) => <tr key={`${fill.timestamp}-${fill.symbol}-${fill.order_id ?? "none"}-${index}`}><th scope="row">{index + 1}</th><td><LocalizedTimestamp value={fill.timestamp} /></td><td>{fill.symbol}</td><td>{fill.side}</td><td><LocalizedNumber value={fill.quantity} /></td><td><LocalizedNumber value={fill.price} /></td><td>{fill.order_id ?? common("notAvailable")}</td></tr>)}</tbody></ScrollableTable>
        )}
      </section>

      <section className="content-panel" aria-labelledby="audit-title">
        <p className="eyebrow">{t("auditEyebrow")}</p>
        <h2 id="audit-title">{t("auditTitle")}</h2>
        <p className="neutral-note">{t("auditBoundary")}</p>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{t("auditSchema")}</dt><dd>{summary.audit.schema_version}</dd></div>
          <div><dt>{t("auditCreated")}</dt><dd><LocalizedTimestamp value={summary.audit.created_timestamp} /></dd></div>
          <div><dt>{t("sessionStart")}</dt><dd><LocalizedTimestamp value={summary.audit.session_start_timestamp} /></dd></div>
          <div><dt>{t("sessionEnd")}</dt><dd><LocalizedTimestamp value={summary.audit.session_end_timestamp} /></dd></div>
          <div><dt>{t("startingCash")}</dt><dd><LocalizedNumber value={summary.audit.starting_cash} /></dd></div>
          <div><dt>{t("endingCash")}</dt><dd><LocalizedNumber value={summary.audit.ending_cash} /></dd></div>
          <div><dt>{t("cashChange")}</dt><dd><LocalizedNumber value={summary.audit.cash_change} /></dd></div>
          <div><dt>{t("orderCount")}</dt><dd>{summary.audit.order_count}</dd></div>
          <div><dt>{t("fillCount")}</dt><dd>{summary.audit.fill_count}</dd></div>
          <div><dt>{t("startingPositionCount")}</dt><dd>{summary.audit.starting_position_count}</dd></div>
          <div><dt>{t("endingPositionCount")}</dt><dd>{summary.audit.ending_position_count}</dd></div>
          <div><dt>{t("positionChangeCount")}</dt><dd>{summary.audit.position_change_count}</dd></div>
        </dl>
      </section>
      <section className="related-panel" aria-labelledby="portfolio-comparison-next-title">
        <div><p className="eyebrow">{t("relatedEyebrow")}</p><h2 id="portfolio-comparison-next-title">{t("relatedTitle")}</h2><p>{t("relatedDescription")}</p></div>
        <Link className="primary-link" href="/comparisons">{t("chooseComparison")}</Link>
      </section>
    </article>
  );
}

export function PortfolioRecordDetailView({ jobId }: { jobId: string }) {
  const t = useTranslations("portfolioRecords.detail");
  const request = useCallback(() => fetchPaperJobResult(jobId), [jobId]);
  const { state, retry } = useApiResource(request);
  const error = useErrorPresentation(state.status === "error" ? state.code : null);
  const notFound = state.status === "error" && state.code === "paper_job_not_found";

  return (
    <div className="business-workspace">
      {state.status === "loading" ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailableTitle") : error.title}
          message={state.message}
          requestId={state.requestId}
          onRetry={notFound ? undefined : retry}
          backHref="/portfolio-records"
          backLabel={t("return")}
        />
      ) : (
        <ResultContent result={state.data} />
      )}
    </div>
  );
}
