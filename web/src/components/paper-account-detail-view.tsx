"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useState,
} from "react";

import {
  ErrorState,
  LoadingState,
  RequestId,
} from "@/components/data-states";
import {
  PaperAccountLifecycleValue,
  PaperAccountProjectionStatusValue,
  PaperAccountReconciliationOutcomeValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import {
  ApiClientError,
  changePaperAccountLifecycle,
  createPaperAccountSnapshot,
  fetchPaperAccountDetail,
  fetchPaperAccountLedger,
  linkPaperAccountEvidence,
  postPaperAccountCashMovement,
  postPaperAccountPositionAdjustment,
  reconcilePaperAccount,
  type PaperAccountCommandResponse,
  type PaperAccountDetailResponse,
  type PaperAccountEvidenceOperationRequest,
  type PaperAccountLedgerResponse,
  type PaperAccountReconciliationCommandResponse,
  type PaperAccountSnapshotCommandResponse,
} from "@/lib/api-client";
import {
  isCanonicalPaperDecimal,
  isNormalizedPaperText,
  isOptionalNormalizedUtc,
  paperAccountLifecycleActions,
  paperCashMovementTypes,
  paperPositionAdjustmentCategories,
} from "@/lib/paper-accounts";
import { useApiResource } from "@/lib/use-api-resource";

type DetailData = {
  detail: PaperAccountDetailResponse;
  ledger: PaperAccountLedgerResponse;
};

type Failure = {
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number;
  operation: string;
} | null;

function failureFrom(error: unknown, operation: string): NonNullable<Failure> {
  if (error instanceof ApiClientError) {
    return {
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
      httpStatus: error.status,
      operation,
    };
  }
  return {
    code: "api_request_failed",
    message: "The local API request failed.",
    requestId: null,
    httpStatus: 0,
    operation,
  };
}

function RawValue({ children }: { children: ReactNode }) {
  return <code className="raw-value">{children}</code>;
}

function ProjectionView({ detail }: { detail: PaperAccountDetailResponse }) {
  const t = useTranslations("paperAccounts.detail");
  const common = useTranslations("paperAccounts.common");
  const { account, projection } = detail;
  return (
    <>
      <section className="evidence-section" aria-labelledby="account-authority">
        <div className="section-heading">
          <h2 id="account-authority">{t("accountAuthority")}</h2>
          <p>{t("accountAuthorityDescription")}</p>
        </div>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{common("accountId")}</dt><dd><RawValue>{account.account_id}</RawValue></dd></div>
          <div><dt>{common("displayName")}</dt><dd>{account.display_name}</dd></div>
          <div><dt>{common("baseCurrency")}</dt><dd><RawValue>{account.base_currency}</RawValue></dd></div>
          <div><dt>{common("lifecycleStatus")}</dt><dd><PaperAccountLifecycleValue value={account.lifecycle_status} /></dd></div>
          <div><dt>{common("headVersion")}</dt><dd>{account.head_version}</dd></div>
          <div><dt>{common("projectionStatus")}</dt><dd><PaperAccountProjectionStatusValue value={account.projection_status} /></dd></div>
          <div><dt>{common("createdBy")}</dt><dd><RawValue>{account.created_by}</RawValue></dd></div>
          <div><dt>{common("created")}</dt><dd><LocalizedTimestamp value={account.created_timestamp} /></dd></div>
          <div><dt>{common("updated")}</dt><dd><LocalizedTimestamp value={account.updated_timestamp} /></dd></div>
          <div><dt>{common("closed")}</dt><dd>{account.closed_timestamp === null ? common("notAvailable") : <LocalizedTimestamp value={account.closed_timestamp} />}</dd></div>
          <div><dt>{common("headEventId")}</dt><dd><RawValue>{account.head_event_id}</RawValue></dd></div>
          <div><dt>{common("headChainDigest")}</dt><dd><RawValue>{account.head_chain_digest}</RawValue></dd></div>
        </dl>
      </section>

      <section className="evidence-section" aria-labelledby="projection-authority">
        <div className="section-heading">
          <h2 id="projection-authority">{t("projectionAuthority")}</h2>
          <p>{t("projectionAuthorityDescription")}</p>
        </div>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{common("cashBalance")}</dt><dd><RawValue>{projection.cash_balance}</RawValue></dd></div>
          <div><dt>{common("availableCash")}</dt><dd><RawValue>{projection.available_cash}</RawValue></dd></div>
          <div><dt>{common("sourceAccountVersion")}</dt><dd>{projection.source_account_version}</dd></div>
          <div><dt>{common("sourceEventId")}</dt><dd><RawValue>{projection.source_event_id}</RawValue></dd></div>
          <div><dt>{common("sourceChainDigest")}</dt><dd><RawValue>{projection.source_chain_digest}</RawValue></dd></div>
          <div><dt>{common("projectionDigest")}</dt><dd><RawValue>{projection.projection_digest}</RawValue></dd></div>
        </dl>

        <h3>{t("positions")}</h3>
        {projection.positions.length === 0 ? (
          <p className="neutral-note">{t("noPositions")}</p>
        ) : (
          <ScrollableTable caption={t("positionsTable")}>
              <thead>
                <tr>
                  <th>{common("symbol")}</th>
                  <th>{common("quantity")}</th>
                  <th>{common("aggregateCostBasis")}</th>
                  <th>{common("averageUnitCost")}</th>
                  <th>{common("rounded")}</th>
                </tr>
              </thead>
              <tbody>
                {projection.positions.map((position, index) => (
                  <tr key={`${position.symbol}-${index}`}>
                    <td><RawValue>{position.symbol}</RawValue></td>
                    <td><RawValue>{position.quantity}</RawValue></td>
                    <td><RawValue>{position.aggregate_cost_basis}</RawValue></td>
                    <td>{position.average_unit_cost === null ? common("notAvailable") : <RawValue>{position.average_unit_cost}</RawValue>}</td>
                    <td><RawValue>{String(position.average_unit_cost_is_rounded)}</RawValue></td>
                  </tr>
                ))}
              </tbody>
          </ScrollableTable>
        )}

        <h3>{t("approvedEvidence")}</h3>
        {projection.approved_portfolio_reviews.length === 0 ? (
          <p className="neutral-note">{t("noApprovedEvidence")}</p>
        ) : (
          <ol className="card-list card-list--compact">
            {projection.approved_portfolio_reviews.map((reference, index) => (
              <li className="evidence-card" key={`${reference.review_id}-${index}`}>
                <h4>{reference.review_id}</h4>
                <dl className="compact-definitions">
                  {Object.entries(reference).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd><RawValue>{String(value)}</RawValue></dd>
                    </div>
                  ))}
                </dl>
                <Link
                  className="text-link"
                  href={`/portfolio-reviews/${encodeURIComponent(reference.review_id)}`}
                >
                  {t("inspectReview")}
                </Link>
              </li>
            ))}
          </ol>
        )}
      </section>
    </>
  );
}

