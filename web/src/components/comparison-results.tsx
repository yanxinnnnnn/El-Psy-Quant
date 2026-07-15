import Link from "next/link";

import { RequestId } from "@/components/data-states";
import type { PaperJobResultResponse } from "@/lib/api-client";
import { comparisonResultErrorTitle, type ComparisonFailure } from "@/lib/comparisons";

export type ComparisonResultSlot =
  | Readonly<{ jobId: string; status: "loading" }>
  | Readonly<{
      jobId: string;
      status: "success";
      result: PaperJobResultResponse;
      requestId: string | null;
    }>
  | Readonly<{ jobId: string; status: "error"; error: ComparisonFailure }>;

type SuccessfulSlot = Extract<ComparisonResultSlot, { status: "success" }>;
type PaperPosition = PaperJobResultResponse["artifact"]["starting_account_state"]["positions"][number];
type PaperPositionChange = PaperJobResultResponse["artifact"]["session_summary"]["position_changes"][number];

function valueFor(
  slot: ComparisonResultSlot,
  read: (result: PaperJobResultResponse) => string | number,
): string | number {
  if (slot.status === "success") {
    return read(slot.result);
  }
  return slot.status === "loading" ? "Loading" : "Unavailable";
}

function ComparisonMatrix({
  caption,
  slots,
  rows,
}: {
  caption: string;
  slots: readonly ComparisonResultSlot[];
  rows: readonly Readonly<{
    label: string;
    read: (result: PaperJobResultResponse) => string | number;
  }>[];
}) {
  return (
    <div className="table-scroll comparison-matrix">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Backend field</th>
            {slots.map((slot, index) => (
              <th scope="col" key={`${slot.jobId}-${index}`}>
                {index + 1}: {slot.jobId}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              {slots.map((slot, index) => (
                <td key={`${slot.jobId}-${row.label}-${index}`}>
                  {valueFor(slot, row.read)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const accountRows = [
  { label: "Starting account timestamp", read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.timestamp },
  { label: "Starting account starting cash", read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.starting_cash },
  { label: "Starting account current cash", read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.current_cash },
  { label: "Ending account timestamp", read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.timestamp },
  { label: "Ending account starting cash", read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.starting_cash },
  { label: "Ending account current cash", read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.current_cash },
] as const;

const sessionRows = [
  { label: "Session start", read: (result: PaperJobResultResponse) => result.artifact.session_summary.session_start_timestamp },
  { label: "Session end", read: (result: PaperJobResultResponse) => result.artifact.session_summary.session_end_timestamp },
  { label: "Starting cash", read: (result: PaperJobResultResponse) => result.artifact.session_summary.starting_cash },
  { label: "Ending cash", read: (result: PaperJobResultResponse) => result.artifact.session_summary.ending_cash },
  { label: "Cash change", read: (result: PaperJobResultResponse) => result.artifact.session_summary.cash_change },
  { label: "Order count", read: (result: PaperJobResultResponse) => result.artifact.session_summary.order_count },
  { label: "Fill count", read: (result: PaperJobResultResponse) => result.artifact.session_summary.fill_count },
] as const;

const auditRows = [
  { label: "Audit schema", read: (result: PaperJobResultResponse) => result.result_summary.audit.schema_version },
  { label: "Audit created", read: (result: PaperJobResultResponse) => result.result_summary.audit.created_timestamp },
  { label: "Session start", read: (result: PaperJobResultResponse) => result.result_summary.audit.session_start_timestamp },
  { label: "Session end", read: (result: PaperJobResultResponse) => result.result_summary.audit.session_end_timestamp },
  { label: "Starting cash", read: (result: PaperJobResultResponse) => result.result_summary.audit.starting_cash },
  { label: "Ending cash", read: (result: PaperJobResultResponse) => result.result_summary.audit.ending_cash },
  { label: "Cash change", read: (result: PaperJobResultResponse) => result.result_summary.audit.cash_change },
  { label: "Order count", read: (result: PaperJobResultResponse) => result.result_summary.audit.order_count },
  { label: "Fill count", read: (result: PaperJobResultResponse) => result.result_summary.audit.fill_count },
  { label: "Starting position count", read: (result: PaperJobResultResponse) => result.result_summary.audit.starting_position_count },
  { label: "Ending position count", read: (result: PaperJobResultResponse) => result.result_summary.audit.ending_position_count },
  { label: "Position change count", read: (result: PaperJobResultResponse) => result.result_summary.audit.position_change_count },
] as const;

function SlotSourceLinks({ jobId }: { jobId: string }) {
  const encodedJobId = encodeURIComponent(jobId);
  return (
    <div className="record-card__actions">
      <Link className="primary-link" href={`/portfolio-records/${encodedJobId}`}>
        Open Portfolio Record for selected job {jobId}
      </Link>
      <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
        Open Paper Job for selected job {jobId}
      </Link>
    </div>
  );
}

function ResultIdentity({ slot, position }: { slot: SuccessfulSlot; position: number }) {
  const { result } = slot;
  const { artifact, result_reference: reference, result_summary: summary } = result;
  return (
    <article className="comparison-run-card">
      <p className="eyebrow">Comparison position {position}</p>
      <h3>{result.run_id}</h3>
      <p className="identity-line">{result.job_id}</p>
      <dl className="compact-definitions">
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
        <div><dt>Audit schema</dt><dd>{summary.audit.schema_version}</dd></div>
        <div><dt>Audit created</dt><dd>{summary.audit.created_timestamp}</dd></div>
      </dl>
      <SlotSourceLinks jobId={slot.jobId} />
    </article>
  );
}

function PositionTable({
  caption,
  positions,
}: {
  caption: string;
  positions: readonly PaperPosition[];
}) {
  if (positions.length === 0) {
    return <p className="reference-empty">{caption}: the result request succeeded and returned no rows.</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th scope="col">Row</th><th scope="col">Symbol</th><th scope="col">Quantity</th></tr></thead>
        <tbody>
          {positions.map((position, index) => (
            <tr key={`${position.symbol}-${position.quantity}-${index}`}>
              <th scope="row">{index + 1}</th><td>{position.symbol}</td><td>{position.quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PositionChangeTable({
  caption,
  changes,
}: {
  caption: string;
  changes: readonly PaperPositionChange[];
}) {
  if (changes.length === 0) {
    return <p className="reference-empty">{caption}: the result request succeeded and returned no rows.</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th scope="col">Row</th><th scope="col">Symbol</th><th scope="col">Starting quantity</th><th scope="col">Ending quantity</th><th scope="col">Quantity change</th></tr></thead>
        <tbody>
          {changes.map((change, index) => (
            <tr key={`${change.symbol}-${change.starting_quantity}-${change.ending_quantity}-${change.quantity_change}-${index}`}>
              <th scope="row">{index + 1}</th><td>{change.symbol}</td><td>{change.starting_quantity}</td><td>{change.ending_quantity}</td><td>{change.quantity_change}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RunPositions({ slot, position }: { slot: SuccessfulSlot; position: number }) {
  const { result } = slot;
  const session = result.artifact.session_summary;
  return (
    <section className="comparison-position-run" aria-labelledby={`comparison-positions-${position}`}>
      <h3 id={`comparison-positions-${position}`}>Run {position}: {result.run_id}</h3>
      <p className="identity-line">{result.job_id}</p>
      <PositionTable caption={`Run ${position} artifact starting positions in exact API order`} positions={result.artifact.starting_account_state.positions} />
      <PositionTable caption={`Run ${position} artifact ending positions in exact API order`} positions={result.artifact.ending_account_state.positions} />
      <PositionTable caption={`Run ${position} session-summary starting positions in exact API order`} positions={session.starting_positions} />
      <PositionTable caption={`Run ${position} session-summary ending positions in exact API order`} positions={session.ending_positions} />
      <PositionChangeTable caption={`Run ${position} session-summary position changes in exact API order`} changes={session.position_changes} />
    </section>
  );
}

export function ComparisonResults({
  slots,
  onRetry,
  onRefresh,
}: {
  slots: readonly ComparisonResultSlot[];
  onRetry: (index: number) => void;
  onRefresh: () => void;
}) {
  return (
    <section className="comparison-results" aria-labelledby="comparison-results-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Applied URL comparison set</p>
          <h2 id="comparison-results-title">Backend-provided facts side by side</h2>
        </div>
        <button className="secondary-button" type="button" onClick={onRefresh}>
          Refresh comparison
        </button>
      </div>
      <p className="neutral-note">
        This workspace preserves explicit selected order and displays authoritative backend facts. It does not calculate cross-run deltas, rank runs, or select a winner.
      </p>

      <div className="comparison-run-grid" aria-label="Selected result identity and provenance">
        {slots.map((slot, index) => {
          if (slot.status === "success") {
            return <ResultIdentity key={`${slot.jobId}-${index}`} slot={slot} position={index + 1} />;
          }
          if (slot.status === "loading") {
            return (
              <article className="comparison-run-card" aria-busy="true" key={`${slot.jobId}-${index}`}>
                <p className="eyebrow">Comparison position {index + 1}</p>
                <h3>Loading selected result</h3>
                <p className="identity-line">{slot.jobId}</p>
                <SlotSourceLinks jobId={slot.jobId} />
              </article>
            );
          }
          return (
            <article className="comparison-run-card comparison-run-card--error" role="alert" key={`${slot.jobId}-${index}`}>
              <p className="eyebrow">Comparison position {index + 1} unavailable</p>
              <h3>{comparisonResultErrorTitle(slot.error.code)}</h3>
              <p className="identity-line">{slot.jobId}</p>
              <p>{slot.error.message}</p>
              <RequestId value={slot.error.requestId} />
              <button className="retry-button" type="button" onClick={() => onRetry(index)}>
                Retry result for {slot.jobId}
              </button>
              <SlotSourceLinks jobId={slot.jobId} />
            </article>
          );
        })}
      </div>

      <section className="content-panel" aria-labelledby="comparison-account-title">
        <p className="eyebrow">Account cash only</p>
        <h2 id="comparison-account-title">Account and cash snapshot matrix</h2>
        <p className="neutral-note">Account cash is not total marked-to-market equity.</p>
        <ComparisonMatrix caption="Backend account and cash snapshots in selected order" slots={slots} rows={accountRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-session-title">
        <p className="eyebrow">Returned session facts</p>
        <h2 id="comparison-session-title">Backend session-summary matrix</h2>
        <ComparisonMatrix caption="Backend session summaries in selected order" slots={slots} rows={sessionRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-audit-title">
        <p className="eyebrow">Separate validated audit</p>
        <h2 id="comparison-audit-title">Backend result-audit matrix</h2>
        <p className="neutral-note">Audit and session values are displayed independently and are not reconciled in the browser.</p>
        <ComparisonMatrix caption="Backend result audits in selected order" slots={slots} rows={auditRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-positions-title">
        <p className="eyebrow">No symbol alignment or aggregation</p>
        <h2 id="comparison-positions-title">Ordered positions and backend-provided changes</h2>
        {slots.map((slot, index) => slot.status === "success" ? (
          <RunPositions key={`${slot.jobId}-${index}`} slot={slot} position={index + 1} />
        ) : null)}
      </section>
    </section>
  );
}
