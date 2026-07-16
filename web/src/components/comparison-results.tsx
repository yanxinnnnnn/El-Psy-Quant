"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { RequestId } from "@/components/data-states";
import { LocalizedNumber, LocalizedTimestamp } from "@/components/localized-values";
import { useErrorPresentation } from "@/i18n/errors";
import type { PaperJobResultResponse } from "@/lib/api-client";
import type { ComparisonFailure } from "@/lib/comparisons";

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

function ComparisonErrorDetail({ error }: { error: ComparisonFailure }) {
  const presentation = useErrorPresentation(error.code);
  const common = useTranslations("common");
  return <><h3>{presentation.title}</h3><p>{presentation.explanation}</p><p>{error.message}</p><p>{presentation.recovery}</p><p className="request-id">{common("errorCode", { code: error.code })}</p></>;
}

function valueFor(
  slot: ComparisonResultSlot,
  read: (result: PaperJobResultResponse) => string | number,
  loading: string,
  unavailable: string,
): ReactNode {
  if (slot.status === "success") {
    const value = read(slot.result);
    if (typeof value === "number") return <LocalizedNumber value={value} />;
    if (/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return <LocalizedTimestamp value={value} />;
    return value;
  }
  return slot.status === "loading" ? loading : unavailable;
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
  const t = useTranslations("comparisons.results");
  return (
    <div className="table-scroll comparison-matrix">
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{t("backendField")}</th>
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
                  {valueFor(slot, row.read, t("loadingValue"), t("unavailableValue"))}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SlotSourceLinks({ jobId }: { jobId: string }) {
  const t = useTranslations("comparisons.results");
  const encodedJobId = encodeURIComponent(jobId);
  return (
    <div className="record-card__actions">
      <Link className="primary-link" href={`/portfolio-records/${encodedJobId}`}>
        {t("openPortfolio", { jobId })}
      </Link>
      <Link className="text-link" href={`/paper-jobs/${encodedJobId}`}>
        {t("openJob", { jobId })}
      </Link>
    </div>
  );
}

function ResultIdentity({ slot, position }: { slot: SuccessfulSlot; position: number }) {
  const t = useTranslations("comparisons.results");
  const { result } = slot;
  const { artifact, result_reference: reference, result_summary: summary } = result;
  return (
    <article className="comparison-run-card">
      <p className="eyebrow">{t("position", { position })}</p>
      <h3>{result.run_id}</h3>
      <p className="identity-line">{result.job_id}</p>
      <dl className="compact-definitions">
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
        <div><dt>{t("auditSchema")}</dt><dd>{summary.audit.schema_version}</dd></div>
        <div><dt>{t("auditCreated")}</dt><dd><LocalizedTimestamp value={summary.audit.created_timestamp} /></dd></div>
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
  const t = useTranslations("comparisons.results");
  if (positions.length === 0) {
    return <p className="reference-empty">{t("emptyRows", { caption })}</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("quantity")}</th></tr></thead>
        <tbody>
          {positions.map((position, index) => (
            <tr key={`${position.symbol}-${position.quantity}-${index}`}>
              <th scope="row">{index + 1}</th><td>{position.symbol}</td><td><LocalizedNumber value={position.quantity} /></td>
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
  const t = useTranslations("comparisons.results");
  if (changes.length === 0) {
    return <p className="reference-empty">{t("emptyRows", { caption })}</p>;
  }
  return (
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th scope="col">{t("row")}</th><th scope="col">{t("symbol")}</th><th scope="col">{t("startingQuantity")}</th><th scope="col">{t("endingQuantity")}</th><th scope="col">{t("quantityChange")}</th></tr></thead>
        <tbody>
          {changes.map((change, index) => (
            <tr key={`${change.symbol}-${change.starting_quantity}-${change.ending_quantity}-${change.quantity_change}-${index}`}>
              <th scope="row">{index + 1}</th><td>{change.symbol}</td><td><LocalizedNumber value={change.starting_quantity} /></td><td><LocalizedNumber value={change.ending_quantity} /></td><td><LocalizedNumber value={change.quantity_change} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RunPositions({ slot, position }: { slot: SuccessfulSlot; position: number }) {
  const t = useTranslations("comparisons.results");
  const { result } = slot;
  const session = result.artifact.session_summary;
  return (
    <section className="comparison-position-run" aria-labelledby={`comparison-positions-${position}`}>
      <h3 id={`comparison-positions-${position}`}>{t("runTitle", { position, runId: result.run_id })}</h3>
      <p className="identity-line">{result.job_id}</p>
      <PositionTable caption={t("startingPositions", { position })} positions={result.artifact.starting_account_state.positions} />
      <PositionTable caption={t("endingPositions", { position })} positions={result.artifact.ending_account_state.positions} />
      <PositionTable caption={t("sessionStarting", { position })} positions={session.starting_positions} />
      <PositionTable caption={t("sessionEnding", { position })} positions={session.ending_positions} />
      <PositionChangeTable caption={t("positionChanges", { position })} changes={session.position_changes} />
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
  const t = useTranslations("comparisons.results");
  const accountRows = [
    { label: t("startingAccountTimestamp"), read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.timestamp },
    { label: t("startingAccountStartingCash"), read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.starting_cash },
    { label: t("startingAccountCurrentCash"), read: (result: PaperJobResultResponse) => result.artifact.starting_account_state.current_cash },
    { label: t("endingAccountTimestamp"), read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.timestamp },
    { label: t("endingAccountStartingCash"), read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.starting_cash },
    { label: t("endingAccountCurrentCash"), read: (result: PaperJobResultResponse) => result.artifact.ending_account_state.current_cash },
  ] as const;
  const sessionRows = [
    { label: t("sessionStart"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.session_start_timestamp },
    { label: t("sessionEnd"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.session_end_timestamp },
    { label: t("startingCash"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.starting_cash },
    { label: t("endingCash"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.ending_cash },
    { label: t("cashChange"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.cash_change },
    { label: t("orderCount"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.order_count },
    { label: t("fillCount"), read: (result: PaperJobResultResponse) => result.artifact.session_summary.fill_count },
  ] as const;
  const auditRows = [
    { label: t("auditSchema"), read: (result: PaperJobResultResponse) => result.result_summary.audit.schema_version },
    { label: t("auditCreated"), read: (result: PaperJobResultResponse) => result.result_summary.audit.created_timestamp },
    { label: t("sessionStart"), read: (result: PaperJobResultResponse) => result.result_summary.audit.session_start_timestamp },
    { label: t("sessionEnd"), read: (result: PaperJobResultResponse) => result.result_summary.audit.session_end_timestamp },
    { label: t("startingCash"), read: (result: PaperJobResultResponse) => result.result_summary.audit.starting_cash },
    { label: t("endingCash"), read: (result: PaperJobResultResponse) => result.result_summary.audit.ending_cash },
    { label: t("cashChange"), read: (result: PaperJobResultResponse) => result.result_summary.audit.cash_change },
    { label: t("orderCount"), read: (result: PaperJobResultResponse) => result.result_summary.audit.order_count },
    { label: t("fillCount"), read: (result: PaperJobResultResponse) => result.result_summary.audit.fill_count },
    { label: t("startingPositionCount"), read: (result: PaperJobResultResponse) => result.result_summary.audit.starting_position_count },
    { label: t("endingPositionCount"), read: (result: PaperJobResultResponse) => result.result_summary.audit.ending_position_count },
    { label: t("positionChangeCount"), read: (result: PaperJobResultResponse) => result.result_summary.audit.position_change_count },
  ] as const;
  return (
    <section className="comparison-results" aria-labelledby="comparison-results-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h2 id="comparison-results-title">{t("title")}</h2>
        </div>
        <button className="secondary-button" type="button" onClick={onRefresh}>
          {t("refresh")}
        </button>
      </div>
      <p className="neutral-note">
        {t("boundary")}
      </p>

      <div className="comparison-run-grid" aria-label={t("identityAria")}>
        {slots.map((slot, index) => {
          if (slot.status === "success") {
            return <ResultIdentity key={`${slot.jobId}-${index}`} slot={slot} position={index + 1} />;
          }
          if (slot.status === "loading") {
            return (
              <article className="comparison-run-card" aria-busy="true" key={`${slot.jobId}-${index}`}>
                <p className="eyebrow">{t("position", { position: index + 1 })}</p>
                <h3>{t("loading")}</h3>
                <p className="identity-line">{slot.jobId}</p>
                <SlotSourceLinks jobId={slot.jobId} />
              </article>
            );
          }
          return (
            <article className="comparison-run-card comparison-run-card--error" role="alert" key={`${slot.jobId}-${index}`}>
              <p className="eyebrow">{t("unavailable", { position: index + 1 })}</p>
              <ComparisonErrorDetail error={slot.error} />
              <p className="identity-line">{slot.jobId}</p>
              <RequestId value={slot.error.requestId} />
              <button className="secondary-button" type="button" onClick={() => onRetry(index)}>
                {t("retry", { jobId: slot.jobId })}
              </button>
              <SlotSourceLinks jobId={slot.jobId} />
            </article>
          );
        })}
      </div>

      <section className="content-panel" aria-labelledby="comparison-account-title">
        <p className="eyebrow">{t("accountEyebrow")}</p>
        <h2 id="comparison-account-title">{t("accountTitle")}</h2>
        <p className="neutral-note">{t("accountBoundary")}</p>
        <ComparisonMatrix caption={t("accountCaption")} slots={slots} rows={accountRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-session-title">
        <p className="eyebrow">{t("sessionEyebrow")}</p>
        <h2 id="comparison-session-title">{t("sessionTitle")}</h2>
        <ComparisonMatrix caption={t("sessionCaption")} slots={slots} rows={sessionRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-audit-title">
        <p className="eyebrow">{t("auditEyebrow")}</p>
        <h2 id="comparison-audit-title">{t("auditTitle")}</h2>
        <p className="neutral-note">{t("auditBoundary")}</p>
        <ComparisonMatrix caption={t("auditCaption")} slots={slots} rows={auditRows} />
      </section>

      <section className="content-panel" aria-labelledby="comparison-positions-title">
        <p className="eyebrow">{t("positionsEyebrow")}</p>
        <h2 id="comparison-positions-title">{t("positionsTitle")}</h2>
        {slots.map((slot, index) => slot.status === "success" ? (
          <RunPositions key={`${slot.jobId}-${index}`} slot={slot} position={index + 1} />
        ) : null)}
      </section>
    </section>
  );
}