function LedgerView({
  ledger,
  loadingMore,
  onLoadMore,
}: {
  ledger: PaperAccountLedgerResponse;
  loadingMore: boolean;
  onLoadMore: () => void;
}) {
  const t = useTranslations("paperAccounts.ledger");
  const common = useTranslations("paperAccounts.common");
  return (
    <section className="evidence-section" aria-labelledby="ledger-timeline">
      <div className="section-heading">
        <h2 id="ledger-timeline">{t("title")}</h2>
        <p>{t("description")}</p>
      </div>
      <ol className="timeline-list">
        {ledger.events.map((event, index) => (
          <li className="timeline-card" key={`${event.event_id}-${index}`}>
            <header>
              <div>
                <p className="eyebrow">{t("sequence", { number: event.sequence_number })}</p>
                <h3>{t(`eventTypes.${event.event_type}`)}</h3>
              </div>
              <RawValue>{event.event_type}</RawValue>
            </header>
            <dl className="compact-definitions">
              <div><dt>{common("eventId")}</dt><dd><RawValue>{event.event_id}</RawValue></dd></div>
              <div><dt>{common("accountVersion")}</dt><dd>{event.account_version}</dd></div>
              <div><dt>{common("actor")}</dt><dd><RawValue>{event.actor}</RawValue></dd></div>
              <div><dt>{common("reason")}</dt><dd>{event.reason ?? common("notAvailable")}</dd></div>
              <div><dt>{common("recorded")}</dt><dd><LocalizedTimestamp value={event.recorded_timestamp_utc} /></dd></div>
              <div><dt>{common("effective")}</dt><dd>{event.effective_timestamp_utc === null ? common("notAvailable") : <LocalizedTimestamp value={event.effective_timestamp_utc} />}</dd></div>
              <div><dt>{common("commandDigest")}</dt><dd><RawValue>{event.command_digest}</RawValue></dd></div>
              <div><dt>{common("eventDigest")}</dt><dd><RawValue>{event.event_digest}</RawValue></dd></div>
              <div><dt>{common("previousChainDigest")}</dt><dd><RawValue>{event.previous_chain_digest}</RawValue></dd></div>
              <div><dt>{common("chainDigest")}</dt><dd><RawValue>{event.chain_digest}</RawValue></dd></div>
            </dl>
            <details className="audit-disclosure">
              <summary>{t("details")}</summary>
              <pre className="json-evidence">{JSON.stringify(event.details, null, 2)}</pre>
            </details>
            {event.cash_postings.length > 0 ? (
              <details className="audit-disclosure">
                <summary>{t("cashPostings", { count: event.cash_postings.length })}</summary>
                <ScrollableTable caption={t("cashTable")}>
                    <thead><tr><th>{common("entryId")}</th><th>{common("movementType")}</th><th>{common("currency")}</th><th>{common("signedAmount")}</th><th>{common("entryDigest")}</th></tr></thead>
                    <tbody>
                      {event.cash_postings.map((posting, postingIndex) => (
                        <tr key={`${posting.cash_entry_id}-${postingIndex}`}>
                          <td><RawValue>{posting.cash_entry_id}</RawValue></td>
                          <td><RawValue>{posting.movement_type}</RawValue></td>
                          <td><RawValue>{posting.currency}</RawValue></td>
                          <td><RawValue>{posting.signed_amount}</RawValue></td>
                          <td><RawValue>{posting.entry_digest}</RawValue></td>
                        </tr>
                      ))}
                    </tbody>
                </ScrollableTable>
              </details>
            ) : null}
            {event.position_postings.length > 0 ? (
              <details className="audit-disclosure">
                <summary>{t("positionPostings", { count: event.position_postings.length })}</summary>
                <ScrollableTable caption={t("positionTable")}>
                    <thead><tr><th>{common("entryId")}</th><th>{common("symbol")}</th><th>{common("quantityDelta")}</th><th>{common("costBasisDelta")}</th><th>{common("adjustmentCategory")}</th><th>{common("entryDigest")}</th></tr></thead>
                    <tbody>
                      {event.position_postings.map((posting, postingIndex) => (
                        <tr key={`${posting.position_entry_id}-${postingIndex}`}>
                          <td><RawValue>{posting.position_entry_id}</RawValue></td>
                          <td><RawValue>{posting.symbol}</RawValue></td>
                          <td><RawValue>{posting.signed_quantity_delta}</RawValue></td>
                          <td><RawValue>{posting.signed_cost_basis_delta}</RawValue></td>
                          <td><RawValue>{posting.adjustment_category}</RawValue></td>
                          <td><RawValue>{posting.entry_digest}</RawValue></td>
                        </tr>
                      ))}
                    </tbody>
                </ScrollableTable>
              </details>
            ) : null}
          </li>
        ))}
      </ol>
      {ledger.next_after_sequence_number !== null ? (
        <button
          className="secondary-button"
          type="button"
          disabled={loadingMore}
          onClick={onLoadMore}
        >
          {loadingMore ? t("loadingMore") : t("loadMore")}
        </button>
      ) : null}
    </section>
  );
}

