import type { components } from "@/generated/api-types";

type Schemas = components["schemas"];
type StrategySignal = Schemas["StrategySignalResponse"];
type StrategySignalCommand = Schemas["StrategySignalCommandResponse"];
type StrategySignalList = Schemas["StrategySignalListResponse"];
type OrderIntent = Schemas["OrderIntentResponse"];
type OrderIntentNoAction = Schemas["OrderIntentNoActionResponse"];
type OrderIntentCommand =
  | Schemas["OrderIntentCommandResponse"]
  | Schemas["OrderIntentNoActionCommandResponse"];
type OrderIntentList = Schemas["OrderIntentListResponse"];
type PreTradeRiskDecision = Schemas["PreTradeRiskDecisionResponse"];
type PreTradeRiskDecisionCommand =
  Schemas["PreTradeRiskDecisionCommandResponse"];
type PreTradeRiskDecisionList = Schemas["PreTradeRiskDecisionListResponse"];
type RiskRuleCode =
  Schemas["PreTradeRiskRuleEvidenceResponse"]["rule_code"];

const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const SIGNAL_ID_PATTERN = /^sig_[0-9a-f]{64}$/;
const INTENT_ID_PATTERN = /^oi_[0-9a-f]{64}$/;
const NO_ACTION_ID_PATTERN = /^no_action_[0-9a-f]{64}$/;
const DECISION_ID_PATTERN = /^risk_decision_[0-9a-f]{64}$/;
const SNAPSHOT_ID_PATTERN = /^risk_input_[0-9a-f]{64}$/;
const CANONICAL_DECIMAL_PATTERN = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?$/;
const UTC_TIMESTAMP_PATTERN = /(?:Z|\+00:00)$/;

export const preTradeRiskRuleOrder = [
  "insufficient_position_quantity",
  "maximum_order_quantity_exceeded",
  "maximum_order_notional_exceeded",
  "insufficient_available_cash",
] as const satisfies readonly RiskRuleCode[];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return (
    actual.length === expected.length &&
    actual.every((key, index) => key === expected[index])
  );
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function boundedString(value: unknown, maximumLength = 512): value is string {
  return (
    string(value) &&
    value.length > 0 &&
    value.length <= maximumLength &&
    value === value.trim()
  );
}

function nullableBoundedString(
  value: unknown,
  maximumLength: number,
): value is string | null {
  return value === null || boundedString(value, maximumLength);
}

function positiveInteger(value: unknown): value is number {
  return Number.isInteger(value) && (value as number) > 0;
}

function boolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function sha256(value: unknown): value is string {
  return string(value) && SHA256_PATTERN.test(value);
}

function canonicalDecimal(
  value: unknown,
  maximumFractionalDigits: number,
): value is string {
  if (
    !string(value) ||
    !CANONICAL_DECIMAL_PATTERN.test(value) ||
    value === "-0"
  ) {
    return false;
  }
  const unsigned = value.startsWith("-") ? value.slice(1) : value;
  const [integerPart, fractionalPart = ""] = unsigned.split(".");
  return integerPart.length <= 18 && fractionalPart.length <= maximumFractionalDigits;
}

function quantity(value: unknown): value is string {
  return canonicalDecimal(value, 12);
}

function money(value: unknown): value is string {
  return canonicalDecimal(value, 8);
}

function nonNegativeQuantity(value: unknown): value is string {
  return quantity(value) && !value.startsWith("-");
}

function positiveQuantity(value: unknown): value is string {
  return nonNegativeQuantity(value) && value !== "0";
}

function nonNegativeMoney(value: unknown): value is string {
  return money(value) && !value.startsWith("-");
}

function positiveMoney(value: unknown): value is string {
  return nonNegativeMoney(value) && value !== "0";
}

function timestamp(value: unknown): value is string {
  return (
    string(value) &&
    UTC_TIMESTAMP_PATTERN.test(value) &&
    Number.isFinite(Date.parse(value))
  );
}

function nullableTimestamp(value: unknown): value is string | null {
  return value === null || timestamp(value);
}

