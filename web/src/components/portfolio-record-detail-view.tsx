"use client";

import Link from "next/link";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import {
  fetchPaperJobResult,
  type PaperJobResultResponse,
} from "@/lib/api-client";
import { portfolioRecordErrorTitle } from "@/lib/portfolio-records";
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
  if (positions.length === 0) {
    return <p className="reference-empty">{emptyMessage}</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th scope="col">Row</th><th scope="col">Symbol</th><th scope="col">Quantity</th></tr></thead>
        <tbody>
          {positions.map((position, index) => (
            <tr key={`${position.symbol}-${position.quantity}-${index}`}>
              <th scope="row">{index + 1}</th>
              <td>{position.symbol}</td>
              <td>{position.quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PositionChangeTable({ changes }: { changes: readonly PaperPositionChange[] }) {
  if (changes.length === 0) {
    return <p className="reference-empty">The result request succeeded. No position changes were returned.</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>Position changes in exact API order</caption>
        <thead><tr><th scope="col">Row</th><th scope="col">Symbol</th><th scope="col">Starting quantity</th><th scope="col">Ending quantity</th><th scope="col">Quantity change</th></tr></thead>
        <tbody>
          {changes.map((change, index) => (
            <tr key={`${change.symbol}-${change.starting_quantity}-${change.ending_quantity}-${change.quantity_change}-${index}`}>
              <th scope="row">{index + 1}</th>
              <td>{change.symbol}</td>
              <td>{change.starting_quantity}</td>
              <td>{change.ending_quantity}</td>
              <td>{change.quantity_change}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ResultContent({ result }: { result: PaperJobResultResponse }) {
  const { artifact, result_reference: reference, result_summary: summary } = result;
  const { session_summary: session } = artifact;
  const encodedJobId = encodeURIComponent(result.job_id);

  return (
    <article>
      <div className="back-links">
        <Link className="text-link" href="/portfolio-records">← Back to portfolio records</Link>
        <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>Open paper job {result.job_id}</Link>
      </div>

      <header className="page-heading page-heading--detail">
        <p className="eyebrow">Portfolio record · Authoritative completed result</p>
        <h1>{result.run_id}</h1>
        <p className="identity-line">{result.job_id}</p>
      </header>

      <section className="content-panel" aria-labelledby="result-identity-title">
        <p className="eyebrow">Path-free backend response</p>
        <h2 id="result-identity-title">Identity and result reference</h2>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>Job ID</dt><dd>{result.job_id}</dd></div>
          <div><dt>Run ID</dt><dd>{result.run_id}</dd></div>
          <div><dt>Reference record schema</dt><dd>{reference.record_schema_version}</dd></div>
          <div><dt>Reference root type</dt><dd>{reference.root_type}</dd></div>
          <div><dt>Reference artifact schema</dt><dd>{reference.artifact_schema_version}</dd></div>
          <div><dt>Reference result-summary schema</dt><dd>{reference.result_summary_schema_version}</dd></div>
          <div><dt>Reference created</dt><dd>{reference.created_timestamp}</dd></div>
          <div><dt>Artifact schema</dt><dd>{artifact.schema_version}</dd></div>
          <div><dt>Artifact created</dt><dd>{artifact.created_timestamp}</dd></div>
          <div><dt>Result-summary schema</dt><dd>{summary.schema_version}</dd></div>
          <div><dt>Result-summary run ID</dt><dd>{summary.run_id}</dd></div>
          <div><dt>Request schema</dt><dd>{summary.request_schema_version}</dd></div>
          <div><dt>Request created</dt><dd>{summary.request_created_timestamp}</dd></div>
          <div><dt>Summary artifact schema</dt><dd>{summary.artifact_schema_version}</dd></div>
          <div><dt>Summary artifact created</dt><dd>{summary.artifact_created_timestamp}</dd></div>
        </dl>
      </section>

      <section className="content-panel" aria-labelledby="account-cash-title">
        <p className="eyebrow">Cash fields supplied by the API</p>
        <h2 id="account-cash-title">Account and cash snapshots</h2>
        <p className="neutral-note">
          Account cash is not calculated total marked-to-market equity. Total marked-to-market
          equity and equity history are not present in this API response.
        </p>
        <div className="account-snapshot-grid">
          <section aria-labelledby="starting-account-title">
            <h3 id="starting-account-title">Starting account state</h3>
            <dl className="definition-grid">
              <div><dt>Timestamp</dt><dd>{artifact.starting_account_state.timestamp}</dd></div>
              <div><dt>Account starting cash</dt><dd>{artifact.starting_account_state.starting_cash}</dd></div>
              <div><dt>Account current cash</dt><dd>{artifact.starting_account_state.current_cash}</dd></div>
            </dl>
          </section>
          <section aria-labelledby="ending-account-title">
            <h3 id="ending-account-title">Ending account state</h3>
            <dl className="definition-grid">
              <div><dt>Timestamp</dt><dd>{artifact.ending_account_state.timestamp}</dd></div>
              <div><dt>Account starting cash</dt><dd>{artifact.ending_account_state.starting_cash}</dd></div>
              <div><dt>Account current cash</dt><dd>{artifact.ending_account_state.current_cash}</dd></div>
            </dl>
          </section>
        </div>
        <section className="subsection" aria-labelledby="session-summary-title">
          <h3 id="session-summary-title">Backend session summary</h3>
          <dl className="definition-grid definition-grid--wide">
            <div><dt>Session start</dt><dd>{session.session_start_timestamp}</dd></div>
            <div><dt>Session end</dt><dd>{session.session_end_timestamp}</dd></div>
            <div><dt>Starting cash</dt><dd>{session.starting_cash}</dd></div>
            <div><dt>Ending cash</dt><dd>{session.ending_cash}</dd></div>
            <div><dt>Cash change</dt><dd>{session.cash_change}</dd></div>
            <div><dt>Order count</dt><dd>{session.order_count}</dd></div>
            <div><dt>Fill count</dt><dd>{session.fill_count}</dd></div>
          </dl>
          <p className="neutral-note">Changes and counts above are backend-provided and are not recomputed by this workspace.</p>
        </section>
      </section>

      <section className="content-panel" aria-labelledby="positions-title">
        <p className="eyebrow">Ordered quantity records</p>
        <h2 id="positions-title">Positions</h2>
        <PositionTable
          caption="Starting account positions in exact API order"
          positions={artifact.starting_account_state.positions}
          emptyMessage="The result request succeeded. No starting account positions were returned."
        />
        <PositionTable
          caption="Ending account positions in exact API order"
          positions={artifact.ending_account_state.positions}
          emptyMessage="The result request succeeded. No ending account positions were returned."
        />
        <PositionTable
          caption="Session-summary starting positions in exact API order"
          positions={session.starting_positions}
          emptyMessage="The result request succeeded. No session-summary starting positions were returned."
        />
        <PositionTable
          caption="Session-summary ending positions in exact API order"
          positions={session.ending_positions}
          emptyMessage="The result request succeeded. No session-summary ending positions were returned."
        />
      </section>

      <section className="content-panel" aria-labelledby="position-changes-title">
        <p className="eyebrow">Backend-provided changes</p>
        <h2 id="position-changes-title">Position changes</h2>
        <PositionChangeTable changes={session.position_changes} />
      </section>

      <section className="content-panel" aria-labelledby="orders-title">
        <p className="eyebrow">Authoritative artifact order</p>
        <h2 id="orders-title">Orders</h2>
        {artifact.orders.length === 0 ? (
          <p className="reference-empty">The result request succeeded. No orders were returned.</p>
        ) : (
          <div className="table-scroll"><table><caption>Orders in exact API order</caption><thead><tr><th scope="col">Row</th><th scope="col">Order ID</th><th scope="col">Timestamp</th><th scope="col">Symbol</th><th scope="col">Side</th><th scope="col">Quantity</th><th scope="col">Status</th></tr></thead><tbody>{artifact.orders.map((order, index) => <tr key={`${order.order_id}-${index}`}><th scope="row">{index + 1}</th><td>{order.order_id}</td><td>{order.timestamp}</td><td>{order.symbol}</td><td>{order.side}</td><td>{order.quantity}</td><td>{order.status}</td></tr>)}</tbody></table></div>
        )}
      </section>

      <section className="content-panel" aria-labelledby="fills-title">
        <p className="eyebrow">Authoritative artifact order</p>
        <h2 id="fills-title">Fills</h2>
        {artifact.fills.length === 0 ? (
          <p className="reference-empty">The result request succeeded. No fills were returned.</p>
        ) : (
          <div className="table-scroll"><table><caption>Fills in exact API order</caption><thead><tr><th scope="col">Row</th><th scope="col">Timestamp</th><th scope="col">Symbol</th><th scope="col">Side</th><th scope="col">Quantity</th><th scope="col">Price</th><th scope="col">Order ID</th></tr></thead><tbody>{artifact.fills.map((fill, index) => <tr key={`${fill.timestamp}-${fill.symbol}-${fill.order_id ?? "none"}-${index}`}><th scope="row">{index + 1}</th><td>{fill.timestamp}</td><td>{fill.symbol}</td><td>{fill.side}</td><td>{fill.quantity}</td><td>{fill.price}</td><td>{fill.order_id ?? "Not available"}</td></tr>)}</tbody></table></div>
        )}
      </section>

      <section className="content-panel" aria-labelledby="audit-title">
        <p className="eyebrow">Validated backend record</p>
        <h2 id="audit-title">Backend result audit</h2>
        <p className="neutral-note">The backend cross-validates the authoritative artifact and result summary before returning this response. This workspace displays the returned audit without merging it with the session summary.</p>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>Audit schema</dt><dd>{summary.audit.schema_version}</dd></div>
          <div><dt>Audit created</dt><dd>{summary.audit.created_timestamp}</dd></div>
          <div><dt>Session start</dt><dd>{summary.audit.session_start_timestamp}</dd></div>
          <div><dt>Session end</dt><dd>{summary.audit.session_end_timestamp}</dd></div>
          <div><dt>Starting cash</dt><dd>{summary.audit.starting_cash}</dd></div>
          <div><dt>Ending cash</dt><dd>{summary.audit.ending_cash}</dd></div>
          <div><dt>Cash change</dt><dd>{summary.audit.cash_change}</dd></div>
          <div><dt>Order count</dt><dd>{summary.audit.order_count}</dd></div>
          <div><dt>Fill count</dt><dd>{summary.audit.fill_count}</dd></div>
          <div><dt>Starting position count</dt><dd>{summary.audit.starting_position_count}</dd></div>
          <div><dt>Ending position count</dt><dd>{summary.audit.ending_position_count}</dd></div>
          <div><dt>Position change count</dt><dd>{summary.audit.position_change_count}</dd></div>
        </dl>
      </section>
      <section className="related-panel" aria-labelledby="portfolio-comparison-next-title">
        <div><p className="eyebrow">Your next review choice</p><h2 id="portfolio-comparison-next-title">Compare this result with other available records</h2><p>Select comparison candidates explicitly; the workspace does not rank or recommend an outcome.</p></div>
        <Link className="primary-link" href="/comparisons">Choose comparison results</Link>
      </section>
    </article>
  );
}

export function PortfolioRecordDetailView({ jobId }: { jobId: string }) {
  const request = useCallback(() => fetchPaperJobResult(jobId), [jobId]);
  const { state, retry } = useApiResource(request);
  const notFound = state.status === "error" && state.code === "paper_job_not_found";

  return (
    <div className="business-workspace">
      {state.status === "loading" ? (
        <LoadingState message="Loading the authoritative paper result…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={portfolioRecordErrorTitle(state.code)}
          message={state.message}
          requestId={state.requestId}
          onRetry={notFound ? undefined : retry}
          backHref="/portfolio-records"
          backLabel="Return to portfolio records"
        />
      ) : (
        <ResultContent result={state.data} />
      )}
    </div>
  );
}
