import type { components } from "@/generated/api-types";

type Schemas = components["schemas"];
type Attempt = Schemas["PaperExecutionAttemptResponse"];
type AttemptList = Schemas["PaperExecutionAttemptListResponse"];
type Fill = Schemas["PaperExecutionFillResponse"];
type FillList = Schemas["PaperExecutionFillListResponse"];
type OrderCommand = Schemas["PaperExecutionOrderCommandResponse"];
type OrderList = Schemas["PaperExecutionOrderListResponse"];
type OrderView = Schemas["PaperExecutionOrderViewResponse"];
type Reconciliation = Schemas["PaperExecutionReconciliationResponse"];
type StepCommand = Schemas["PaperExecutionStepCommandResponse"];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length
    && actual.every((key, index) => key === expected[index]);
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function boundedString(value: unknown, maximumLength = 2048): value is string {
  return string(value) && value.length > 0 && value.length <= maximumLength;
}

function nullableString(value: unknown): value is string | null {
  return value === null || string(value);
}

function boolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function integer(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value);
}

function digest(value: unknown): value is string {
  return string(value) && /^[0-9a-f]{64}$/.test(value);
}

function schema(value: Record<string, unknown>): boolean {
  return value.schema_version === 1;
}

function orderReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, ["schema_version", "execution_order_id", "execution_order_digest"])
    && schema(value)
    && boundedString(value.execution_order_id)
    && digest(value.execution_order_digest);
}

function intentReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, ["schema_version", "intent_id", "intent_digest"])
    && schema(value)
    && boundedString(value.intent_id)
    && digest(value.intent_digest);
}

function riskPolicyReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "policy_id", "reference_price_policy_id",
      "maximum_order_quantity", "maximum_order_notional",
      "configuration_digest", "reference_digest",
    ])
    && schema(value)
    && value.policy_id === "long_only_cash_risk_v1"
    && value.reference_price_policy_id === "latest_trade_price_v1"
    && nullableString(value.maximum_order_quantity)
    && nullableString(value.maximum_order_notional)
    && digest(value.configuration_digest)
    && digest(value.reference_digest);
}

function accountHandoff(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "account_id", "account_head_version",
      "account_head_event_id", "account_head_chain_digest", "lifecycle_status",
      "base_currency", "cash_balance", "available_cash", "instrument_id",
      "current_instrument_quantity", "reference_digest",
    ])
    && schema(value)
    && boundedString(value.account_id)
    && integer(value.account_head_version)
    && boundedString(value.account_head_event_id)
    && digest(value.account_head_chain_digest)
    && value.lifecycle_status === "active"
    && boundedString(value.base_currency)
    && string(value.cash_balance)
    && string(value.available_cash)
    && boundedString(value.instrument_id)
    && string(value.current_instrument_quantity)
    && digest(value.reference_digest);
}

function marketHandoff(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "calendar_id", "calendar_version", "trading_session_id",
      "trading_date", "session_type", "session_open_time", "session_close_time",
      "replay_id", "event_stream_digest", "cursor_position", "last_event_id",
      "current_event_id", "current_event_time", "instrument_id",
      "handoff_replay_status", "reference_digest",
    ])
    && schema(value)
    && boundedString(value.calendar_id)
    && integer(value.calendar_version)
    && boundedString(value.trading_session_id)
    && boundedString(value.trading_date)
    && boundedString(value.session_type)
    && boundedString(value.session_open_time)
    && boundedString(value.session_close_time)
    && boundedString(value.replay_id)
    && digest(value.event_stream_digest)
    && integer(value.cursor_position)
    && boundedString(value.last_event_id)
    && boundedString(value.current_event_id)
    && boundedString(value.current_event_time)
    && boundedString(value.instrument_id)
    && value.handoff_replay_status === "running"
    && digest(value.reference_digest);
}