function signalReference(value: unknown): boolean {
  return (
    object(value) &&
    exactKeys(value, ["schema_version", "signal_id", "signal_digest"]) &&
    value.schema_version === 1 &&
    string(value.signal_id) &&
    SIGNAL_ID_PATTERN.test(value.signal_id) &&
    sha256(value.signal_digest)
  );
}

function strategyRuntimeReference(value: unknown): boolean {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "strategy_name",
      "strategy_version",
      "adapter_version",
      "runtime_sizing_semantics",
      "parameters",
      "parameters_digest",
      "reference_digest",
    ]) ||
    value.schema_version !== 1 ||
    value.strategy_name !== "moving_average_crossover" ||
    value.strategy_version !== "v1" ||
    value.adapter_version !== "v1" ||
    value.runtime_sizing_semantics !== "target_position_quantity" ||
    !object(value.parameters) ||
    !exactKeys(value.parameters, [
      "fast_window",
      "slow_window",
      "target_position_quantity",
    ]) ||
    !positiveInteger(value.parameters.fast_window) ||
    !positiveInteger(value.parameters.slow_window) ||
    value.parameters.fast_window >= value.parameters.slow_window ||
    !positiveQuantity(value.parameters.target_position_quantity) ||
    !sha256(value.parameters_digest) ||
    !sha256(value.reference_digest)
  ) {
    return false;
  }
  return true;
}

function signalMarketReference(value: unknown): boolean {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "calendar_id",
      "calendar_version",
      "trading_session_id",
      "replay_id",
      "event_stream_digest",
      "cursor_position",
      "last_event_id",
      "signal_event_id",
      "signal_time",
      "instrument_id",
      "reference_digest",
    ]) ||
    value.schema_version !== 1 ||
    !boundedString(value.calendar_id) ||
    !positiveInteger(value.calendar_version) ||
    !boundedString(value.trading_session_id) ||
    !boundedString(value.replay_id) ||
    !sha256(value.event_stream_digest) ||
    !positiveInteger(value.cursor_position) ||
    !boundedString(value.last_event_id) ||
    !boundedString(value.signal_event_id) ||
    !timestamp(value.signal_time) ||
    !boundedString(value.instrument_id) ||
    !sha256(value.reference_digest)
  ) {
    return false;
  }
  return value.last_event_id === value.signal_event_id;
}

export function isStrategySignalResponse(
  value: unknown,
): value is StrategySignal {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "signal_id",
      "signal_digest",
      "strategy_runtime_reference",
      "market_reference",
      "target_semantics",
      "target_position_quantity",
      "created_at",
    ]) ||
    value.schema_version !== 1 ||
    !string(value.signal_id) ||
    !SIGNAL_ID_PATTERN.test(value.signal_id) ||
    !sha256(value.signal_digest) ||
    !strategyRuntimeReference(value.strategy_runtime_reference) ||
    !signalMarketReference(value.market_reference) ||
    value.target_semantics !== "target_position_quantity" ||
    !nonNegativeQuantity(value.target_position_quantity) ||
    !timestamp(value.created_at)
  ) {
    return false;
  }
  if (
    !object(value.strategy_runtime_reference) ||
    !object(value.strategy_runtime_reference.parameters)
  ) {
    return false;
  }
  const configuredTarget =
    value.strategy_runtime_reference.parameters.target_position_quantity;
  return (
    value.target_position_quantity === "0" ||
    value.target_position_quantity === configuredTarget
  );
}

export function isStrategySignalCommandResponse(
  value: unknown,
): value is StrategySignalCommand {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "replayed",
      "request_id",
      "signal",
    ]) &&
    value.schema_version === 1 &&
    boolean(value.replayed) &&
    boundedString(value.request_id, 128) &&
    isStrategySignalResponse(value.signal)
  );
}

export function isStrategySignalListResponse(
  value: unknown,
): value is StrategySignalList {
  return (
    object(value) &&
    exactKeys(value, ["schema_version", "items", "next_cursor"]) &&
    value.schema_version === 1 &&
    Array.isArray(value.items) &&
    value.items.every(isStrategySignalResponse) &&
    nullableBoundedString(value.next_cursor, 2048)
  );
}

