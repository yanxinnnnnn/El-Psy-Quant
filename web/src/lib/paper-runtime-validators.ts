import type {
  PaperRuntimeAuditListResponse,
  PaperRuntimeCheckpointListResponse,
  PaperRuntimeCommandResponse,
  PaperRuntimeHealthResponse,
  PaperRuntimeListResponse,
  PaperRuntimeReconciliationResponse,
  PaperRuntimeResponse,
  PaperRuntimeWorkListResponse,
} from "@/lib/api-client";

type RecordValue = Record<string, unknown>;

const DIGEST = /^[0-9a-f]{64}$/;
const RUNTIME_ID = /^prt_[0-9a-f]{64}$/;
const ORDER_ID = /^peo_[0-9a-f]{64}$/;
const WORK_ID = /^prw_[0-9a-f]{64}$/;
const CHECKPOINT_ID = /^prc_[0-9a-f]{64}$/;
const EVENT_ID = /^pre_[0-9a-f]{64}$/;
const REASON_CODE = /^[a-z0-9_]+$/;

function object(value: unknown): value is RecordValue {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: RecordValue, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  return actual.length === keys.length
    && keys.slice().sort().every((key, index) => key === actual[index]);
}

function bounded(value: unknown, maximum = 512): value is string {
  return typeof value === "string"
    && value.length > 0
    && value.length <= maximum
    && value === value.trim();
}

function nullableBounded(value: unknown, maximum = 512): boolean {
  return value === null || bounded(value, maximum);
}

function digest(value: unknown): value is string {
  return typeof value === "string" && DIGEST.test(value);
}

function nonnegativeInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) >= 0;
}

function positiveInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) > 0;
}

function timestamp(value: unknown): value is string {
  if (typeof value !== "string" || !value.endsWith("Z")) return false;
  return Number.isFinite(Date.parse(value));
}

function nullableTimestamp(value: unknown): boolean {
  return value === null || timestamp(value);
}

function cursor(value: unknown): boolean {
  return value === null || (typeof value === "string" && value.length <= 2048);
}

function desired(value: unknown): boolean {
  return value === "running" || value === "stopped";
}

function observed(value: unknown): boolean {
  return ["ready", "running", "stopped", "completed", "blocked"].includes(String(value));
}

function reason(value: unknown): boolean {
  return value === null || (typeof value === "string" && value.length <= 128 && REASON_CODE.test(value));
}

export function isPaperRuntimeResponse(value: unknown): value is PaperRuntimeResponse {
  return object(value)
    && exactKeys(value, [
      "schema_version", "runtime_id", "runtime_binding_digest",
      "execution_order_id", "execution_order_digest", "account_id", "replay_id",
      "trading_session_id", "logical_actor", "runtime_policy_id",
      "runtime_policy_version", "desired_state", "observed_state", "owner_id",
      "fencing_token", "claimed_at", "heartbeat_at", "lease_expires_at",
      "row_version", "block_reason_code", "created_at", "updated_at",
    ])
    && value.schema_version === 1
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && digest(value.runtime_binding_digest)
    && typeof value.execution_order_id === "string" && ORDER_ID.test(value.execution_order_id)
    && digest(value.execution_order_digest)
    && bounded(value.account_id)
    && bounded(value.replay_id)
    && bounded(value.trading_session_id)
    && bounded(value.logical_actor, 256)
    && bounded(value.runtime_policy_id, 128)
    && nonnegativeInteger(value.runtime_policy_version)
    && desired(value.desired_state)
    && observed(value.observed_state)
    && nullableBounded(value.owner_id, 256)
    && nonnegativeInteger(value.fencing_token)
    && nullableTimestamp(value.claimed_at)
    && nullableTimestamp(value.heartbeat_at)
    && nullableTimestamp(value.lease_expires_at)
    && nonnegativeInteger(value.row_version)
    && reason(value.block_reason_code)
    && timestamp(value.created_at)
    && timestamp(value.updated_at);
}

export function isPaperRuntimeCommandResponse(value: unknown): value is PaperRuntimeCommandResponse {
  return object(value)
    && exactKeys(value, ["schema_version", "replayed", "request_id", "runtime"])
    && value.schema_version === 1
    && typeof value.replayed === "boolean"
    && bounded(value.request_id, 128)
    && isPaperRuntimeResponse(value.runtime);
}

export function isPaperRuntimeListResponse(value: unknown): value is PaperRuntimeListResponse {
  return object(value)
    && exactKeys(value, ["schema_version", "items", "next_cursor"])
    && value.schema_version === 1
    && Array.isArray(value.items)
    && value.items.every(isPaperRuntimeResponse)
    && cursor(value.next_cursor);
}

export function isPaperRuntimeHealthResponse(value: unknown): value is PaperRuntimeHealthResponse {
  return object(value)
    && exactKeys(value, [
      "schema_version", "runtime_id", "desired_state", "observed_state",
      "row_version", "fencing_token", "claimed", "lease_status", "claimed_at",
      "heartbeat_at", "lease_expires_at", "terminal", "blocked",
      "block_reason_code", "checked_at",
    ])
    && value.schema_version === 1
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && desired(value.desired_state)
    && observed(value.observed_state)
    && nonnegativeInteger(value.row_version)
    && nonnegativeInteger(value.fencing_token)
    && typeof value.claimed === "boolean"
    && ["unowned", "active", "expired"].includes(String(value.lease_status))
    && nullableTimestamp(value.claimed_at)
    && nullableTimestamp(value.heartbeat_at)
    && nullableTimestamp(value.lease_expires_at)
    && typeof value.terminal === "boolean"
    && typeof value.blocked === "boolean"
    && reason(value.block_reason_code)
    && timestamp(value.checked_at);
}

