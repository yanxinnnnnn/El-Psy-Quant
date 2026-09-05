"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { ErrorState, LoadingState, RequestId } from "@/components/data-states";
import { LocalizedTimestamp } from "@/components/localized-values";
import { ScrollableTable } from "@/components/ui/scrollable-table";
import {
  ApiClientError,
  fetchPaperRuntimeAudit,
  fetchPaperRuntimeCheckpoints,
  fetchPaperRuntimeDetail,
  fetchPaperRuntimeHealth,
  fetchPaperRuntimeReconciliation,
  fetchPaperRuntimeWork,
  recoverPaperRuntime,
  resumePaperRuntime,
  startPaperRuntime,
  stopPaperRuntime,
  type PaperRuntimeAuditListResponse,
  type PaperRuntimeCheckpointListResponse,
  type PaperRuntimeCommandResponse,
  type PaperRuntimeHealthResponse,
  type PaperRuntimeReconciliationResponse,
  type PaperRuntimeResponse,
  type PaperRuntimeWorkListResponse,
} from "@/lib/api-client";

type Failure = Readonly<{ code: string; message: string; requestId: string | null; status: number }>;
type Section = "runtime" | "health" | "reconciliation" | "audit" | "work" | "checkpoints";
type Action = "start" | "stop" | "resume" | "recover";
type KeyState = Readonly<{ fingerprint: string; key: string }>;

function failure(error: unknown): Failure {
  return error instanceof ApiClientError
    ? { code: error.code, message: error.publicMessage, requestId: error.requestId, status: error.status }
    : { code: "api_unavailable", message: "The local API is unavailable.", requestId: null, status: 0 };
}

function keyFor(fingerprint: string, current: KeyState | null): KeyState {
  return current?.fingerprint === fingerprint
    ? current
    : { fingerprint, key: `s224-control-${globalThis.crypto.randomUUID()}` };
}

function Raw({ value }: { value: string | number | boolean | null }) {
  return <code className="raw-value">{value === null ? "—" : String(value)}</code>;
}

function SectionFailure({ value, operation, onRetry }: { value?: Failure; operation: string; onRetry: () => void }) {
  const t = useTranslations("paperRuntimes");
  return value ? <ErrorState title={t("detail.sectionError")} code={value.code} message={value.message} requestId={value.requestId} httpStatus={value.status} operation={operation} onRetry={onRetry} /> : null;
}

