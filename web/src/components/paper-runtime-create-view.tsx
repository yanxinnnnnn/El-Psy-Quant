"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { EmptyState, ErrorState, LoadingState, RequestId } from "@/components/data-states";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import {
  ApiClientError,
  createPaperRuntime,
  fetchPaperExecutionOrders,
  type PaperExecutionOrderListResponse,
  type PaperRuntimeCommandResponse,
  type PaperRuntimeCreateRequest,
} from "@/lib/api-client";

type Failure = Readonly<{ code: string; message: string; requestId: string | null; status: number }>;
type KeyState = Readonly<{ fingerprint: string; key: string }>;

function failure(error: unknown): Failure {
  return error instanceof ApiClientError
    ? { code: error.code, message: error.publicMessage, requestId: error.requestId, status: error.status }
    : { code: "api_unavailable", message: "The local API is unavailable.", requestId: null, status: 0 };
}

function keyFor(fingerprint: string, current: KeyState | null): KeyState {
  return current?.fingerprint === fingerprint
    ? current
    : { fingerprint, key: `s224-create-${globalThis.crypto.randomUUID()}` };
}

export function PaperRuntimeCreateView() {
  const t = useTranslations("paperRuntimes");
  const [orders, setOrders] = useState<PaperExecutionOrderListResponse | null>(null);
  const [ordersError, setOrdersError] = useState<Failure | null>(null);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [logicalActor, setLogicalActor] = useState("founder-paper-runtime");
  const [policyId, setPolicyId] = useState("durable-runtime-v1");
  const [policyVersion, setPolicyVersion] = useState("1");
  const [actor, setActor] = useState("founder");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<Failure | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [result, setResult] = useState<PaperRuntimeCommandResponse | null>(null);
  const [keyState, setKeyState] = useState<KeyState | null>(null);
  const pending = useRef(false);
  const sequence = useRef(0);

  const loadOrders = useCallback(async (cursor?: string | null) => {
    const requestSequence = ++sequence.current;
    setOrdersLoading(true);
    setOrdersError(null);
    try {
      const response = await fetchPaperExecutionOrders({ limit: 25, ...(cursor ? { cursor } : {}) });
      if (requestSequence !== sequence.current) return;
      setOrders((previous) => cursor && previous
        ? { ...response.data, items: [...previous.items, ...response.data.items] }
        : response.data);
    } catch (caught) {
      if (requestSequence === sequence.current) setOrdersError(failure(caught));
    } finally {
      if (requestSequence === sequence.current) setOrdersLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOrders();
  }, [loadOrders]);

  const selected = useMemo(
    () => orders?.items.find((view) => view.order.execution_order_id === selectedOrderId && !view.state.terminal) ?? null,
    [orders, selectedOrderId],
  );

  async function submit() {
    if (pending.current) return;
    setSubmitError(null);
    setValidationError(null);
    setResult(null);
    if (selected === null) {
      setValidationError(t("create.validationOrder"));
      return;
    }
    const version = Number(policyVersion);
    const invalid = logicalActor.length === 0 || logicalActor !== logicalActor.trim() || logicalActor.length > 256
        ? t("create.validationActor")
        : policyId.length === 0 || policyId !== policyId.trim() || policyId.length > 128
          ? t("create.validationPolicy")
          : !Number.isInteger(version) || version < 0
            ? t("create.validationVersion")
            : actor.length === 0 || actor !== actor.trim() || actor.length > 256
              ? t("create.validationActor")
              : null;
    if (invalid !== null) { setValidationError(invalid); return; }
    const request: PaperRuntimeCreateRequest = {
      execution_order_id: selected.order.execution_order_id,
      execution_order_digest: selected.order.execution_order_digest,
      logical_actor: logicalActor,
      runtime_policy_id: policyId,
      runtime_policy_version: version,
      actor,
    };
    const fingerprint = JSON.stringify(request);
    const nextKey = keyFor(fingerprint, keyState);
    setKeyState(nextKey);
    pending.current = true;
    setSubmitting(true);
    try {
      const response = await createPaperRuntime(request, nextKey.key);
      setResult(response.data);
    } catch (caught) {
      setSubmitError(failure(caught));
    } finally {
      pending.current = false;
      setSubmitting(false);
    }
  }

  return <div className="business-workspace">
    <header className="page-heading"><p className="eyebrow">{t("create.eyebrow")}</p><h1>{t("create.title")}</h1><p>{t("create.description")}</p><Link className="text-link" href="/paper-runtimes">{t("create.back")}</Link></header>
    <aside className="boundary-note" aria-label={t("common.authorityTitle")}><strong>{t("common.authorityTitle")}</strong><p>{t("create.authority")}</p></aside>
    <section className="content-panel" aria-labelledby="runtime-order-candidates"><div className="section-heading"><div><p className="eyebrow">{t("create.candidatesEyebrow")}</p><h2 id="runtime-order-candidates">{t("create.candidatesTitle")}</h2></div><p>{t("create.candidatesDescription")}</p></div>
      {ordersLoading && !orders ? <LoadingState message={t("create.loadingCandidates")} /> : null}
      {ordersError ? <ErrorState title={t("create.candidatesError")} code={ordersError.code} message={ordersError.message} requestId={ordersError.requestId} httpStatus={ordersError.status} operation="paper_execution.order.list" onRetry={() => void loadOrders()} /> : null}
      {orders?.items.length === 0 ? <EmptyState title={t("create.noCandidatesTitle")} message={t("create.noCandidatesMessage")} /> : null}
      {orders && orders.items.length > 0 ? <ScrollableTable caption={t("create.candidatesCaption")}><thead><tr><th>{t("create.select")}</th><th>{t("fields.execution_order_id")}</th><th>{t("fields.account_id")}</th><th>{t("fields.instrument_id")}</th><th>{t("fields.side")}</th><th>{t("fields.requested_quantity")}</th><th>{t("fields.remaining_quantity")}</th><th>{t("fields.execution_version")}</th><th>{t("fields.execution_status")}</th><th>{t("fields.replay_id")}</th><th>{t("fields.trading_session_id")}</th></tr></thead><tbody>{orders.items.map((view, index) => <tr key={`${view.order.execution_order_id}-${index}`}>
        <td>{view.state.terminal ? <span>{t("create.terminal")}</span> : <input type="radio" name="execution-order" aria-label={t("create.selectOrder", { id: view.order.execution_order_id })} checked={selectedOrderId === view.order.execution_order_id} onChange={() => setSelectedOrderId(view.order.execution_order_id)} />}</td>
        <td><code className="raw-value">{view.order.execution_order_id}<br />{view.order.execution_order_digest}</code></td><td><code>{view.order.account_id}</code></td><td><code>{view.order.instrument_id}</code></td><td><code>{view.order.side}</code></td><td><code>{view.order.requested_quantity}</code></td><td><code>{view.state.remaining_quantity}</code></td><td>{view.state.execution_version}</td><td><code>{view.state.status}</code></td><td><code>{view.order.market_handoff_reference.replay_id}</code></td><td><code>{view.order.market_handoff_reference.trading_session_id}</code></td>
      </tr>)}</tbody></ScrollableTable> : null}
      {orders?.next_cursor ? <button className="secondary-button" type="button" disabled={ordersLoading} onClick={() => void loadOrders(orders.next_cursor)}>{ordersLoading ? t("actions.loadingMore") : t("actions.loadMore")}</button> : null}
    </section>
    {validationError ? <section className="state-panel state-panel--error" role="alert"><h2>{t("create.validationTitle")}</h2><p>{validationError}</p></section> : null}
    {submitError ? <ErrorState title={t("create.submitError")} code={submitError.code} message={submitError.message} requestId={submitError.requestId} httpStatus={submitError.status} operation="paper_runtime.create" onRetry={() => void submit()} retryLabel={t("actions.retryExact")} /> : null}
    {result ? <section className="state-panel state-panel--success" role="status"><p className="eyebrow">{result.replayed ? t("create.replayed") : t("create.created")}</p><h2>{t("create.successTitle")}</h2><p>{t("create.noAutoStart")}</p><RequestId value={result.request_id} /><dl className="compact-definitions"><div><dt>{t("fields.runtime_id")}</dt><dd><code className="raw-value">{result.runtime.runtime_id}</code></dd></div><div><dt>{t("fields.desired_state")}</dt><dd><code>{result.runtime.desired_state}</code></dd></div><div><dt>{t("fields.observed_state")}</dt><dd><code>{result.runtime.observed_state}</code></dd></div></dl><Link className="primary-link" href={`/paper-runtimes/${encodeURIComponent(result.runtime.runtime_id)}`}>{t("create.inspect")}</Link></section> : null}
    <form className="business-form" onSubmit={(event) => { event.preventDefault(); void submit(); }}><fieldset><legend>{t("create.draftLegend")}</legend><div className="form-grid">
      <label>{t("fields.logical_actor")}<input value={logicalActor} onChange={(event) => setLogicalActor(event.target.value)} maxLength={256} required /></label>
      <label>{t("fields.runtime_policy_id")}<input value={policyId} onChange={(event) => setPolicyId(event.target.value)} maxLength={128} required /></label>
      <label>{t("fields.runtime_policy_version")}<input type="number" min="0" step="1" value={policyVersion} onChange={(event) => setPolicyVersion(event.target.value)} required /></label>
      <label>{t("fields.actor")}<input value={actor} onChange={(event) => setActor(event.target.value)} maxLength={256} required /></label>
    </div></fieldset><button className="primary-button" type="submit" disabled={submitting}>{submitting ? t("create.submitting") : t("create.submit")}</button></form>
  </div>;
}