export function isPaperRuntimeReconciliationResponse(value: unknown): value is PaperRuntimeReconciliationResponse {
  return object(value)
    && exactKeys(value, [
      "schema_version", "runtime_id", "runtime_binding_digest", "status",
      "historical_coherent", "continuation_status", "execution_order_id",
      "execution_order_digest", "execution_version", "execution_terminal",
      "work_count", "checkpoint_count", "event_count", "pending_work_id",
    ])
    && value.schema_version === 1
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && digest(value.runtime_binding_digest)
    && ["coherent_nonterminal", "coherent_terminal", "coherent_stopped", "blocked", "continuation_stale"].includes(String(value.status))
    && value.historical_coherent === true
    && ["current", "stale", "not_applicable"].includes(String(value.continuation_status))
    && typeof value.execution_order_id === "string" && ORDER_ID.test(value.execution_order_id)
    && digest(value.execution_order_digest)
    && nonnegativeInteger(value.execution_version)
    && typeof value.execution_terminal === "boolean"
    && nonnegativeInteger(value.work_count)
    && nonnegativeInteger(value.checkpoint_count)
    && nonnegativeInteger(value.event_count)
    && (value.pending_work_id === null || (typeof value.pending_work_id === "string" && WORK_ID.test(value.pending_work_id)));
}

function auditEntry(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "event_id", "event_digest", "runtime_id", "event_sequence",
      "event_type", "resulting_runtime_version", "recorded_at", "work_id", "checkpoint_id",
    ])
    && value.schema_version === 1
    && typeof value.event_id === "string" && EVENT_ID.test(value.event_id)
    && digest(value.event_digest)
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && nonnegativeInteger(value.event_sequence)
    && ["runtime_created", "start_requested", "stop_requested", "resume_requested", "recover_requested", "claim_acquired", "claim_released", "claim_taken_over", "work_created", "work_observed", "runtime_completed", "runtime_blocked"].includes(String(value.event_type))
    && nonnegativeInteger(value.resulting_runtime_version)
    && timestamp(value.recorded_at)
    && (value.work_id === null || (typeof value.work_id === "string" && WORK_ID.test(value.work_id)))
    && (value.checkpoint_id === null || (typeof value.checkpoint_id === "string" && CHECKPOINT_ID.test(value.checkpoint_id)));
}

function work(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "work_id", "work_digest", "runtime_id", "execution_order_id",
      "execution_order_digest", "expected_execution_version", "m34_step_idempotency_key",
      "m34_step_actor", "created_at",
    ])
    && value.schema_version === 1
    && typeof value.work_id === "string" && WORK_ID.test(value.work_id)
    && digest(value.work_digest)
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && typeof value.execution_order_id === "string" && ORDER_ID.test(value.execution_order_id)
    && digest(value.execution_order_digest)
    && nonnegativeInteger(value.expected_execution_version)
    && bounded(value.m34_step_idempotency_key, 128)
    && bounded(value.m34_step_actor, 256)
    && timestamp(value.created_at);
}

function checkpoint(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "checkpoint_id", "checkpoint_digest", "runtime_id", "work_id",
      "execution_order_id", "execution_order_digest", "observed_execution_version",
      "attempt_id", "attempt_digest", "fill_id", "fill_digest", "settlement_link_id",
      "settlement_link_evidence_digest", "account_event_id", "replay_id",
      "event_stream_digest", "post_cursor_position", "post_cursor_last_event_id", "observed_at",
    ])
    && value.schema_version === 1
    && typeof value.checkpoint_id === "string" && CHECKPOINT_ID.test(value.checkpoint_id)
    && digest(value.checkpoint_digest)
    && typeof value.runtime_id === "string" && RUNTIME_ID.test(value.runtime_id)
    && typeof value.work_id === "string" && WORK_ID.test(value.work_id)
    && typeof value.execution_order_id === "string" && ORDER_ID.test(value.execution_order_id)
    && digest(value.execution_order_digest)
    && positiveInteger(value.observed_execution_version)
    && bounded(value.attempt_id)
    && digest(value.attempt_digest)
    && nullableBounded(value.fill_id)
    && (value.fill_digest === null || digest(value.fill_digest))
    && nullableBounded(value.settlement_link_id)
    && (value.settlement_link_evidence_digest === null || digest(value.settlement_link_evidence_digest))
    && nullableBounded(value.account_event_id)
    && bounded(value.replay_id)
    && digest(value.event_stream_digest)
    && nonnegativeInteger(value.post_cursor_position)
    && nullableBounded(value.post_cursor_last_event_id)
    && timestamp(value.observed_at);
}

function list(value: unknown, itemValidator: (item: unknown) => boolean): boolean {
  return object(value)
    && exactKeys(value, ["schema_version", "items", "next_cursor"])
    && value.schema_version === 1
    && Array.isArray(value.items)
    && value.items.every(itemValidator)
    && cursor(value.next_cursor);
}

export function isPaperRuntimeAuditListResponse(value: unknown): value is PaperRuntimeAuditListResponse {
  return list(value, auditEntry);
}

export function isPaperRuntimeWorkListResponse(value: unknown): value is PaperRuntimeWorkListResponse {
  return list(value, work);
}

export function isPaperRuntimeCheckpointListResponse(value: unknown): value is PaperRuntimeCheckpointListResponse {
  return list(value, checkpoint);
}