function MutationFeedback({
  failure,
  command,
  onRefresh,
}: {
  failure: Failure;
  command: PaperAccountCommandResponse | null;
  onRefresh: () => void;
}) {
  const t = useTranslations("paperAccounts.operations");
  if (failure) {
    return (
      <ErrorState
        title={t("failureTitle")}
        code={failure.code}
        message={failure.message}
        requestId={failure.requestId}
        httpStatus={failure.httpStatus}
        operation={failure.operation}
      />
    );
  }
  if (!command) return null;
  return (
    <section className="state-panel state-panel--success" role="status">
      <p className="eyebrow">{command.replayed ? t("replayed") : t("accepted")}</p>
      <h2>{t("acceptedTitle")}</h2>
      <RequestId value={command.request_id} />
      <p><RawValue>{command.event.event_type}</RawValue> · <RawValue>{command.event.event_id}</RawValue></p>
      <button className="secondary-button" type="button" onClick={onRefresh}>
        {t("refreshAuthority")}
      </button>
    </section>
  );
}

function OperationsWorkspace({
  accountId,
  detail,
  onCommand,
  onRefresh,
}: {
  accountId: string;
  detail: PaperAccountDetailResponse;
  onCommand: (command: PaperAccountCommandResponse) => void;
  onRefresh: () => void;
}) {
  const t = useTranslations("paperAccounts.operations");
  const common = useTranslations("paperAccounts.common");
  const validation = useTranslations("paperAccounts.validation");
  const [failure, setFailure] = useState<Failure>(null);
  const [command, setCommand] = useState<PaperAccountCommandResponse | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [cash, setCash] = useState({ actor: "", reason: "", idempotencyKey: "", movementType: "", requestedAmount: "", effectiveTimestamp: "" });
  const [position, setPosition] = useState({ actor: "", reason: "", idempotencyKey: "", symbol: "", category: "", quantityDelta: "", costBasisDelta: "", effectiveTimestamp: "" });
  const [evidence, setEvidence] = useState({ actor: "", reason: "", idempotencyKey: "", reviewId: "" });
  const [lifecycle, setLifecycle] = useState({ actor: "", reason: "", idempotencyKey: "", action: "", confirmed: false });
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  const run = async (
    operation: string,
    task: () => Promise<{ data: PaperAccountCommandResponse }>,
  ) => {
    setFailure(null);
    setCommand(null);
    setPending(operation);
    try {
      const result = await task();
      setCommand(result.data);
      onCommand(result.data);
    } catch (error) {
      setFailure(failureFrom(error, operation));
    } finally {
      setPending(null);
    }
  };

  const validCommon = (actor: string, reason: string, key: string) =>
    isNormalizedPaperText(actor, 512) &&
    isNormalizedPaperText(reason, 2000) &&
    isNormalizedPaperText(key, 128);

  const invalid = (message: string) => {
    setValidationMessage(message);
    setFailure(null);
    setCommand(null);
  };

  const submitCash = (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    if (
      !validCommon(cash.actor, cash.reason, cash.idempotencyKey) ||
      !paperCashMovementTypes.includes(
        cash.movementType as (typeof paperCashMovementTypes)[number],
      ) ||
      !isCanonicalPaperDecimal(cash.requestedAmount) ||
      !isOptionalNormalizedUtc(cash.effectiveTimestamp)
    ) {
      invalid(validation("operation"));
      return;
    }
    void run("paper_account.cash_movement", () =>
      postPaperAccountCashMovement(
        accountId,
        {
          expected_account_version: detail.account.head_version,
          actor: cash.actor,
          reason: cash.reason,
          movement_type: cash.movementType as (typeof paperCashMovementTypes)[number],
          requested_amount: cash.requestedAmount,
          effective_timestamp_utc: cash.effectiveTimestamp || null,
        },
        cash.idempotencyKey,
      ),
    );
  };

  const submitPosition = (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    if (
      !validCommon(position.actor, position.reason, position.idempotencyKey) ||
      !isNormalizedPaperText(position.symbol, 128) ||
      !paperPositionAdjustmentCategories.includes(
        position.category as (typeof paperPositionAdjustmentCategories)[number],
      ) ||
      !isCanonicalPaperDecimal(position.quantityDelta) ||
      !isCanonicalPaperDecimal(position.costBasisDelta) ||
      !isOptionalNormalizedUtc(position.effectiveTimestamp)
    ) {
      invalid(validation("operation"));
      return;
    }
    void run("paper_account.position_adjustment", () =>
      postPaperAccountPositionAdjustment(
        accountId,
        {
          expected_account_version: detail.account.head_version,
          actor: position.actor,
          reason: position.reason,
          symbol: position.symbol,
          adjustment_category: position.category as (typeof paperPositionAdjustmentCategories)[number],
          signed_quantity_delta: position.quantityDelta,
          signed_cost_basis_delta: position.costBasisDelta,
          effective_timestamp_utc: position.effectiveTimestamp || null,
        },
        position.idempotencyKey,
      ),
    );
  };

  const submitEvidence = (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    if (
      !validCommon(evidence.actor, evidence.reason, evidence.idempotencyKey) ||
      !isNormalizedPaperText(evidence.reviewId, 512)
    ) {
      invalid(validation("operation"));
      return;
    }
    void run("paper_account.evidence_link", () =>
      linkPaperAccountEvidence(
        accountId,
        {
          expected_account_version: detail.account.head_version,
          actor: evidence.actor,
          reason: evidence.reason,
          review_id: evidence.reviewId,
        },
        evidence.idempotencyKey,
      ),
    );
  };

  const submitLifecycle = (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    if (
      !validCommon(lifecycle.actor, lifecycle.reason, lifecycle.idempotencyKey) ||
      !paperAccountLifecycleActions.includes(
        lifecycle.action as (typeof paperAccountLifecycleActions)[number],
      ) ||
      !lifecycle.confirmed
    ) {
      invalid(validation("operation"));
      return;
    }
    void run("paper_account.lifecycle", () =>
      changePaperAccountLifecycle(
        accountId,
        {
          expected_account_version: detail.account.head_version,
          actor: lifecycle.actor,
          reason: lifecycle.reason,
          action: lifecycle.action as (typeof paperAccountLifecycleActions)[number],
        },
        lifecycle.idempotencyKey,
      ),
    );
  };

  return (
    <section className="evidence-section" aria-labelledby="account-operations">
      <div className="section-heading">
        <h2 id="account-operations">{t("title")}</h2>
        <p>{t("description")}</p>
      </div>
      <aside className="boundary-note">
        <strong>{t("backendDecidesTitle")}</strong>
        <p>{t("backendDecides")}</p>
      </aside>
      {validationMessage ? (
        <section className="state-panel state-panel--error" role="alert">
          <h3>{validation("title")}</h3>
          <p>{validationMessage}</p>
          <p>{validation("noRequest")}</p>
        </section>
      ) : null}
      <MutationFeedback failure={failure} command={command} onRefresh={onRefresh} />

      <div className="operation-grid">
        <form className="business-form operation-card" onSubmit={submitCash}>
          <fieldset>
            <legend>{t("cash.title")}</legend>
            <p>{t("cash.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("movementType")}<select value={cash.movementType} onChange={(event) => setCash({ ...cash, movementType: event.target.value })} required><option value="">{common("choose")}</option>{paperCashMovementTypes.map((value) => <option key={value} value={value}>{t(`cash.types.${value}`)} ({value})</option>)}</select></label>
            <label>{common("requestedAmount")}<input value={cash.requestedAmount} onChange={(event) => setCash({ ...cash, requestedAmount: event.target.value })} inputMode="decimal" required /></label>
            <label>{common("effectiveTimestamp")}<input value={cash.effectiveTimestamp} onChange={(event) => setCash({ ...cash, effectiveTimestamp: event.target.value })} placeholder="2026-07-26T12:00:00Z" /></label>
            <label>{common("actor")}<input value={cash.actor} onChange={(event) => setCash({ ...cash, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={cash.reason} onChange={(event) => setCash({ ...cash, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={cash.idempotencyKey} onChange={(event) => setCash({ ...cash, idempotencyKey: event.target.value })} required /></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending !== null}>{t("cash.submit")}</button>
        </form>

        <form className="business-form operation-card" onSubmit={submitPosition}>
          <fieldset>
            <legend>{t("position.title")}</legend>
            <p>{t("position.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("symbol")}<input value={position.symbol} onChange={(event) => setPosition({ ...position, symbol: event.target.value })} required /></label>
            <label>{common("adjustmentCategory")}<select value={position.category} onChange={(event) => setPosition({ ...position, category: event.target.value })} required><option value="">{common("choose")}</option>{paperPositionAdjustmentCategories.map((value) => <option key={value} value={value}>{t(`position.categories.${value}`)} ({value})</option>)}</select></label>
            <label>{common("quantityDelta")}<input value={position.quantityDelta} onChange={(event) => setPosition({ ...position, quantityDelta: event.target.value })} inputMode="decimal" required /></label>
            <label>{common("costBasisDelta")}<input value={position.costBasisDelta} onChange={(event) => setPosition({ ...position, costBasisDelta: event.target.value })} inputMode="decimal" required /></label>
            <label>{common("effectiveTimestamp")}<input value={position.effectiveTimestamp} onChange={(event) => setPosition({ ...position, effectiveTimestamp: event.target.value })} placeholder="2026-07-26T12:00:00Z" /></label>
            <label>{common("actor")}<input value={position.actor} onChange={(event) => setPosition({ ...position, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={position.reason} onChange={(event) => setPosition({ ...position, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={position.idempotencyKey} onChange={(event) => setPosition({ ...position, idempotencyKey: event.target.value })} required /></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending !== null}>{t("position.submit")}</button>
        </form>

        <form className="business-form operation-card" onSubmit={submitEvidence}>
          <fieldset>
            <legend>{t("evidence.title")}</legend>
            <p>{t("evidence.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("reviewId")}<input value={evidence.reviewId} onChange={(event) => setEvidence({ ...evidence, reviewId: event.target.value })} required /></label>
            <label>{common("actor")}<input value={evidence.actor} onChange={(event) => setEvidence({ ...evidence, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={evidence.reason} onChange={(event) => setEvidence({ ...evidence, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={evidence.idempotencyKey} onChange={(event) => setEvidence({ ...evidence, idempotencyKey: event.target.value })} required /></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending !== null}>{t("evidence.submit")}</button>
        </form>

        <form className="business-form operation-card" onSubmit={submitLifecycle}>
          <fieldset>
            <legend>{t("lifecycle.title")}</legend>
            <p>{t("lifecycle.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("action")}<select value={lifecycle.action} onChange={(event) => setLifecycle({ ...lifecycle, action: event.target.value })} required><option value="">{common("choose")}</option>{paperAccountLifecycleActions.map((value) => <option key={value} value={value}>{t(`lifecycle.actions.${value}`)} ({value})</option>)}</select></label>
            <label>{common("actor")}<input value={lifecycle.actor} onChange={(event) => setLifecycle({ ...lifecycle, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={lifecycle.reason} onChange={(event) => setLifecycle({ ...lifecycle, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={lifecycle.idempotencyKey} onChange={(event) => setLifecycle({ ...lifecycle, idempotencyKey: event.target.value })} required /></label>
            <label className="confirmation-control"><input type="checkbox" checked={lifecycle.confirmed} onChange={(event) => setLifecycle({ ...lifecycle, confirmed: event.target.checked })} /><span>{t("lifecycle.confirmation")}</span></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending !== null}>{t("lifecycle.submit")}</button>
        </form>
      </div>
    </section>
  );
}

function EvidenceOperations({
  accountId,
  detail,
}: {
  accountId: string;
  detail: PaperAccountDetailResponse;
}) {
  const t = useTranslations("paperAccounts.evidenceOperations");
  const common = useTranslations("paperAccounts.common");
  const validation = useTranslations("paperAccounts.validation");
  const [snapshotDraft, setSnapshotDraft] = useState({ actor: "", reason: "", idempotencyKey: "" });
  const [reconciliationDraft, setReconciliationDraft] = useState({ actor: "", reason: "", idempotencyKey: "" });
  const [snapshotResult, setSnapshotResult] = useState<PaperAccountSnapshotCommandResponse | null>(null);
  const [reconciliationResult, setReconciliationResult] = useState<PaperAccountReconciliationCommandResponse | null>(null);
  const [failure, setFailure] = useState<Failure>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const requestFor = (
    draft: { actor: string; reason: string },
  ): PaperAccountEvidenceOperationRequest => ({
    expected_account_version: detail.account.head_version,
    expected_head_event_id: detail.account.head_event_id,
    expected_head_chain_digest: detail.account.head_chain_digest,
    actor: draft.actor,
    reason: draft.reason,
  });

  const valid = (draft: { actor: string; reason: string; idempotencyKey: string }) =>
    isNormalizedPaperText(draft.actor, 512) &&
    isNormalizedPaperText(draft.reason, 2000) &&
    isNormalizedPaperText(draft.idempotencyKey, 128);

  const submitSnapshot = async (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    setFailure(null);
    if (!valid(snapshotDraft)) {
      setValidationMessage(validation("operation"));
      return;
    }
    setPending(true);
    try {
      const result = await createPaperAccountSnapshot(
        accountId,
        requestFor(snapshotDraft),
        snapshotDraft.idempotencyKey,
      );
      setSnapshotResult(result.data);
    } catch (error) {
      setFailure(failureFrom(error, "paper_account.snapshot"));
    } finally {
      setPending(false);
    }
  };

  const submitReconciliation = async (event: FormEvent) => {
    event.preventDefault();
    setValidationMessage(null);
    setFailure(null);
    if (!valid(reconciliationDraft)) {
      setValidationMessage(validation("operation"));
      return;
    }
    setPending(true);
    try {
      const result = await reconcilePaperAccount(
        accountId,
        requestFor(reconciliationDraft),
        reconciliationDraft.idempotencyKey,
      );
      setReconciliationResult(result.data);
    } catch (error) {
      setFailure(failureFrom(error, "paper_account.reconciliation"));
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="evidence-section" aria-labelledby="derived-evidence">
      <div className="section-heading">
        <h2 id="derived-evidence">{t("title")}</h2>
        <p>{t("description")}</p>
      </div>
      {validationMessage ? <section className="state-panel state-panel--error" role="alert"><h3>{validation("title")}</h3><p>{validationMessage}</p><p>{validation("noRequest")}</p></section> : null}
      {failure ? <ErrorState title={t("failureTitle")} code={failure.code} message={failure.message} requestId={failure.requestId} httpStatus={failure.httpStatus} operation={failure.operation} /> : null}
      <div className="operation-grid">
        <form className="business-form operation-card" onSubmit={submitSnapshot}>
          <fieldset>
            <legend>{t("snapshot.title")}</legend>
            <p>{t("snapshot.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("expectedHeadEventId")}<input value={detail.account.head_event_id} readOnly /></label>
            <label>{common("expectedHeadChainDigest")}<input value={detail.account.head_chain_digest} readOnly /></label>
            <label>{common("actor")}<input value={snapshotDraft.actor} onChange={(event) => setSnapshotDraft({ ...snapshotDraft, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={snapshotDraft.reason} onChange={(event) => setSnapshotDraft({ ...snapshotDraft, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={snapshotDraft.idempotencyKey} onChange={(event) => setSnapshotDraft({ ...snapshotDraft, idempotencyKey: event.target.value })} required /></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending}>{t("snapshot.submit")}</button>
        </form>
        <form className="business-form operation-card" onSubmit={submitReconciliation}>
          <fieldset>
            <legend>{t("reconciliation.title")}</legend>
            <p>{t("reconciliation.description")}</p>
            <label>{common("expectedAccountVersion")}<input value={detail.account.head_version} readOnly /></label>
            <label>{common("expectedHeadEventId")}<input value={detail.account.head_event_id} readOnly /></label>
            <label>{common("expectedHeadChainDigest")}<input value={detail.account.head_chain_digest} readOnly /></label>
            <label>{common("actor")}<input value={reconciliationDraft.actor} onChange={(event) => setReconciliationDraft({ ...reconciliationDraft, actor: event.target.value })} required /></label>
            <label>{common("reason")}<textarea value={reconciliationDraft.reason} onChange={(event) => setReconciliationDraft({ ...reconciliationDraft, reason: event.target.value })} required /></label>
            <label>{common("idempotencyKey")}<input value={reconciliationDraft.idempotencyKey} onChange={(event) => setReconciliationDraft({ ...reconciliationDraft, idempotencyKey: event.target.value })} required /></label>
          </fieldset>
          <button className="primary-button" type="submit" disabled={pending}>{t("reconciliation.submit")}</button>
        </form>
      </div>

      {snapshotResult ? (
        <article className="evidence-card immutable-evidence">
          <p className="eyebrow">{snapshotResult.replayed ? t("replayed") : t("created")}</p>
          <h3>{t("snapshot.inspectionTitle")}</h3>
          <RequestId value={snapshotResult.request_id} />
          <dl className="definition-grid definition-grid--wide">
            {Object.entries(snapshotResult.snapshot).filter(([key]) => key !== "projection").map(([key, value]) => (
              <div key={key}><dt>{key}</dt><dd><RawValue>{String(value)}</RawValue></dd></div>
            ))}
          </dl>
          <h4>{t("snapshot.projectionTitle")}</h4>
          <pre className="json-evidence">{JSON.stringify(snapshotResult.snapshot.projection, null, 2)}</pre>
        </article>
      ) : null}

      {reconciliationResult ? (
        <article className="evidence-card immutable-evidence">
          <p className="eyebrow">{reconciliationResult.replayed ? t("replayed") : t("created")}</p>
          <h3>{t("reconciliation.inspectionTitle")}</h3>
          <RequestId value={reconciliationResult.request_id} />
          <PaperAccountReconciliationOutcomeValue value={reconciliationResult.reconciliation.outcome} />
          <dl className="definition-grid definition-grid--wide">
            {Object.entries(reconciliationResult.reconciliation).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd><RawValue>{Array.isArray(value) ? value.join(", ") || "[]" : String(value)}</RawValue></dd>
              </div>
            ))}
          </dl>
        </article>
      ) : null}
    </section>
  );
}

export function PaperAccountDetailView({ accountId }: { accountId: string }) {
  const t = useTranslations("paperAccounts.detail");
  const common = useTranslations("paperAccounts.common");
  const [retained, setRetained] = useState<DetailData | null>(null);
  const [commandOverride, setCommandOverride] =
    useState<PaperAccountCommandResponse | null>(null);
  const [ledgerOverride, setLedgerOverride] =
    useState<PaperAccountLedgerResponse | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [ledgerFailure, setLedgerFailure] = useState<Failure>(null);
  const request = useCallback(async () => {
    const [detail, ledger] = await Promise.all([
      fetchPaperAccountDetail(accountId),
      fetchPaperAccountLedger(accountId),
    ]);
    const data = { detail: detail.data, ledger: ledger.data };
    setRetained(data);
    setCommandOverride(null);
    setLedgerOverride(null);
    return { data, requestId: detail.requestId ?? ledger.requestId };
  }, [accountId]);
  const { state, retry } = useApiResource(request);
  const loaded = state.status === "success" ? state.data : retained;
  const detail = commandOverride
    ? {
        schema_version: 1 as const,
        account: commandOverride.account,
        projection: commandOverride.projection,
      }
    : loaded?.detail ?? null;
  const ledger = ledgerOverride ?? loaded?.ledger ?? null;

  if (state.status === "loading" && loaded === null) {
    return <LoadingState message={t("loading")} />;
  }
  if (state.status === "error" && loaded === null) {
    return (
      <ErrorState
        title={t("unavailableTitle")}
        code={state.code}
        message={state.message}
        requestId={state.requestId}
        httpStatus={state.httpStatus}
        operation="paper_account.detail"
        entityLabel={common("accountId")}
        entityId={accountId}
        onRetry={retry}
        backHref="/paper-accounts"
        backLabel={t("back")}
      />
    );
  }
  if (detail === null || ledger === null) return null;

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{detail.account.display_name}</h1>
          <p><RawValue>{detail.account.account_id}</RawValue></p>
          <Link className="text-link" href="/paper-accounts">{t("back")}</Link>
        </div>
        <button className="secondary-button" type="button" onClick={retry}>
          {t("refresh")}
        </button>
      </header>
      {state.status === "loading" ? <p className="neutral-note" role="status">{common("refreshing")}</p> : null}
      {state.status === "error" ? (
        <ErrorState
          title={t("refreshFailureTitle")}
          code={state.code}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="paper_account.detail"
          entityLabel={common("accountId")}
          entityId={accountId}
          onRetry={retry}
        />
      ) : null}

      <ProjectionView detail={detail} />
      {ledgerFailure ? (
        <ErrorState
          title={t("ledgerFailureTitle")}
          code={ledgerFailure.code}
          message={ledgerFailure.message}
          requestId={ledgerFailure.requestId}
          httpStatus={ledgerFailure.httpStatus}
          operation={ledgerFailure.operation}
        />
      ) : null}
      <LedgerView
        ledger={ledger}
        loadingMore={loadingMore}
        onLoadMore={() => {
          if (ledger.next_after_sequence_number === null) return;
          setLoadingMore(true);
          setLedgerFailure(null);
          void fetchPaperAccountLedger(accountId, {
            afterSequenceNumber: ledger.next_after_sequence_number,
          }).then((result) => {
            setLedgerOverride({
              schema_version: 1,
              events: [...ledger.events, ...result.data.events],
              next_after_sequence_number: result.data.next_after_sequence_number,
            });
          }).catch((error: unknown) => {
            setLedgerFailure(failureFrom(error, "paper_account.ledger"));
          }).finally(() => setLoadingMore(false));
        }}
      />
      <OperationsWorkspace
        accountId={accountId}
        detail={detail}
        onCommand={setCommandOverride}
        onRefresh={retry}
      />
      <EvidenceOperations accountId={accountId} detail={detail} />
    </div>
  );
}