function accountReference(value: unknown): boolean {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "account_id",
      "base_currency",
      "lifecycle_status",
      "account_head_version",
      "account_head_event_id",
      "account_head_chain_digest",
      "cash_balance",
      "available_cash",
      "instrument_id",
      "current_instrument_quantity",
      "reference_digest",
    ]) ||
    value.schema_version !== 1 ||
    !boundedString(value.account_id) ||
    !string(value.base_currency) ||
    !/^[A-Z]{3}$/.test(value.base_currency) ||
    value.lifecycle_status !== "active" ||
    !positiveInteger(value.account_head_version) ||
    !boundedString(value.account_head_event_id) ||
    !sha256(value.account_head_chain_digest) ||
    !nonNegativeMoney(value.cash_balance) ||
    !nonNegativeMoney(value.available_cash) ||
    !boundedString(value.instrument_id) ||
    !nonNegativeQuantity(value.current_instrument_quantity) ||
    !sha256(value.reference_digest)
  ) {
    return false;
  }
  return value.available_cash === value.cash_balance;
}

function orderIntentBase(value: Record<string, unknown>): boolean {
  return (
    value.schema_version === 1 &&
    signalReference(value.signal_reference) &&
    signalMarketReference(value.market_reference) &&
    accountReference(value.account_reference) &&
    value.target_semantics === "target_position_quantity" &&
    nonNegativeQuantity(value.target_position_quantity) &&
    nonNegativeQuantity(value.current_position_quantity) &&
    value.intent_policy_version === "target_position_quantity_delta_v1" &&
    sha256(value.origin_command_digest) &&
    boundedString(value.origin_actor) &&
    timestamp(value.created_at) &&
    object(value.account_reference) &&
    object(value.market_reference) &&
    value.current_position_quantity ===
      value.account_reference.current_instrument_quantity &&
    value.account_reference.instrument_id === value.market_reference.instrument_id
  );
}

export function isOrderIntentResponse(value: unknown): value is OrderIntent {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "intent_id",
      "intent_digest",
      "signal_reference",
      "market_reference",
      "account_reference",
      "target_semantics",
      "target_position_quantity",
      "current_position_quantity",
      "side",
      "requested_quantity",
      "intent_policy_version",
      "origin_command_digest",
      "origin_actor",
      "created_at",
    ]) &&
    orderIntentBase(value) &&
    string(value.intent_id) &&
    INTENT_ID_PATTERN.test(value.intent_id) &&
    sha256(value.intent_digest) &&
    (value.side === "buy" || value.side === "sell") &&
    positiveQuantity(value.requested_quantity)
  );
}

export function isOrderIntentNoActionResponse(
  value: unknown,
): value is OrderIntentNoAction {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "no_action_id",
      "no_action_digest",
      "reason_code",
      "signal_reference",
      "market_reference",
      "account_reference",
      "target_semantics",
      "target_position_quantity",
      "current_position_quantity",
      "intent_policy_version",
      "origin_command_digest",
      "origin_actor",
      "created_at",
    ]) &&
    orderIntentBase(value) &&
    string(value.no_action_id) &&
    NO_ACTION_ID_PATTERN.test(value.no_action_id) &&
    sha256(value.no_action_digest) &&
    value.reason_code === "target_already_satisfied" &&
    value.target_position_quantity === value.current_position_quantity
  );
}

export function isOrderIntentCommandResponse(
  value: unknown,
): value is OrderIntentCommand {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "replayed",
      "request_id",
      "result_kind",
      "result",
    ]) ||
    value.schema_version !== 1 ||
    !boolean(value.replayed) ||
    !boundedString(value.request_id, 128)
  ) {
    return false;
  }
  return value.result_kind === "order_intent"
    ? isOrderIntentResponse(value.result)
    : value.result_kind === "order_intent_no_action" &&
        isOrderIntentNoActionResponse(value.result);
}

export function isOrderIntentListResponse(
  value: unknown,
): value is OrderIntentList {
  return (
    object(value) &&
    exactKeys(value, ["schema_version", "items", "next_cursor"]) &&
    value.schema_version === 1 &&
    Array.isArray(value.items) &&
    value.items.every(isOrderIntentResponse) &&
    nullableBoundedString(value.next_cursor, 2048)
  );
}