function riskHandoff(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "order_intent_reference", "risk_decision_id",
      "risk_decision_digest", "risk_snapshot_id", "risk_snapshot_digest",
      "risk_policy_reference", "outcome", "reference_digest",
    ])
    && schema(value)
    && intentReference(value.order_intent_reference)
    && boundedString(value.risk_decision_id)
    && digest(value.risk_decision_digest)
    && boundedString(value.risk_snapshot_id)
    && digest(value.risk_snapshot_digest)
    && riskPolicyReference(value.risk_policy_reference)
    && value.outcome === "allow"
    && digest(value.reference_digest);
}

function policyReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "policy_id", "max_fill_quantity_per_trade_event",
      "slippage_bps", "commission_bps", "fee_bps", "buy_tax_bps",
      "sell_tax_bps", "execution_price_policy_id", "slippage_policy_id",
      "transaction_cost_policy_id", "configuration_digest", "reference_digest",
    ])
    && schema(value)
    && value.policy_id === "paper_execution_v1"
    && nullableString(value.max_fill_quantity_per_trade_event)
    && string(value.slippage_bps)
    && string(value.commission_bps)
    && string(value.fee_bps)
    && string(value.buy_tax_bps)
    && string(value.sell_tax_bps)
    && value.execution_price_policy_id === "consumed_trade_event_price_v1"
    && value.slippage_policy_id === "fixed_bps_slippage_v1"
    && value.transaction_cost_policy_id === "per_fill_bps_costs_v1"
    && digest(value.configuration_digest)
    && digest(value.reference_digest);
}

function order(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "execution_order_id", "execution_order_digest",
      "order_intent_reference", "risk_handoff_reference",
      "account_handoff_reference", "market_handoff_reference",
      "execution_policy_reference", "account_id", "instrument_id", "side",
      "requested_quantity", "origin_command_digest", "origin_actor", "created_at",
    ])
    && schema(value)
    && boundedString(value.execution_order_id)
    && digest(value.execution_order_digest)
    && intentReference(value.order_intent_reference)
    && riskHandoff(value.risk_handoff_reference)
    && accountHandoff(value.account_handoff_reference)
    && marketHandoff(value.market_handoff_reference)
    && policyReference(value.execution_policy_reference)
    && boundedString(value.account_id)
    && boundedString(value.instrument_id)
    && (value.side === "buy" || value.side === "sell")
    && string(value.requested_quantity)
    && digest(value.origin_command_digest)
    && boundedString(value.origin_actor)
    && boundedString(value.created_at);
}

function orderState(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "execution_order_reference", "execution_version",
      "status", "requested_quantity", "cumulative_filled_quantity",
      "remaining_quantity", "terminal",
    ])
    && schema(value)
    && orderReference(value.execution_order_reference)
    && integer(value.execution_version)
    && ["working", "partially_filled", "filled", "rejected", "partially_filled_rejected"].includes(String(value.status))
    && string(value.requested_quantity)
    && string(value.cumulative_filled_quantity)
    && string(value.remaining_quantity)
    && boolean(value.terminal);
}

function replayCursor(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "replay_id", "event_stream_digest", "position",
      "last_event_id", "current_event_time", "status",
    ])
    && schema(value)
    && boundedString(value.replay_id)
    && digest(value.event_stream_digest)
    && integer(value.position)
    && nullableString(value.last_event_id)
    && nullableString(value.current_event_time)
    && ["ready", "running", "paused", "completed"].includes(String(value.status));
}

function eventReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "replay_id", "event_stream_digest", "event_id",
      "event_digest", "event_type", "event_time", "instrument_id",
      "consumed_event_position", "pre_step_cursor_position",
      "post_step_cursor_position", "post_step_last_event_id",
      "post_step_current_event_time", "post_step_replay_status", "reference_digest",
    ])
    && schema(value)
    && boundedString(value.replay_id)
    && digest(value.event_stream_digest)
    && boundedString(value.event_id)
    && digest(value.event_digest)
    && boundedString(value.event_type)
    && boundedString(value.event_time)
    && boundedString(value.instrument_id)
    && integer(value.consumed_event_position)
    && integer(value.pre_step_cursor_position)
    && integer(value.post_step_cursor_position)
    && boundedString(value.post_step_last_event_id)
    && boundedString(value.post_step_current_event_time)
    && ["ready", "running", "paused", "completed"].includes(String(value.post_step_replay_status))
    && digest(value.reference_digest);
}