export function PaperRuntimeDetailView({ runtimeId }: { runtimeId: string }) {
  const t = useTranslations("paperRuntimes");
  const [runtime, setRuntime] = useState<PaperRuntimeResponse | null>(null);
  const [health, setHealth] = useState<PaperRuntimeHealthResponse | null>(null);
  const [reconciliation, setReconciliation] = useState<PaperRuntimeReconciliationResponse | null>(null);
  const [audit, setAudit] = useState<PaperRuntimeAuditListResponse | null>(null);
  const [work, setWork] = useState<PaperRuntimeWorkListResponse | null>(null);
  const [checkpoints, setCheckpoints] = useState<PaperRuntimeCheckpointListResponse | null>(null);
  const [failures, setFailures] = useState<Partial<Record<Section, Failure>>>({});
  const [refreshing, setRefreshing] = useState(false);
  const [actor, setActor] = useState("founder");
  const [commandPending, setCommandPending] = useState(false);
  const [commandFailure, setCommandFailure] = useState<Failure | null>(null);
  const [commandResult, setCommandResult] = useState<PaperRuntimeCommandResponse | null>(null);
  const [lastAction, setLastAction] = useState<Action | null>(null);
  const [keyState, setKeyState] = useState<KeyState | null>(null);
  const refreshSequence = useRef(0);
  const evidenceGeneration = useRef(0);
  const commandPendingRef = useRef(false);
  const auditSequence = useRef(0);
  const workSequence = useRef(0);
  const checkpointSequence = useRef(0);

  const clearFailure = useCallback((section: Section) => setFailures((current) => {
    const next = { ...current }; delete next[section]; return next;
  }), []);
  const setSectionFailure = useCallback((section: Section, caught: unknown) => setFailures((current) => ({ ...current, [section]: failure(caught) })), []);

  const refresh = useCallback(async (includeRuntime = true) => {
    const sequence = ++refreshSequence.current;
    evidenceGeneration.current += 1;
    setRefreshing(true);
    const reads: Promise<void>[] = [];
    if (includeRuntime) reads.push(fetchPaperRuntimeDetail(runtimeId).then((result) => {
      if (sequence === refreshSequence.current) { setRuntime(result.data); clearFailure("runtime"); }
    }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("runtime", caught); }));
    reads.push(
      fetchPaperRuntimeHealth(runtimeId).then((result) => { if (sequence === refreshSequence.current) { setHealth(result.data); clearFailure("health"); } }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("health", caught); }),
      fetchPaperRuntimeReconciliation(runtimeId).then((result) => { if (sequence === refreshSequence.current) { setReconciliation(result.data); clearFailure("reconciliation"); } }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("reconciliation", caught); }),
      fetchPaperRuntimeAudit(runtimeId, { limit: 25 }).then((result) => { if (sequence === refreshSequence.current) { setAudit(result.data); clearFailure("audit"); } }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("audit", caught); }),
      fetchPaperRuntimeWork(runtimeId, { limit: 25 }).then((result) => { if (sequence === refreshSequence.current) { setWork(result.data); clearFailure("work"); } }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("work", caught); }),
      fetchPaperRuntimeCheckpoints(runtimeId, { limit: 25 }).then((result) => { if (sequence === refreshSequence.current) { setCheckpoints(result.data); clearFailure("checkpoints"); } }).catch((caught) => { if (sequence === refreshSequence.current) setSectionFailure("checkpoints", caught); }),
    );
    await Promise.all(reads);
    if (sequence === refreshSequence.current) setRefreshing(false);
  }, [clearFailure, runtimeId, setSectionFailure]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh(true);
    return () => {
      refreshSequence.current += 1;
      evidenceGeneration.current += 1;
    };
  }, [refresh]);

  async function loadMoreAudit() {
    if (!audit?.next_cursor) return;
    const sequence = ++auditSequence.current;
    const generation = evidenceGeneration.current;
    try { const result = await fetchPaperRuntimeAudit(runtimeId, { limit: 25, cursor: audit.next_cursor }); if (generation === evidenceGeneration.current && sequence === auditSequence.current) { setAudit({ ...result.data, items: [...audit.items, ...result.data.items] }); clearFailure("audit"); } } catch (caught) { if (generation === evidenceGeneration.current && sequence === auditSequence.current) setSectionFailure("audit", caught); }
  }
  async function loadMoreWork() {
    if (!work?.next_cursor) return;
    const sequence = ++workSequence.current;
    const generation = evidenceGeneration.current;
    try { const result = await fetchPaperRuntimeWork(runtimeId, { limit: 25, cursor: work.next_cursor }); if (generation === evidenceGeneration.current && sequence === workSequence.current) { setWork({ ...result.data, items: [...work.items, ...result.data.items] }); clearFailure("work"); } } catch (caught) { if (generation === evidenceGeneration.current && sequence === workSequence.current) setSectionFailure("work", caught); }
  }
  async function loadMoreCheckpoints() {
    if (!checkpoints?.next_cursor) return;
    const sequence = ++checkpointSequence.current;
    const generation = evidenceGeneration.current;
    try { const result = await fetchPaperRuntimeCheckpoints(runtimeId, { limit: 25, cursor: checkpoints.next_cursor }); if (generation === evidenceGeneration.current && sequence === checkpointSequence.current) { setCheckpoints({ ...result.data, items: [...checkpoints.items, ...result.data.items] }); clearFailure("checkpoints"); } } catch (caught) { if (generation === evidenceGeneration.current && sequence === checkpointSequence.current) setSectionFailure("checkpoints", caught); }
  }

  async function command(action: Action) {
    if (!runtime || commandPendingRef.current) return;
    const request = { runtime_binding_digest: runtime.runtime_binding_digest, expected_runtime_version: runtime.row_version, actor };
    const fingerprint = JSON.stringify({ action, runtime_id: runtime.runtime_id, ...request });
    const nextKey = keyFor(fingerprint, keyState);
    setKeyState(nextKey);
    setCommandFailure(null);
    setCommandResult(null);
    setLastAction(action);
    commandPendingRef.current = true;
    setCommandPending(true);
    try {
      const invoke = action === "start" ? startPaperRuntime : action === "stop" ? stopPaperRuntime : action === "resume" ? resumePaperRuntime : recoverPaperRuntime;
      const result = await invoke(runtime.runtime_id, request, nextKey.key);
      refreshSequence.current += 1;
      setRuntime(result.data.runtime);
      setCommandResult(result.data);
      await refresh(false);
    } catch (caught) {
      setCommandFailure(failure(caught));
    } finally {
      commandPendingRef.current = false;
      setCommandPending(false);
    }
  }

  const terminal = runtime?.observed_state === "completed" || runtime?.observed_state === "blocked";
  const showStart = !terminal && runtime?.desired_state === "stopped" && runtime.observed_state === "ready";
  const showStop = !terminal && runtime?.desired_state === "running" && ["ready", "running", "stopped"].includes(runtime.observed_state);
  const showResume = !terminal && runtime?.desired_state === "stopped" && runtime.observed_state === "stopped";
  const showRecover = !terminal && runtime?.desired_state === "running" && ["ready", "running"].includes(runtime.observed_state) && health !== null && health.lease_status !== "active";

  if (!runtime && refreshing && !failures.runtime) return <LoadingState message={t("detail.loading")} />;

  return <div className="business-workspace">
    <header className="page-heading page-heading--with-action"><div><p className="eyebrow">{t("detail.eyebrow")}</p><h1>{t("detail.title")}</h1><p><code className="raw-value">{runtimeId}</code></p><Link className="text-link" href="/paper-runtimes">{t("detail.back")}</Link></div><button className="secondary-button" type="button" disabled={refreshing || commandPending} onClick={() => void refresh(true)}>{refreshing ? t("actions.refreshing") : t("actions.refresh")}</button></header>
    <aside className="boundary-note" aria-label={t("common.authorityTitle")}><strong>{t("common.authorityTitle")}</strong><p>{t("detail.authority")}</p></aside>
    <SectionFailure value={failures.runtime} operation="paper_runtime.detail" onRetry={() => void refresh(true)} />
    {runtime ? <>
      <section className="content-panel" aria-labelledby="runtime-binding"><div className="section-heading"><div><p className="eyebrow">{t("detail.bindingEyebrow")}</p><h2 id="runtime-binding">{t("detail.bindingTitle")}</h2></div><p>{t("detail.bindingDescription")}</p></div><dl className="definition-grid definition-grid--wide">
        <div><dt>{t("fields.runtime_id")}</dt><dd><Raw value={runtime.runtime_id} /></dd></div><div><dt>{t("fields.runtime_binding_digest")}</dt><dd><Raw value={runtime.runtime_binding_digest} /></dd></div><div><dt>{t("fields.execution_order_id")}</dt><dd><Raw value={runtime.execution_order_id} /></dd></div><div><dt>{t("fields.execution_order_digest")}</dt><dd><Raw value={runtime.execution_order_digest} /></dd></div><div><dt>{t("fields.account_id")}</dt><dd><Raw value={runtime.account_id} /></dd></div><div><dt>{t("fields.replay_id")}</dt><dd><Raw value={runtime.replay_id} /></dd></div><div><dt>{t("fields.trading_session_id")}</dt><dd><Raw value={runtime.trading_session_id} /></dd></div><div><dt>{t("fields.logical_actor")}</dt><dd><Raw value={runtime.logical_actor} /></dd></div><div><dt>{t("fields.runtime_policy_id")}</dt><dd><Raw value={runtime.runtime_policy_id} /></dd></div><div><dt>{t("fields.runtime_policy_version")}</dt><dd>{runtime.runtime_policy_version}</dd></div><div><dt>{t("fields.created_at")}</dt><dd><LocalizedTimestamp value={runtime.created_at} /></dd></div><div><dt>{t("fields.updated_at")}</dt><dd><LocalizedTimestamp value={runtime.updated_at} /></dd></div>
      </dl></section>
      <section className="content-panel" aria-labelledby="runtime-lifecycle"><div className="section-heading"><div><p className="eyebrow">{t("detail.lifecycleEyebrow")}</p><h2 id="runtime-lifecycle">{t("detail.lifecycleTitle")}</h2></div><p>{t("detail.lifecycleDescription")}</p></div><div className="summary-grid"><article className="summary-card"><p className="eyebrow">{t("common.requestedState")}</p><h3><Raw value={runtime.desired_state} /></h3><p>{t("detail.requestedHelp")}</p></article><article className="summary-card"><p className="eyebrow">{t("common.observedRuntime")}</p><h3><Raw value={runtime.observed_state} /></h3><p>{t("detail.observedHelp")}</p></article></div><dl className="compact-definitions"><div><dt>{t("fields.row_version")}</dt><dd>{runtime.row_version}</dd></div><div><dt>{t("fields.fencing_token")}</dt><dd>{runtime.fencing_token}</dd></div><div><dt>{t("fields.block_reason_code")}</dt><dd><Raw value={runtime.block_reason_code} /></dd></div></dl></section>
      <section className="content-panel" aria-labelledby="runtime-controls"><div className="section-heading"><div><p className="eyebrow">{t("controls.eyebrow")}</p><h2 id="runtime-controls">{t("controls.title")}</h2></div><p>{t("controls.description")}</p></div><label>{t("fields.actor")}<input value={actor} maxLength={256} onChange={(event) => setActor(event.target.value)} /></label><div className="submission-actions">{showStart ? <button className="primary-button" type="button" disabled={commandPending} onClick={() => void command("start")}>{t("controls.start")}</button> : null}{showStop ? <button className="secondary-button" type="button" disabled={commandPending} onClick={() => void command("stop")}>{t("controls.stop")}</button> : null}{showResume ? <button className="primary-button" type="button" disabled={commandPending} onClick={() => void command("resume")}>{t("controls.resume")}</button> : null}{showRecover ? <button className="secondary-button" type="button" disabled={commandPending} onClick={() => void command("recover")}>{t("controls.recover")}</button> : null}{terminal ? <p className="neutral-note">{t("controls.inspectionOnly")}</p> : null}</div><p>{t("controls.stopCooperative")}</p><p>{t("controls.runnerNotice")}</p></section>
      {commandFailure ? <ErrorState title={t("controls.errorTitle")} code={commandFailure.code} message={commandFailure.message} requestId={commandFailure.requestId} httpStatus={commandFailure.status} operation={`paper_runtime.${lastAction ?? "control"}`} onRetry={lastAction ? () => void command(lastAction) : undefined} retryLabel={t("actions.retryExact")} /> : null}
      {commandResult ? <section className="state-panel state-panel--success" role="status"><p className="eyebrow">{commandResult.replayed ? t("controls.replayed") : t("controls.accepted")}</p><h2>{lastAction === "recover" ? t("controls.recoveryRequested") : t("controls.intentRecorded")}</h2><p>{t("controls.noExecutionProof")}</p><RequestId value={commandResult.request_id} /></section> : null}
    </> : null}
    <section className="content-panel" aria-labelledby="runtime-health"><div className="section-heading"><div><p className="eyebrow">{t("detail.healthEyebrow")}</p><h2 id="runtime-health">{t("detail.healthTitle")}</h2></div><p>{t("detail.healthDescription")}</p></div><SectionFailure value={failures.health} operation="paper_runtime.health" onRetry={() => void refresh(false)} />{health ? <dl className="definition-grid definition-grid--wide"><div><dt>{t("fields.claimed")}</dt><dd><Raw value={health.claimed} /></dd></div><div><dt>{t("fields.lease_status")}</dt><dd><Raw value={health.lease_status} /></dd></div><div><dt>{t("fields.claimed_at")}</dt><dd>{health.claimed_at ? <LocalizedTimestamp value={health.claimed_at} /> : <Raw value={null} />}</dd></div><div><dt>{t("fields.heartbeat_at")}</dt><dd>{health.heartbeat_at ? <LocalizedTimestamp value={health.heartbeat_at} /> : <Raw value={null} />}</dd></div><div><dt>{t("fields.lease_expires_at")}</dt><dd>{health.lease_expires_at ? <LocalizedTimestamp value={health.lease_expires_at} /> : <Raw value={null} />}</dd></div><div><dt>{t("fields.terminal")}</dt><dd><Raw value={health.terminal} /></dd></div><div><dt>{t("fields.blocked")}</dt><dd><Raw value={health.blocked} /></dd></div><div><dt>{t("fields.checked_at")}</dt><dd><LocalizedTimestamp value={health.checked_at} /></dd></div></dl> : null}</section>
    <section className="content-panel" aria-labelledby="runtime-reconciliation"><div className="section-heading"><div><p className="eyebrow">{t("detail.reconciliationEyebrow")}</p><h2 id="runtime-reconciliation">{t("detail.reconciliationTitle")}</h2></div><p>{t("detail.reconciliationDescription")}</p></div><SectionFailure value={failures.reconciliation} operation="paper_runtime.reconciliation" onRetry={() => void refresh(false)} />{reconciliation ? <dl className="definition-grid definition-grid--wide"><div><dt>{t("fields.historical_coherent")}</dt><dd><Raw value={reconciliation.historical_coherent} /></dd></div><div><dt>{t("fields.reconciliation_status")}</dt><dd><Raw value={reconciliation.status} /></dd></div><div><dt>{t("fields.continuation_status")}</dt><dd><Raw value={reconciliation.continuation_status} /></dd></div><div><dt>{t("fields.execution_version")}</dt><dd>{reconciliation.execution_version}</dd></div><div><dt>{t("fields.execution_terminal")}</dt><dd><Raw value={reconciliation.execution_terminal} /></dd></div><div><dt>{t("fields.work_count")}</dt><dd>{reconciliation.work_count}</dd></div><div><dt>{t("fields.checkpoint_count")}</dt><dd>{reconciliation.checkpoint_count}</dd></div><div><dt>{t("fields.event_count")}</dt><dd>{reconciliation.event_count}</dd></div><div><dt>{t("fields.pending_work_id")}</dt><dd><Raw value={reconciliation.pending_work_id} /></dd></div></dl> : null}{reconciliation?.status === "continuation_stale" ? <p className="attention-note">{t("detail.continuationStale")}</p> : null}</section>
    <section className="content-panel" aria-labelledby="runtime-audit"><div className="section-heading"><div><p className="eyebrow">{t("evidence.eyebrow")}</p><h2 id="runtime-audit">{t("evidence.auditTitle")}</h2></div><p>{t("evidence.auditDescription")}</p></div><SectionFailure value={failures.audit} operation="paper_runtime.audit" onRetry={() => void refresh(false)} />{audit ? <ScrollableTable caption={t("evidence.auditCaption")}><thead><tr>{(["event_sequence", "event_type", "resulting_runtime_version", "recorded_at", "work_id", "checkpoint_id", "event_id"] as const).map((field) => <th key={field}>{t(`fields.${field}`)}</th>)}</tr></thead><tbody>{audit.items.map((item, index) => <tr key={`${item.event_id}-${index}`}><td>{item.event_sequence}</td><td><Raw value={item.event_type} /></td><td>{item.resulting_runtime_version}</td><td><LocalizedTimestamp value={item.recorded_at} /></td><td><Raw value={item.work_id} /></td><td><Raw value={item.checkpoint_id} /></td><td><Raw value={item.event_id} /><br /><Raw value={item.event_digest} /></td></tr>)}</tbody></ScrollableTable> : null}{audit?.next_cursor ? <button className="secondary-button" type="button" disabled={refreshing} onClick={() => void loadMoreAudit()}>{t("actions.loadMore")}</button> : null}</section>
    <section className="content-panel" aria-labelledby="runtime-work"><div className="section-heading"><div><p className="eyebrow">{t("evidence.eyebrow")}</p><h2 id="runtime-work">{t("evidence.workTitle")}</h2></div><p>{t("evidence.workDescription")}</p></div><SectionFailure value={failures.work} operation="paper_runtime.work" onRetry={() => void refresh(false)} />{work ? <ScrollableTable caption={t("evidence.workCaption")}><thead><tr>{(["work_id", "execution_order_id", "expected_execution_version", "m34_step_idempotency_key", "m34_step_actor", "created_at"] as const).map((field) => <th key={field}>{t(`fields.${field}`)}</th>)}</tr></thead><tbody>{work.items.map((item, index) => <tr key={`${item.work_id}-${index}`}><td><Raw value={item.work_id} /><br /><Raw value={item.work_digest} /></td><td><Raw value={item.execution_order_id} /><br /><Raw value={item.execution_order_digest} /></td><td>{item.expected_execution_version}</td><td><Raw value={item.m34_step_idempotency_key} /></td><td><Raw value={item.m34_step_actor} /></td><td><LocalizedTimestamp value={item.created_at} /></td></tr>)}</tbody></ScrollableTable> : null}{work?.next_cursor ? <button className="secondary-button" type="button" disabled={refreshing} onClick={() => void loadMoreWork()}>{t("actions.loadMore")}</button> : null}</section>
    <section className="content-panel" aria-labelledby="runtime-checkpoints"><div className="section-heading"><div><p className="eyebrow">{t("evidence.eyebrow")}</p><h2 id="runtime-checkpoints">{t("evidence.checkpointsTitle")}</h2></div><p>{t("evidence.checkpointsDescription")}</p></div><SectionFailure value={failures.checkpoints} operation="paper_runtime.checkpoints" onRetry={() => void refresh(false)} />{checkpoints ? <ScrollableTable caption={t("evidence.checkpointsCaption")}><thead><tr>{(["checkpoint_id", "work_id", "observed_execution_version", "attempt_id", "fill_id", "settlement_link_id", "account_event_id", "replay_id", "post_cursor_position", "post_cursor_last_event_id", "observed_at"] as const).map((field) => <th key={field}>{t(`fields.${field}`)}</th>)}</tr></thead><tbody>{checkpoints.items.map((item, index) => <tr key={`${item.checkpoint_id}-${index}`}><td><Raw value={item.checkpoint_id} /><br /><Raw value={item.checkpoint_digest} /></td><td><Raw value={item.work_id} /></td><td>{item.observed_execution_version}</td><td><Raw value={item.attempt_id} /><br /><Raw value={item.attempt_digest} /></td><td><Raw value={item.fill_id} /><br /><Raw value={item.fill_digest} /></td><td><Raw value={item.settlement_link_id} /><br /><Raw value={item.settlement_link_evidence_digest} /></td><td><Raw value={item.account_event_id} /></td><td><Raw value={item.replay_id} /><br /><Raw value={item.event_stream_digest} /></td><td>{item.post_cursor_position}</td><td><Raw value={item.post_cursor_last_event_id} /></td><td><LocalizedTimestamp value={item.observed_at} /></td></tr>)}</tbody></ScrollableTable> : null}{checkpoints?.next_cursor ? <button className="secondary-button" type="button" disabled={refreshing} onClick={() => void loadMoreCheckpoints()}>{t("actions.loadMore")}</button> : null}</section>
  </div>;
}