function intentReference(value: unknown): boolean {
  return (
    object(value) &&
    exactKeys(value, ["schema_version", "intent_id", "intent_digest"]) &&
    value.schema_version === 1 &&
    string(value.intent_id) &&
    INTENT_ID_PATTERN.test(value.intent_id) &&
    sha256(value.intent_digest)
  );
}

function riskPolicyReference(value: unknown): boolean {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "policy_id",
      "reference_price_policy_id",
      "maximum_order_quantity",
      "maximum_order_notional",
      "configuration_digest",
      "reference_digest",
    ]) &&
    value.schema_version === 1 &&
    value.policy_id === "long_only_cash_risk_v1" &&
    value.reference_price_policy_id === "latest_trade_price_v1" &&
    (value.maximum_order_quantity === null ||
      positiveQuantity(value.maximum_order_quantity)) &&
    (value.maximum_order_notional === null ||
      positiveMoney(value.maximum_order_notional)) &&
    sha256(value.configuration_digest) &&
    sha256(value.reference_digest)
  );
}

function priceReference(value: unknown): boolean {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "reference_price_policy_id",
      "event_stream_digest",
      "replay_id",
      "cursor_position",
      "price_event_position",
      "price_event_id",
      "price_event_time",
      "instrument_id",
      "price_event_digest",
      "reference_price",
      "reference_digest",
    ]) &&
    value.schema_version === 1 &&
    value.reference_price_policy_id === "latest_trade_price_v1" &&
    sha256(value.event_stream_digest) &&
    boundedString(value.replay_id) &&
    positiveInteger(value.cursor_position) &&
    positiveInteger(value.price_event_position) &&
    boundedString(value.price_event_id) &&
    timestamp(value.price_event_time) &&
    boundedString(value.instrument_id) &&
    sha256(value.price_event_digest) &&
    positiveMoney(value.reference_price) &&
    value.price_event_position <= value.cursor_position &&
    sha256(value.reference_digest)
  );
}

function riskRule(value: unknown, expectedCode: RiskRuleCode): boolean {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "rule_code",
      "applicable",
      "value_type",
      "observed_value",
      "threshold_value",
      "passed",
      "rule_digest",
    ]) ||
    value.schema_version !== 1 ||
    value.rule_code !== expectedCode ||
    !boolean(value.applicable) ||
    !boolean(value.passed) ||
    !sha256(value.rule_digest)
  ) {
    return false;
  }
  const expectedType =
    expectedCode === "maximum_order_notional_exceeded" ||
    expectedCode === "insufficient_available_cash"
      ? "money"
      : "quantity";
  if (value.value_type !== expectedType) {
    return false;
  }
  if (!value.applicable) {
    return (
      value.passed === true &&
      value.observed_value === null &&
      value.threshold_value === null
    );
  }
  const observedValidator =
    expectedCode === "insufficient_position_quantity"
      ? nonNegativeQuantity
      : expectedCode === "insufficient_available_cash"
        ? nonNegativeMoney
        : expectedType === "money"
          ? positiveMoney
          : positiveQuantity;
  const thresholdValidator = expectedType === "money"
    ? positiveMoney
    : positiveQuantity;
  return (
    observedValidator(value.observed_value) &&
    thresholdValidator(value.threshold_value)
  );
}