function priceEvidence(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "execution_price_policy_id", "slippage_policy_id",
      "execution_event_reference", "side", "base_trade_price", "slippage_bps",
      "pre_round_execution_price", "execution_price", "rounding_quantum",
      "rounding_mode", "rounding_applied", "price_evidence_digest",
    ])
    && schema(value)
    && value.execution_price_policy_id === "consumed_trade_event_price_v1"
    && value.slippage_policy_id === "fixed_bps_slippage_v1"
    && eventReference(value.execution_event_reference)
    && (value.side === "buy" || value.side === "sell")
    && string(value.base_trade_price)
    && string(value.slippage_bps)
    && string(value.pre_round_execution_price)
    && string(value.execution_price)
    && string(value.rounding_quantum)
    && boundedString(value.rounding_mode)
    && boolean(value.rounding_applied)
    && digest(value.price_evidence_digest);
}

function costEvidence(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "transaction_cost_policy_id", "execution_price_evidence",
      "fill_quantity", "rounding_quantum", "rounding_mode",
      "gross_notional_pre_round", "gross_notional", "gross_notional_rounding_applied",
      "commission_bps", "commission_pre_round", "commission", "commission_rounding_applied",
      "fee_bps", "fee_pre_round", "fee", "fee_rounding_applied",
      "side_tax_bps", "tax_pre_round", "tax", "tax_rounding_applied",
      "total_charges", "cost_evidence_digest",
    ])
    && schema(value)
    && value.transaction_cost_policy_id === "per_fill_bps_costs_v1"
    && priceEvidence(value.execution_price_evidence)
    && string(value.fill_quantity)
    && string(value.rounding_quantum)
    && boundedString(value.rounding_mode)
    && string(value.gross_notional_pre_round)
    && string(value.gross_notional)
    && boolean(value.gross_notional_rounding_applied)
    && string(value.commission_bps)
    && string(value.commission_pre_round)
    && string(value.commission)
    && boolean(value.commission_rounding_applied)
    && string(value.fee_bps)
    && string(value.fee_pre_round)
    && string(value.fee)
    && boolean(value.fee_rounding_applied)
    && string(value.side_tax_bps)
    && string(value.tax_pre_round)
    && string(value.tax)
    && boolean(value.tax_rounding_applied)
    && string(value.total_charges)
    && digest(value.cost_evidence_digest);
}

function riskRule(value: unknown): boolean {
  return object(value)
    && exactKeys(value, ["rule_id", "observed_value", "limit_value", "passed", "reason_code"])
    && boundedString(value.rule_id)
    && nullableString(value.observed_value)
    && nullableString(value.limit_value)
    && boolean(value.passed)
    && nullableString(value.reason_code);
}

