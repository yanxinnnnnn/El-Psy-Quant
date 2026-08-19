"use client";

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import {
  ApiClientError,
  createPaperExecutionOrder,
  fetchOrderIntents,
  fetchPaperExecutionAttempts,
  fetchPaperExecutionFills,
  fetchPaperExecutionOrderDetail,
  fetchPaperExecutionOrders,
  fetchPaperExecutionReconciliation,
  fetchPreTradeRiskDecisions,
  stepPaperExecutionOrder,
  type OrderIntentListResponse,
  type PaperExecutionAttemptListResponse,
  type PaperExecutionFillListResponse,
  type PaperExecutionOrderCommandResponse,
  type PaperExecutionOrderCreateRequest,
  type PaperExecutionOrderListResponse,
  type PaperExecutionOrderViewResponse,
  type PaperExecutionReconciliationResponse,
  type PaperExecutionStepCommandResponse,
  type PreTradeRiskDecisionListResponse,
} from "@/lib/api-client";

type CommandError = Readonly<{
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number | null;
}>;

type Resource<Data> =
  | Readonly<{ status: "idle" }>
  | Readonly<{ status: "loading"; previous?: Data }>
  | Readonly<{ status: "success"; data: Data; requestId: string | null }>
  | Readonly<{ status: "error"; error: CommandError; previous?: Data }>;

type Candidate = Readonly<{
  decision: PreTradeRiskDecisionListResponse["items"][number];
  intent: OrderIntentListResponse["items"][number];
}>;

type KeyState = Readonly<{ fingerprint: string; key: string }>;

function commandError(error: unknown): CommandError {
  if (error instanceof ApiClientError) {
    return {
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
      httpStatus: error.status > 0 ? error.status : null,
    };
  }
  return {
    code: "api_unavailable",
    message: "The local API is unavailable.",
    requestId: null,
    httpStatus: null,
  };
}

function fingerprint(value: object): string {
  return JSON.stringify(value);
}

function commandKey(kind: "create" | "step"): string {
  return `s213-${kind}-${globalThis.crypto.randomUUID()}`;
}

function keyFor(fingerprintValue: string, current: KeyState | null, kind: "create" | "step"): KeyState {
  return current?.fingerprint === fingerprintValue
    ? current
    : { fingerprint: fingerprintValue, key: commandKey(kind) };
}

