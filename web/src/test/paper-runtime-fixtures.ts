import type {
  PaperRuntimeAuditListResponse,
  PaperRuntimeCheckpointListResponse,
  PaperRuntimeCommandResponse,
  PaperRuntimeHealthResponse,
  PaperRuntimeReconciliationResponse,
  PaperRuntimeResponse,
  PaperRuntimeWorkListResponse,
} from "@/lib/api-client";
import { executionRaw } from "@/test/paper-execution-fixtures";
import { raw } from "@/test/strategy-order-fixtures";

const digest = (character: string) => character.repeat(64);

export const runtimeRaw = {
  runtimeId: `prt_${digest("1")}`,
  runtimeDigest: digest("2"),
  workId: `prw_${digest("3")}`,
  checkpointId: `prc_${digest("4")}`,
  eventId: `pre_${digest("5")}`,
  cursor: "opaque+/=runtime:下一页",
  requestId: "request-s224-exact",
} as const;

export const paperRuntime = {
  schema_version: 1,
  runtime_id: runtimeRaw.runtimeId,
  runtime_binding_digest: runtimeRaw.runtimeDigest,
  execution_order_id: executionRaw.orderId,
  execution_order_digest: executionRaw.orderDigest,
  account_id: raw.accountId,
  replay_id: raw.replayId,
  trading_session_id: raw.sessionId,
  logical_actor: "founder-paper-runtime",
  runtime_policy_id: "durable-runtime-v1",
  runtime_policy_version: 1,
  desired_state: "stopped",
  observed_state: "ready",
  owner_id: null,
  fencing_token: 0,
  claimed_at: null,
  heartbeat_at: null,
  lease_expires_at: null,
  row_version: 0,
  block_reason_code: null,
  created_at: "2026-08-28T01:00:00Z",
  updated_at: "2026-08-28T01:00:00Z",
} as const satisfies PaperRuntimeResponse;

export const paperRuntimeHealth = {
  schema_version: 1,
  runtime_id: runtimeRaw.runtimeId,
  desired_state: "stopped",
  observed_state: "ready",
  row_version: 0,
  fencing_token: 0,
  claimed: false,
  lease_status: "unowned",
  claimed_at: null,
  heartbeat_at: null,
  lease_expires_at: null,
  terminal: false,
  blocked: false,
  block_reason_code: null,
  checked_at: "2026-08-28T01:01:00Z",
} as const satisfies PaperRuntimeHealthResponse;

export const paperRuntimeReconciliation = {
  schema_version: 1,
  runtime_id: runtimeRaw.runtimeId,
  runtime_binding_digest: runtimeRaw.runtimeDigest,
  status: "coherent_nonterminal",
  historical_coherent: true,
  continuation_status: "current",
  execution_order_id: executionRaw.orderId,
  execution_order_digest: executionRaw.orderDigest,
  execution_version: 0,
  execution_terminal: false,
  work_count: 0,
  checkpoint_count: 0,
  event_count: 1,
  pending_work_id: null,
} as const satisfies PaperRuntimeReconciliationResponse;

export const paperRuntimeAudit = {
  schema_version: 1,
  items: [{
    schema_version: 1,
    event_id: runtimeRaw.eventId,
    event_digest: digest("6"),
    runtime_id: runtimeRaw.runtimeId,
    event_sequence: 0,
    event_type: "runtime_created",
    resulting_runtime_version: 0,
    recorded_at: "2026-08-28T01:00:00Z",
    work_id: null,
    checkpoint_id: null,
  }],
  next_cursor: null,
} as const satisfies PaperRuntimeAuditListResponse;

export const paperRuntimeWork = {
  schema_version: 1,
  items: [{
    schema_version: 1,
    work_id: runtimeRaw.workId,
    work_digest: digest("7"),
    runtime_id: runtimeRaw.runtimeId,
    execution_order_id: executionRaw.orderId,
    execution_order_digest: executionRaw.orderDigest,
    expected_execution_version: 0,
    m34_step_idempotency_key: "runtime-step-exact-key",
    m34_step_actor: "durable-runner",
    created_at: "2026-08-28T01:02:00Z",
  }],
  next_cursor: null,
} as const satisfies PaperRuntimeWorkListResponse;

export const paperRuntimeCheckpoints = {
  schema_version: 1,
  items: [{
    schema_version: 1,
    checkpoint_id: runtimeRaw.checkpointId,
    checkpoint_digest: digest("8"),
    runtime_id: runtimeRaw.runtimeId,
    work_id: runtimeRaw.workId,
    execution_order_id: executionRaw.orderId,
    execution_order_digest: executionRaw.orderDigest,
    observed_execution_version: 1,
    attempt_id: executionRaw.attemptId,
    attempt_digest: executionRaw.attemptDigest,
    fill_id: executionRaw.fillId,
    fill_digest: executionRaw.fillDigest,
    settlement_link_id: executionRaw.settlementId,
    settlement_link_evidence_digest: digest("9"),
    account_event_id: "account-event-s224",
    replay_id: raw.replayId,
    event_stream_digest: raw.streamDigest,
    post_cursor_position: 3,
    post_cursor_last_event_id: "market-event-3",
    observed_at: "2026-08-28T01:03:00Z",
  }],
  next_cursor: null,
} as const satisfies PaperRuntimeCheckpointListResponse;

export const paperRuntimeCommand = {
  schema_version: 1,
  replayed: false,
  request_id: runtimeRaw.requestId,
  runtime: paperRuntime,
} as const satisfies PaperRuntimeCommandResponse;