function riskRevalidation(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "risk_revalidation_id", "risk_revalidation_digest",
      "execution_order_reference", "execution_version", "account_id",
      "account_head_version", "account_head_event_id", "account_head_chain_digest",
      "available_cash", "current_instrument_quantity", "requested_quantity",
      "remaining_quantity_before_step", "candidate_fill_quantity",
      "execution_price_evidence", "cost_evidence", "cumulative_filled_gross_notional",
      "projected_notional_pre_round", "projected_order_gross_notional",
      "rounding_quantum", "rounding_mode", "projected_notional_rounding_applied",
      "risk_policy_reference", "rules", "outcome", "reason_codes",
    ])
    && schema(value)
    && boundedString(value.risk_revalidation_id)
    && digest(value.risk_revalidation_digest)
    && orderReference(value.execution_order_reference)
    && integer(value.execution_version)
    && boundedString(value.account_id)
    && integer(value.account_head_version)
    && boundedString(value.account_head_event_id)
    && digest(value.account_head_chain_digest)
    && string(value.available_cash)
    && string(value.current_instrument_quantity)
    && string(value.requested_quantity)
    && string(value.remaining_quantity_before_step)
    && string(value.candidate_fill_quantity)
    && priceEvidence(value.execution_price_evidence)
    && costEvidence(value.cost_evidence)
    && string(value.cumulative_filled_gross_notional)
    && string(value.projected_notional_pre_round)
    && string(value.projected_order_gross_notional)
    && string(value.rounding_quantum)
    && boundedString(value.rounding_mode)
    && boolean(value.projected_notional_rounding_applied)
    && riskPolicyReference(value.risk_policy_reference)
    && Array.isArray(value.rules)
    && value.rules.every(riskRule)
    && (value.outcome === "allow" || value.outcome === "reject")
    && Array.isArray(value.reason_codes)
    && value.reason_codes.every(string);
}

function attemptReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, ["schema_version", "attempt_id", "attempt_digest"])
    && schema(value)
    && boundedString(value.attempt_id)
    && digest(value.attempt_digest);
}

export function isPaperExecutionAttemptResponse(value: unknown): value is Attempt {
  return object(value)
    && exactKeys(value, [
      "schema_version", "attempt_id", "attempt_digest", "execution_order_reference",
      "execution_version_before", "execution_version_after", "attempt_result",
      "no_fill_reason_code", "terminal_reason_code", "pre_step_cursor",
      "post_step_cursor", "consumed_event_reference", "prior_order_state",
      "risk_revalidation", "created_at",
    ])
    && schema(value)
    && boundedString(value.attempt_id)
    && digest(value.attempt_digest)
    && orderReference(value.execution_order_reference)
    && integer(value.execution_version_before)
    && integer(value.execution_version_after)
    && ["no_fill", "fill", "risk_rejected", "boundary_rejected"].includes(String(value.attempt_result))
    && (value.no_fill_reason_code === null || ["instrument_mismatch", "event_type_not_trade", "trade_price_invalid"].includes(String(value.no_fill_reason_code)))
    && (value.terminal_reason_code === null || ["execution_risk_rejected", "replay_exhausted", "session_exhausted"].includes(String(value.terminal_reason_code)))
    && replayCursor(value.pre_step_cursor)
    && replayCursor(value.post_step_cursor)
    && (value.consumed_event_reference === null || eventReference(value.consumed_event_reference))
    && orderState(value.prior_order_state)
    && (value.risk_revalidation === null || riskRevalidation(value.risk_revalidation))
    && boundedString(value.created_at);
}

function fillReference(value: unknown): boolean {
  return object(value)
    && exactKeys(value, ["schema_version", "fill_id", "fill_digest"])
    && schema(value)
    && boundedString(value.fill_id)
    && digest(value.fill_digest);
}

export function isPaperExecutionFillResponse(value: unknown): value is Fill {
  return object(value)
    && exactKeys(value, [
      "schema_version", "fill_id", "fill_digest", "execution_order_reference",
      "attempt_reference", "execution_event_reference", "side", "fill_quantity",
      "execution_price_evidence", "cost_evidence", "created_at",
    ])
    && schema(value)
    && boundedString(value.fill_id)
    && digest(value.fill_digest)
    && orderReference(value.execution_order_reference)
    && attemptReference(value.attempt_reference)
    && eventReference(value.execution_event_reference)
    && (value.side === "buy" || value.side === "sell")
    && string(value.fill_quantity)
    && priceEvidence(value.execution_price_evidence)
    && costEvidence(value.cost_evidence)
    && boundedString(value.created_at);
}