function ExactEvidence({ value, label }: { value: unknown; label: string }) {
  if (Array.isArray(value)) {
    return value.length === 0 ? <code className="raw-value">[]</code> : (
      <ol className="strategy-risk-rules" aria-label={label}>
        {value.map((item, index) => (
          <li key={index}><ExactEvidence value={item} label={`${label} ${index + 1}`} /></li>
        ))}
      </ol>
    );
  }
  if (typeof value === "object" && value !== null) {
    return (
      <dl className="definition-grid definition-grid--wide">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt><code>{key}</code></dt>
            <dd><ExactEvidence value={item} label={key} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return <code className="raw-value">{value === null ? "null" : String(value)}</code>;
}

function OperationError({ error, title, operation, onRetry }: {
  error: CommandError;
  title: string;
  operation: string;
  onRetry?: () => void;
}) {
  const t = useTranslations("paperExecution.actions");
  return (
    <ErrorState
      title={title}
      code={error.code}
      message={error.message}
      requestId={error.requestId}
      httpStatus={error.httpStatus}
      operation={operation}
      onRetry={onRetry}
      retryLabel={t("retryExact")}
    />
  );
}

function EvidenceSection({ title, eyebrow, value }: {
  title: string;
  eyebrow: string;
  value: unknown;
}) {
  return (
    <section className="immutable-evidence">
      <div className="section-heading"><div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div></div>
      <ExactEvidence value={value} label={title} />
    </section>
  );
}

export function PaperExecutionWorkspace() {
  const t = useTranslations("paperExecution");
  const [actor, setActor] = useState("founder");
  const [maxFill, setMaxFill] = useState("");
  const [slippage, setSlippage] = useState("");
  const [commission, setCommission] = useState("");
  const [fee, setFee] = useState("");
  const [buyTax, setBuyTax] = useState("");
  const [sellTax, setSellTax] = useState("");

  const [candidates, setCandidates] = useState<Resource<readonly Candidate[]>>({ status: "idle" });
  const [selectedDecisionId, setSelectedDecisionId] = useState("");
  const [orders, setOrders] = useState<Resource<PaperExecutionOrderListResponse>>({ status: "idle" });
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<Resource<PaperExecutionOrderViewResponse>>({ status: "idle" });
  const [attempts, setAttempts] = useState<Resource<PaperExecutionAttemptListResponse>>({ status: "idle" });
  const [fills, setFills] = useState<Resource<PaperExecutionFillListResponse>>({ status: "idle" });
  const [reconciliation, setReconciliation] = useState<Resource<PaperExecutionReconciliationResponse>>({ status: "idle" });

  const [createPending, setCreatePending] = useState(false);
  const [createError, setCreateError] = useState<CommandError | null>(null);
  const [createResult, setCreateResult] = useState<PaperExecutionOrderCommandResponse | null>(null);
  const [createKey, setCreateKey] = useState<KeyState | null>(null);
  const createPendingRef = useRef(false);

  const [stepPending, setStepPending] = useState(false);
  const [stepError, setStepError] = useState<CommandError | null>(null);
  const [stepResult, setStepResult] = useState<PaperExecutionStepCommandResponse | null>(null);
  const [stepKey, setStepKey] = useState<KeyState | null>(null);
  const stepPendingRef = useRef(false);

  const selectedCandidate = useMemo(
    () => candidates.status === "success"
      ? candidates.data.find((candidate) => candidate.decision.decision_id === selectedDecisionId) ?? null
      : candidates.status === "loading" || candidates.status === "error"
        ? candidates.previous?.find((candidate) => candidate.decision.decision_id === selectedDecisionId) ?? null
        : null,
    [candidates, selectedDecisionId],
  );

  const loadCandidates = useCallback(async () => {
    setCandidates((current) => ({
      status: "loading",
      ...(current.status === "success" ? { previous: current.data } : current.status === "error" && current.previous ? { previous: current.previous } : {}),
    }));
    try {
      const [decisionResult, intentResult] = await Promise.all([
        fetchPreTradeRiskDecisions({ outcome: "allow", limit: 50 }),
        fetchOrderIntents({ limit: 50 }),
      ]);
      const data = decisionResult.data.items.flatMap((decision) => {
        const reference = decision.input_snapshot.intent_reference;
        const intent = intentResult.data.items.find((item) =>
          item.intent_id === reference.intent_id && item.intent_digest === reference.intent_digest,
        );
        return decision.outcome === "allow" && intent ? [{ decision, intent }] : [];
      });
      setCandidates({ status: "success", data, requestId: decisionResult.requestId });
    } catch (error) {
      setCandidates((current) => ({
        status: "error",
        error: commandError(error),
        ...(current.status === "loading" && current.previous ? { previous: current.previous } : {}),
      }));
    }
  }, []);

  const loadOrders = useCallback(async (cursor?: string | null) => {
    setOrders((current) => ({
      status: "loading",
      ...(current.status === "success" ? { previous: current.data } : current.status === "error" && current.previous ? { previous: current.previous } : {}),
    }));
    try {
      const result = await fetchPaperExecutionOrders({ limit: 25, ...(cursor ? { cursor } : {}) });
      setOrders((current) => {
        const prior = cursor && current.status === "loading" ? current.previous : undefined;
        return {
          status: "success",
          data: prior ? { ...result.data, items: [...prior.items, ...result.data.items] } : result.data,
          requestId: result.requestId,
        };
      });
    } catch (error) {
      setOrders((current) => ({
        status: "error",
        error: commandError(error),
        ...(current.status === "loading" && current.previous ? { previous: current.previous } : {}),
      }));
    }
  }, []);

  useEffect(() => {
    void loadCandidates();
    void loadOrders();
  }, [loadCandidates, loadOrders]);

  async function selectOrder(executionOrderId: string) {
    setSelectedOrderId(executionOrderId);
    setStepError(null);
    setStepResult(null);
    setReconciliation({ status: "idle" });
    setSelectedOrder((current) => ({ status: "loading", ...(current.status === "success" ? { previous: current.data } : {}) }));
    setAttempts({ status: "loading" });
    setFills({ status: "loading" });
    const results = await Promise.allSettled([
      fetchPaperExecutionOrderDetail(executionOrderId),
      fetchPaperExecutionAttempts(executionOrderId, { limit: 25 }),
      fetchPaperExecutionFills({ execution_order_id: executionOrderId, limit: 25 }),
    ]);
    const [orderResult, attemptResult, fillResult] = results;
    if (orderResult.status === "fulfilled") {
      setSelectedOrder({ status: "success", data: orderResult.value.data, requestId: orderResult.value.requestId });
    } else {
      setSelectedOrder((current) => ({ status: "error", error: commandError(orderResult.reason), ...(current.status === "loading" && current.previous ? { previous: current.previous } : {}) }));
    }
    setAttempts(attemptResult.status === "fulfilled"
      ? { status: "success", data: attemptResult.value.data, requestId: attemptResult.value.requestId }
      : { status: "error", error: commandError(attemptResult.reason) });
    setFills(fillResult.status === "fulfilled"
      ? { status: "success", data: fillResult.value.data, requestId: fillResult.value.requestId }
      : { status: "error", error: commandError(fillResult.reason) });
  }

  const createRequest = useMemo<PaperExecutionOrderCreateRequest | null>(() => {
    if (!selectedCandidate || actor.length === 0 || [slippage, commission, fee, buyTax, sellTax].some((value) => value.length === 0)) return null;
    return {
      intent: {
        intent_id: selectedCandidate.intent.intent_id,
        intent_digest: selectedCandidate.intent.intent_digest,
      },
      decision: {
        decision_id: selectedCandidate.decision.decision_id,
        decision_digest: selectedCandidate.decision.decision_digest,
      },
      execution_policy: {
        max_fill_quantity_per_trade_event: maxFill.length === 0 ? null : maxFill,
        slippage_bps: slippage,
        commission_bps: commission,
        fee_bps: fee,
        buy_tax_bps: buyTax,
        sell_tax_bps: sellTax,
      },
      actor,
    };
  }, [selectedCandidate, actor, maxFill, slippage, commission, fee, buyTax, sellTax]);

  async function submitCreate() {
    if (!createRequest || createPendingRef.current) return;
    createPendingRef.current = true;
    setCreatePending(true);
    setCreateError(null);
    const requestFingerprint = fingerprint(createRequest);
    const nextKey = keyFor(requestFingerprint, createKey, "create");
    setCreateKey(nextKey);
    try {
      const result = await createPaperExecutionOrder(createRequest, nextKey.key);
      setCreateResult(result.data);
      const view = result.data.result;
      setSelectedOrderId(view.order.execution_order_id);
      setSelectedOrder({ status: "success", data: view, requestId: result.requestId });
      setAttempts({ status: "success", data: { schema_version: 1, items: [], next_cursor: null }, requestId: null });
      setFills({ status: "success", data: { schema_version: 1, items: [], next_cursor: null }, requestId: null });
      setReconciliation({ status: "idle" });
      setOrders((current) => {
        const existing = current.status === "success" ? current.data : current.status === "loading" || current.status === "error" ? current.previous : undefined;
        if (!existing || existing.items.some((item) => item.order.execution_order_id === view.order.execution_order_id)) return current;
        return { status: "success", data: { ...existing, items: [view, ...existing.items] }, requestId: result.requestId };
      });
    } catch (error) {
      setCreateError(commandError(error));
    } finally {
      createPendingRef.current = false;
      setCreatePending(false);
    }
  }

  const activeOrder = selectedOrder.status === "success" ? selectedOrder.data
    : selectedOrder.status === "loading" || selectedOrder.status === "error" ? selectedOrder.previous ?? null : null;

  async function submitStep() {
    if (!activeOrder || activeOrder.state.terminal || actor.length === 0 || stepPendingRef.current) return;
    const request = {
      execution_order_digest: activeOrder.order.execution_order_digest,
      expected_execution_version: activeOrder.state.execution_version,
      actor,
    };
    const requestFingerprint = fingerprint({ execution_order_id: activeOrder.order.execution_order_id, ...request });
    const nextKey = keyFor(requestFingerprint, stepKey, "step");
    stepPendingRef.current = true;
    setStepPending(true);
    setStepError(null);
    setStepKey(nextKey);
    try {
      const result = await stepPaperExecutionOrder(activeOrder.order.execution_order_id, request, nextKey.key);
      setStepResult(result.data);
      const nextView = { order: activeOrder.order, state: result.data.result.order_state };
      setSelectedOrder({ status: "success", data: nextView, requestId: result.requestId });
      setOrders((current) => current.status === "success" ? {
        ...current,
        data: {
          ...current.data,
          items: current.data.items.map((item) => item.order.execution_order_id === activeOrder.order.execution_order_id ? nextView : item),
        },
      } : current);
      setAttempts((current) => current.status === "success" && !current.data.items.some((item) => item.attempt_id === result.data.result.attempt.attempt_id) ? {
        ...current,
        data: { ...current.data, items: [...current.data.items, result.data.result.attempt] },
      } : current);
      if (result.data.result.fill) {
        const nextFill = result.data.result.fill;
        setFills((current) => current.status === "success" && !current.data.items.some((item) => item.fill_id === nextFill.fill_id) ? {
          ...current,
          data: { ...current.data, items: [...current.data.items, nextFill] },
        } : current);
      }
    } catch (error) {
      setStepError(commandError(error));
    } finally {
      stepPendingRef.current = false;
      setStepPending(false);
    }
  }

  async function loadMoreAttempts() {
    if (!activeOrder || attempts.status !== "success" || !attempts.data.next_cursor) return;
    const prior = attempts.data;
    setAttempts({ status: "loading", previous: prior });
    try {
      const result = await fetchPaperExecutionAttempts(activeOrder.order.execution_order_id, { limit: 25, cursor: prior.next_cursor });
      setAttempts({ status: "success", data: { ...result.data, items: [...prior.items, ...result.data.items] }, requestId: result.requestId });
    } catch (error) {
      setAttempts({ status: "error", error: commandError(error), previous: prior });
    }
  }

  async function loadMoreFills() {
    if (!activeOrder || fills.status !== "success" || !fills.data.next_cursor) return;
    const prior = fills.data;
    setFills({ status: "loading", previous: prior });
    try {
      const result = await fetchPaperExecutionFills({ execution_order_id: activeOrder.order.execution_order_id, limit: 25, cursor: prior.next_cursor });
      setFills({ status: "success", data: { ...result.data, items: [...prior.items, ...result.data.items] }, requestId: result.requestId });
    } catch (error) {
      setFills({ status: "error", error: commandError(error), previous: prior });
    }
  }

  async function reconcile() {
    if (!activeOrder || reconciliation.status === "loading") return;
    setReconciliation((current) => ({ status: "loading", ...(current.status === "success" ? { previous: current.data } : current.status === "error" && current.previous ? { previous: current.previous } : {}) }));
    try {
      const result = await fetchPaperExecutionReconciliation(activeOrder.order.execution_order_id);
      setReconciliation({ status: "success", data: result.data, requestId: result.requestId });
    } catch (error) {
      setReconciliation((current) => ({ status: "error", error: commandError(error), ...(current.status === "loading" && current.previous ? { previous: current.previous } : {}) }));
    }
  }

  const orderData = orders.status === "success" ? orders.data : orders.status === "loading" || orders.status === "error" ? orders.previous : undefined;
  const attemptData = attempts.status === "success" ? attempts.data : attempts.status === "loading" || attempts.status === "error" ? attempts.previous : undefined;
  const fillData = fills.status === "success" ? fills.data : fills.status === "loading" || fills.status === "error" ? fills.previous : undefined;
  const candidateData = candidates.status === "success" ? candidates.data
    : candidates.status === "loading" || candidates.status === "error" ? candidates.previous : undefined;

  return (
    <div className="page-stack paper-execution-workspace">
      <section className="page-heading"><p className="eyebrow">{t("eyebrow")}</p><h1>{t("title")}</h1><p>{t("description")}</p></section>
      <aside className="boundary-note"><strong>{t("boundary.title")}</strong><p>{t("boundary.description")}</p></aside>

      <section className="content-panel" aria-labelledby="candidate-title">
        <div className="section-heading"><div><p className="eyebrow">{t("candidate.eyebrow")}</p><h2 id="candidate-title">{t("candidate.title")}</h2></div><p>{t("candidate.description")}</p></div>
        {candidates.status === "loading" && !candidates.previous ? <LoadingState message={t("candidate.loading")} /> : null}
        {candidates.status === "error" ? <OperationError error={candidates.error} title={t("candidate.errorTitle")} operation="strategy_order.historical_allow_list" onRetry={() => void loadCandidates()} /> : null}
        {candidateData ? (
          <label className="form-section">{t("candidate.label")}
            <select value={selectedDecisionId} onChange={(event) => setSelectedDecisionId(event.target.value)}>
              <option value="">{t("candidate.choose")}</option>
              {candidateData.map(({ decision, intent }) => (
                <option key={decision.decision_id} value={decision.decision_id}>{decision.decision_id} · {intent.intent_id}</option>
              ))}
            </select>
          </label>
        ) : null}
        <p className="neutral-note" role="note">{t("candidate.historicalWarning")}</p>
        {selectedCandidate ? <EvidenceSection title={t("candidate.evidenceTitle")} eyebrow={t("candidate.evidenceEyebrow")} value={{ decision_id: selectedCandidate.decision.decision_id, decision_digest: selectedCandidate.decision.decision_digest, outcome: selectedCandidate.decision.outcome, intent_id: selectedCandidate.intent.intent_id, intent_digest: selectedCandidate.intent.intent_digest, decision_created_at: selectedCandidate.decision.created_at }} /> : null}
      </section>

      <section className="content-panel" aria-labelledby="policy-title">
        <div className="section-heading"><div><p className="eyebrow">{t("policy.eyebrow")}</p><h2 id="policy-title">{t("policy.title")}</h2></div><p>{t("policy.description")}</p></div>
        <fieldset className="form-section"><legend>{t("policy.legend")}</legend><p className="field-guidance">{t("policy.draftWarning")}</p>
          <div className="form-grid">
            <label>{t("policy.actor")}<input value={actor} onChange={(event) => setActor(event.target.value)} /></label>
            <label>{t("policy.maxFill")}<input value={maxFill} onChange={(event) => setMaxFill(event.target.value)} aria-describedby="max-fill-null" /><span id="max-fill-null" className="field-guidance">{t("policy.maxFillNull")}</span></label>
            <label>{t("policy.slippage")}<input value={slippage} onChange={(event) => setSlippage(event.target.value)} /></label>
            <label>{t("policy.commission")}<input value={commission} onChange={(event) => setCommission(event.target.value)} /></label>
            <label>{t("policy.fee")}<input value={fee} onChange={(event) => setFee(event.target.value)} /></label>
            <label>{t("policy.buyTax")}<input value={buyTax} onChange={(event) => setBuyTax(event.target.value)} /></label>
            <label>{t("policy.sellTax")}<input value={sellTax} onChange={(event) => setSellTax(event.target.value)} /></label>
          </div>
        </fieldset>
        <div className="submission-actions"><button className="primary-button" type="button" disabled={!createRequest || createPending} aria-busy={createPending} onClick={() => void submitCreate()}>{createPending ? t("create.pending") : t("create.action")}</button><p>{t("create.guidance")}</p></div>
        {createError ? <OperationError error={createError} title={t("create.errorTitle")} operation="paper_execution.order.create" onRetry={() => void submitCreate()} /> : null}
        {createResult ? <EvidenceSection title={createResult.replayed ? t("create.replayedTitle") : t("create.createdTitle")} eyebrow={createResult.replayed ? t("create.replayedEyebrow") : t("create.createdEyebrow")} value={createResult} /> : null}
      </section>

      <section className="content-panel" aria-labelledby="orders-title">
        <div className="section-heading"><div><p className="eyebrow">{t("orders.eyebrow")}</p><h2 id="orders-title">{t("orders.title")}</h2></div><p>{t("orders.description")}</p></div>
        {orders.status === "loading" && !orders.previous ? <LoadingState message={t("orders.loading")} /> : null}
        {orders.status === "error" ? <OperationError error={orders.error} title={t("orders.errorTitle")} operation="paper_execution.order.list" onRetry={() => void loadOrders()} /> : null}
        {orderData ? <ScrollableTable caption={t("orders.caption")}><thead><tr><th>{t("orders.id")}</th><th>{t("orders.account")}</th><th>{t("orders.instrument")}</th><th>{t("orders.side")}</th><th>{t("orders.requested")}</th><th>{t("orders.version")}</th><th>{t("orders.status")}</th><th>{t("orders.filled")}</th><th>{t("orders.remaining")}</th><th>{t("orders.terminal")}</th><th>{t("orders.createdAt")}</th><th>{t("orders.inspect")}</th></tr></thead><tbody>{orderData.items.map((view) => <tr key={view.order.execution_order_id}><td><code className="raw-value">{view.order.execution_order_id}<br />{view.order.execution_order_digest}</code></td><td><code>{view.order.account_id}</code></td><td><code>{view.order.instrument_id}</code></td><td><code>{view.order.side}</code></td><td><code>{view.order.requested_quantity}</code></td><td>{view.state.execution_version}</td><td><code>{view.state.status}</code></td><td><code>{view.state.cumulative_filled_quantity}</code></td><td><code>{view.state.remaining_quantity}</code></td><td><code>{String(view.state.terminal)}</code></td><td><code>{view.order.created_at}</code></td><td><button className="secondary-button" type="button" aria-pressed={selectedOrderId === view.order.execution_order_id} onClick={() => void selectOrder(view.order.execution_order_id)}>{t("orders.inspect")}</button></td></tr>)}</tbody></ScrollableTable> : null}
        {orderData?.next_cursor ? <button className="secondary-button" type="button" disabled={orders.status === "loading"} onClick={() => void loadOrders(orderData.next_cursor)}>{orders.status === "loading" ? t("actions.loadingMore") : t("actions.loadMore")}</button> : null}
      </section>

      {selectedOrder.status === "loading" && !selectedOrder.previous ? <LoadingState message={t("detail.loading")} /> : null}
      {selectedOrder.status === "error" ? <OperationError error={selectedOrder.error} title={t("detail.errorTitle")} operation="paper_execution.order.detail" onRetry={selectedOrderId ? () => void selectOrder(selectedOrderId) : undefined} /> : null}
      {activeOrder ? <section className="content-panel" aria-labelledby="detail-title"><div className="section-heading"><div><p className="eyebrow">{t("detail.eyebrow")}</p><h2 id="detail-title">{t("detail.title")}</h2></div><p>{t("detail.historical")}</p></div><EvidenceSection title={t("detail.authorityTitle")} eyebrow={t("detail.authorityEyebrow")} value={activeOrder} />
        <div className="submission-actions">{!activeOrder.state.terminal ? <button className="primary-button" type="button" disabled={stepPending || actor.length === 0} aria-busy={stepPending} onClick={() => void submitStep()}>{stepPending ? t("step.pending") : t("step.action")}</button> : <p className="neutral-note" role="status">{t("step.terminal")}</p>}<p>{t("step.guidance")}</p></div>
        {stepError ? <OperationError error={stepError} title={t("step.errorTitle")} operation="paper_execution.order.step" onRetry={() => void submitStep()} /> : null}
        {stepResult ? <EvidenceSection title={stepResult.replayed ? t("step.replayedTitle") : t("step.committedTitle")} eyebrow={t("step.resultEyebrow")} value={stepResult} /> : null}
      </section> : null}

      {activeOrder ? <section className="content-panel" aria-labelledby="attempts-title"><div className="section-heading"><div><p className="eyebrow">{t("attempts.eyebrow")}</p><h2 id="attempts-title">{t("attempts.title")}</h2></div><p>{t("attempts.description")}</p></div>
        {attempts.status === "error" ? <OperationError error={attempts.error} title={t("attempts.errorTitle")} operation="paper_execution.attempt.list" onRetry={() => void selectOrder(activeOrder.order.execution_order_id)} /> : null}
        {attemptData?.items.map((attempt) => <EvidenceSection key={attempt.attempt_id} title={t("attempts.itemTitle")} eyebrow={attempt.attempt_result} value={attempt} />)}
        {attemptData?.items.length === 0 ? <p className="neutral-note">{t("attempts.empty")}</p> : null}
        {attemptData?.next_cursor ? <button className="secondary-button" type="button" disabled={attempts.status === "loading"} onClick={() => void loadMoreAttempts()}>{attempts.status === "loading" ? t("actions.loadingMore") : t("actions.loadMore")}</button> : null}
      </section> : null}

      {activeOrder ? <section className="content-panel" aria-labelledby="fills-title"><div className="section-heading"><div><p className="eyebrow">{t("fills.eyebrow")}</p><h2 id="fills-title">{t("fills.title")}</h2></div><p>{t("fills.description")}</p></div>
        {fills.status === "error" ? <OperationError error={fills.error} title={t("fills.errorTitle")} operation="paper_execution.fill.list" onRetry={() => void selectOrder(activeOrder.order.execution_order_id)} /> : null}
        {fillData?.items.map((fillItem) => <EvidenceSection key={fillItem.fill_id} title={t("fills.itemTitle")} eyebrow={fillItem.side} value={fillItem} />)}
        {fillData?.items.length === 0 ? <p className="neutral-note">{t("fills.empty")}</p> : null}
        {fillData?.next_cursor ? <button className="secondary-button" type="button" disabled={fills.status === "loading"} onClick={() => void loadMoreFills()}>{fills.status === "loading" ? t("actions.loadingMore") : t("actions.loadMore")}</button> : null}
      </section> : null}

      {activeOrder ? <section className="content-panel" aria-labelledby="reconciliation-title"><div className="section-heading"><div><p className="eyebrow">{t("reconciliation.eyebrow")}</p><h2 id="reconciliation-title">{t("reconciliation.title")}</h2></div><p>{t("reconciliation.description")}</p></div>
        <button className="secondary-button" type="button" disabled={reconciliation.status === "loading"} aria-busy={reconciliation.status === "loading"} onClick={() => void reconcile()}>{reconciliation.status === "loading" ? t("reconciliation.pending") : t("reconciliation.action")}</button>
        {reconciliation.status === "error" ? <OperationError error={reconciliation.error} title={t("reconciliation.errorTitle")} operation="paper_execution.reconciliation.read" onRetry={() => void reconcile()} /> : null}
        {reconciliation.status === "success" ? <EvidenceSection title={t("reconciliation.successTitle")} eyebrow={t("reconciliation.successEyebrow")} value={reconciliation.data} /> : reconciliation.status === "loading" && reconciliation.previous ? <EvidenceSection title={t("reconciliation.successTitle")} eyebrow={t("reconciliation.previousEyebrow")} value={reconciliation.previous} /> : reconciliation.status === "error" && reconciliation.previous ? <EvidenceSection title={t("reconciliation.successTitle")} eyebrow={t("reconciliation.previousEyebrow")} value={reconciliation.previous} /> : null}
      </section> : null}
    </div>
  );
}