function riskInputSnapshot(value: unknown): boolean {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "snapshot_id",
      "snapshot_digest",
      "intent_reference",
      "market_reference",
      "account_reference",
      "risk_policy_reference",
      "price_reference",
      "side",
      "requested_quantity",
      "verified_available_cash",
      "verified_current_instrument_quantity",
      "estimated_order_notional",
      "rule_evidence",
    ]) ||
    value.schema_version !== 1 ||
    !string(value.snapshot_id) ||
    !SNAPSHOT_ID_PATTERN.test(value.snapshot_id) ||
    !sha256(value.snapshot_digest) ||
    !intentReference(value.intent_reference) ||
    !signalMarketReference(value.market_reference) ||
    !accountReference(value.account_reference) ||
    !riskPolicyReference(value.risk_policy_reference) ||
    !priceReference(value.price_reference) ||
    (value.side !== "buy" && value.side !== "sell") ||
    !positiveQuantity(value.requested_quantity) ||
    !nonNegativeMoney(value.verified_available_cash) ||
    !nonNegativeQuantity(value.verified_current_instrument_quantity) ||
    !positiveMoney(value.estimated_order_notional) ||
    !Array.isArray(value.rule_evidence) ||
    value.rule_evidence.length !== preTradeRiskRuleOrder.length ||
    !value.rule_evidence.every((rule, index) =>
      riskRule(rule, preTradeRiskRuleOrder[index]),
    )
  ) {
    return false;
  }
  if (
    !object(value.account_reference) ||
    !object(value.market_reference) ||
    !object(value.price_reference) ||
    !object(value.risk_policy_reference)
  ) {
    return false;
  }
  return (
    value.verified_available_cash === value.account_reference.available_cash &&
    value.verified_current_instrument_quantity ===
      value.account_reference.current_instrument_quantity &&
    value.account_reference.instrument_id === value.market_reference.instrument_id &&
    value.price_reference.replay_id === value.market_reference.replay_id &&
    value.price_reference.event_stream_digest ===
      value.market_reference.event_stream_digest &&
    value.price_reference.cursor_position === value.market_reference.cursor_position &&
    value.price_reference.instrument_id === value.market_reference.instrument_id &&
    value.price_reference.reference_price_policy_id ===
      value.risk_policy_reference.reference_price_policy_id
  );
}

export function isPreTradeRiskDecisionResponse(
  value: unknown,
): value is PreTradeRiskDecision {
  if (
    !object(value) ||
    !exactKeys(value, [
      "schema_version",
      "decision_id",
      "decision_digest",
      "input_snapshot",
      "outcome",
      "reason_codes",
      "origin_command_digest",
      "origin_actor",
      "created_at",
    ]) ||
    value.schema_version !== 1 ||
    !string(value.decision_id) ||
    !DECISION_ID_PATTERN.test(value.decision_id) ||
    !sha256(value.decision_digest) ||
    !riskInputSnapshot(value.input_snapshot) ||
    (value.outcome !== "allow" && value.outcome !== "reject") ||
    !Array.isArray(value.reason_codes) ||
    !value.reason_codes.every((code) => preTradeRiskRuleOrder.includes(code)) ||
    !sha256(value.origin_command_digest) ||
    !boundedString(value.origin_actor) ||
    !timestamp(value.created_at) ||
    !object(value.input_snapshot) ||
    !Array.isArray(value.input_snapshot.rule_evidence)
  ) {
    return false;
  }
  const failedReasons = value.input_snapshot.rule_evidence
    .filter(
      (rule) => object(rule) && rule.applicable === true && rule.passed === false,
    )
    .map((rule) => (rule as Record<string, unknown>).rule_code);
  return (
    (value.outcome === "allow"
      ? value.reason_codes.length === 0
      : value.reason_codes.length > 0) &&
    value.reason_codes.length === failedReasons.length &&
    value.reason_codes.every((reason, index) => reason === failedReasons[index])
  );
}

export function isPreTradeRiskDecisionCommandResponse(
  value: unknown,
): value is PreTradeRiskDecisionCommand {
  return (
    object(value) &&
    exactKeys(value, [
      "schema_version",
      "replayed",
      "request_id",
      "decision",
    ]) &&
    value.schema_version === 1 &&
    boolean(value.replayed) &&
    boundedString(value.request_id, 128) &&
    isPreTradeRiskDecisionResponse(value.decision)
  );
}

export function isPreTradeRiskDecisionListResponse(
  value: unknown,
): value is PreTradeRiskDecisionList {
  return (
    object(value) &&
    exactKeys(value, ["schema_version", "items", "next_cursor"]) &&
    value.schema_version === 1 &&
    Array.isArray(value.items) &&
    value.items.every(isPreTradeRiskDecisionResponse) &&
    nullableBoundedString(value.next_cursor, 2048)
  );
}

export function isOptionalSignalEventTime(
  value: unknown,
): value is string | null {
  return nullableTimestamp(value);
}