function settlementLink(value: unknown): boolean {
  return object(value)
    && exactKeys(value, [
      "schema_version", "settlement_link_id", "settlement_link_digest",
      "settlement_link_evidence_digest", "execution_order_reference",
      "execution_attempt_reference", "execution_fill_reference", "account_id",
      "account_event_id", "account_event_digest", "account_chain_digest",
      "account_version", "cash_entry_id", "cash_entry_digest",
      "position_entry_id", "position_entry_digest",
    ])
    && schema(value)
    && boundedString(value.settlement_link_id)
    && digest(value.settlement_link_digest)
    && digest(value.settlement_link_evidence_digest)
    && orderReference(value.execution_order_reference)
    && attemptReference(value.execution_attempt_reference)
    && fillReference(value.execution_fill_reference)
    && boundedString(value.account_id)
    && boundedString(value.account_event_id)
    && digest(value.account_event_digest)
    && digest(value.account_chain_digest)
    && integer(value.account_version)
    && boundedString(value.cash_entry_id)
    && digest(value.cash_entry_digest)
    && boundedString(value.position_entry_id)
    && digest(value.position_entry_digest);
}

export function isPaperExecutionOrderViewResponse(value: unknown): value is OrderView {
  return object(value)
    && exactKeys(value, ["order", "state"])
    && order(value.order)
    && orderState(value.state);
}

export function isPaperExecutionOrderListResponse(value: unknown): value is OrderList {
  return object(value)
    && exactKeys(value, ["schema_version", "items", "next_cursor"])
    && schema(value)
    && Array.isArray(value.items)
    && value.items.every(isPaperExecutionOrderViewResponse)
    && (value.next_cursor === null || boundedString(value.next_cursor));
}

export function isPaperExecutionAttemptListResponse(value: unknown): value is AttemptList {
  return object(value)
    && exactKeys(value, ["schema_version", "items", "next_cursor"])
    && schema(value)
    && Array.isArray(value.items)
    && value.items.every(isPaperExecutionAttemptResponse)
    && (value.next_cursor === null || boundedString(value.next_cursor));
}

export function isPaperExecutionFillListResponse(value: unknown): value is FillList {
  return object(value)
    && exactKeys(value, ["schema_version", "items", "next_cursor"])
    && schema(value)
    && Array.isArray(value.items)
    && value.items.every(isPaperExecutionFillResponse)
    && (value.next_cursor === null || boundedString(value.next_cursor));
}

export function isPaperExecutionOrderCommandResponse(value: unknown): value is OrderCommand {
  return object(value)
    && exactKeys(value, ["schema_version", "replayed", "request_id", "result"])
    && schema(value)
    && boolean(value.replayed)
    && boundedString(value.request_id, 128)
    && object(value.result)
    && exactKeys(value.result, ["order", "state"])
    && order(value.result.order)
    && orderState(value.result.state);
}

export function isPaperExecutionStepCommandResponse(value: unknown): value is StepCommand {
  if (!object(value)
    || !exactKeys(value, ["schema_version", "replayed", "request_id", "result"])
    || !schema(value)
    || !boolean(value.replayed)
    || !boundedString(value.request_id, 128)
    || !object(value.result)
    || !exactKeys(value.result, [
      "schema_version", "attempt", "fill", "settlement_link",
      "account_event_id", "order_state",
    ])) return false;
  const result = value.result;
  return schema(result)
    && isPaperExecutionAttemptResponse(result.attempt)
    && (result.fill === null || isPaperExecutionFillResponse(result.fill))
    && (result.settlement_link === null || settlementLink(result.settlement_link))
    && nullableString(result.account_event_id)
    && orderState(result.order_state);
}

export function isPaperExecutionReconciliationResponse(value: unknown): value is Reconciliation {
  return object(value)
    && exactKeys(value, ["schema_version", "order", "state", "attempts", "fills", "settlement_links"])
    && schema(value)
    && order(value.order)
    && orderState(value.state)
    && Array.isArray(value.attempts)
    && value.attempts.every(isPaperExecutionAttemptResponse)
    && Array.isArray(value.fills)
    && value.fills.every(isPaperExecutionFillResponse)
    && Array.isArray(value.settlement_links)
    && value.settlement_links.every(settlementLink);
}
