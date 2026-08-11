import type {
  MarketDataReplayDetailResponse,
  OrderIntentCommandResponse,
  PaperAccountDetailResponse,
  PaperAccountListResponse,
  PreTradeRiskDecisionCommandResponse,
  ReplaySessionListResponse,
  StrategySignalCommandResponse,
  TradingCalendarDetailResponse,
  TradingCalendarListResponse,
} from "@/lib/api-client";

export const raw = {
  signalId: `sig_${"a".repeat(64)}`,
  signalDigest: "b".repeat(64),
  intentId: `oi_${"c".repeat(64)}`,
  intentDigest: "d".repeat(64),
  decisionId: `risk_decision_${"e".repeat(64)}`,
  decisionDigest: "f".repeat(64),
  snapshotId: `risk_input_${"1".repeat(64)}`,
  snapshotDigest: "2".repeat(64),
  noActionId: `no_action_${"3".repeat(64)}`,
  noActionDigest: "4".repeat(64),
  calendarId: "calendar-xnys-2026",
  sessionId: "session-xnys-2026-08-11",
  replayId: "replay-s204",
  streamDigest: "5".repeat(64),
  eventId: "market-event-2",
  eventTime: "2026-08-11T01:31:00Z",
  instrumentId: "AAPL.XNAS",
  accountId: "paper-account-s204",
  accountEventId: "account-event-s204",
  accountChainDigest: "6".repeat(64),
  requestId: "request-s204-raw",
  timestamp: "2026-08-11T02:00:00Z",
} as const;

const marketReference = {
  schema_version: 1,
  calendar_id: raw.calendarId,
  calendar_version: 1,
  trading_session_id: raw.sessionId,
  replay_id: raw.replayId,
  event_stream_digest: raw.streamDigest,
  cursor_position: 2,
  last_event_id: raw.eventId,
  signal_event_id: raw.eventId,
  signal_time: raw.eventTime,
  instrument_id: raw.instrumentId,
  reference_digest: "7".repeat(64),
} as const;

const accountReference = {
  schema_version: 1,
  account_id: raw.accountId,
  base_currency: "USD",
  lifecycle_status: "active",
  account_head_version: 1,
  account_head_event_id: raw.accountEventId,
  account_head_chain_digest: raw.accountChainDigest,
  cash_balance: "1000",
  available_cash: "1000",
  instrument_id: raw.instrumentId,
  current_instrument_quantity: "0",
  reference_digest: "8".repeat(64),
} as const;

export const signalCommand = {
  schema_version: 1,
  replayed: false,
  request_id: raw.requestId,
  signal: {
    schema_version: 1,
    signal_id: raw.signalId,
    signal_digest: raw.signalDigest,
    strategy_runtime_reference: {
      schema_version: 1,
      strategy_name: "moving_average_crossover",
      strategy_version: "v1",
      adapter_version: "v1",
      runtime_sizing_semantics: "target_position_quantity",
      parameters: {
        fast_window: 20,
        slow_window: 50,
        target_position_quantity: "100",
      },
      parameters_digest: "9".repeat(64),
      reference_digest: "a".repeat(64),
    },
    market_reference: marketReference,
    target_semantics: "target_position_quantity",
    target_position_quantity: "100",
    created_at: raw.timestamp,
  },
} as const satisfies StrategySignalCommandResponse;

export const intentCommand = {
  schema_version: 1,
  replayed: false,
  request_id: raw.requestId,
  result_kind: "order_intent",
  result: {
    schema_version: 1,
    intent_id: raw.intentId,
    intent_digest: raw.intentDigest,
    signal_reference: {
      schema_version: 1,
      signal_id: raw.signalId,
      signal_digest: raw.signalDigest,
    },
    market_reference: marketReference,
    account_reference: accountReference,
    target_semantics: "target_position_quantity",
    target_position_quantity: "100",
    current_position_quantity: "0",
    side: "buy",
    requested_quantity: "100",
    intent_policy_version: "target_position_quantity_delta_v1",
    origin_command_digest: "b".repeat(64),
    origin_actor: "founder",
    created_at: raw.timestamp,
  },
} as const satisfies OrderIntentCommandResponse;

export const noActionCommand = {
  schema_version: 1,
  replayed: false,
  request_id: raw.requestId,
  result_kind: "order_intent_no_action",
  result: {
    schema_version: 1,
    no_action_id: raw.noActionId,
    no_action_digest: raw.noActionDigest,
    reason_code: "target_already_satisfied",
    signal_reference: {
      schema_version: 1,
      signal_id: raw.signalId,
      signal_digest: raw.signalDigest,
    },
    market_reference: marketReference,
    account_reference: { ...accountReference, current_instrument_quantity: "100" },
    target_semantics: "target_position_quantity",
    target_position_quantity: "100",
    current_position_quantity: "100",
    intent_policy_version: "target_position_quantity_delta_v1",
    origin_command_digest: "c".repeat(64),
    origin_actor: "founder",
    created_at: raw.timestamp,
  },
} as const satisfies OrderIntentCommandResponse;

const rules = [
  {
    schema_version: 1 as const,
    rule_code: "insufficient_position_quantity" as const,
    applicable: false,
    value_type: "quantity" as const,
    observed_value: "0",
    threshold_value: "100",
    passed: true,
    rule_digest: "d".repeat(64),
  },
  {
    schema_version: 1 as const,
    rule_code: "maximum_order_quantity_exceeded" as const,
    applicable: true,
    value_type: "quantity" as const,
    observed_value: "100",
    threshold_value: "200",
    passed: true,
    rule_digest: "e".repeat(64),
  },
  {
    schema_version: 1 as const,
    rule_code: "maximum_order_notional_exceeded" as const,
    applicable: true,
    value_type: "money" as const,
    observed_value: "500",
    threshold_value: "2000",
    passed: true,
    rule_digest: "f".repeat(64),
  },
  {
    schema_version: 1 as const,
    rule_code: "insufficient_available_cash" as const,
    applicable: true,
    value_type: "money" as const,
    observed_value: "500",
    threshold_value: "1000",
    passed: true,
    rule_digest: "0".repeat(64),
  },
];

export const riskCommand = {
  schema_version: 1,
  replayed: false,
  request_id: raw.requestId,
  decision: {
    schema_version: 1,
    decision_id: raw.decisionId,
    decision_digest: raw.decisionDigest,
    input_snapshot: {
      schema_version: 1,
      snapshot_id: raw.snapshotId,
      snapshot_digest: raw.snapshotDigest,
      intent_reference: {
        schema_version: 1,
        intent_id: raw.intentId,
        intent_digest: raw.intentDigest,
      },
      market_reference: marketReference,
      account_reference: accountReference,
      risk_policy_reference: {
        schema_version: 1,
        policy_id: "long_only_cash_risk_v1",
        reference_price_policy_id: "latest_trade_price_v1",
        maximum_order_quantity: "200",
        maximum_order_notional: "2000",
        configuration_digest: "1".repeat(64),
        reference_digest: "2".repeat(64),
      },
      price_reference: {
        schema_version: 1,
        reference_price_policy_id: "latest_trade_price_v1",
        event_stream_digest: raw.streamDigest,
        replay_id: raw.replayId,
        cursor_position: 2,
        price_event_position: 2,
        price_event_id: raw.eventId,
        price_event_time: raw.eventTime,
        instrument_id: raw.instrumentId,
        price_event_digest: "3".repeat(64),
        reference_price: "5",
        reference_digest: "4".repeat(64),
      },
      side: "buy",
      requested_quantity: "100",
      verified_available_cash: "1000",
      verified_current_instrument_quantity: "0",
      estimated_order_notional: "500",
      rule_evidence: rules,
    },
    outcome: "allow",
    reason_codes: [],
    origin_command_digest: "5".repeat(64),
    origin_actor: "founder",
    created_at: raw.timestamp,
  },
} as const satisfies PreTradeRiskDecisionCommandResponse;

export const rejectedRiskCommand: PreTradeRiskDecisionCommandResponse = {
  ...riskCommand,
  decision: {
    ...riskCommand.decision,
    decision_id: `risk_decision_${"9".repeat(64)}`,
    decision_digest: "8".repeat(64),
    outcome: "reject",
    reason_codes: ["insufficient_available_cash"],
    input_snapshot: {
      ...riskCommand.decision.input_snapshot,
      rule_evidence: rules.map((rule) =>
        rule.rule_code === "insufficient_available_cash"
          ? { ...rule, passed: false }
          : rule,
      ),
    },
  },
};

const accountSummary = {
  record_schema_version: 1,
  account_id: raw.accountId,
  display_name: "Sprint 204 Account",
  base_currency: "USD",
  lifecycle_status: "active",
  head_version: 1,
  head_event_id: raw.accountEventId,
  head_chain_digest: raw.accountChainDigest,
  projection_status: "current",
  created_by: "founder",
  created_timestamp: raw.timestamp,
  updated_timestamp: raw.timestamp,
  closed_timestamp: null,
} as const;

export const paperAccountList = {
  schema_version: 1,
  items: [accountSummary],
  next_cursor: null,
} as const satisfies PaperAccountListResponse;

export const paperAccountDetail = {
  schema_version: 1,
  account: accountSummary,
  projection: {
    schema_version: 1,
    account_identity: {
      schema_version: 1,
      account_id: raw.accountId,
      display_name: "Sprint 204 Account",
      base_currency: "USD",
      created_by: "founder",
      created_timestamp: raw.timestamp,
    },
    lifecycle_status: "active",
    cash_balance: "1000",
    available_cash: "1000",
    positions: [],
    approved_portfolio_reviews: [],
    source_account_version: 1,
    source_event_id: raw.accountEventId,
    source_chain_digest: raw.accountChainDigest,
    projection_digest: "7".repeat(64),
  },
} as const satisfies PaperAccountDetailResponse;

export const calendarList = [
  {
    schema_version: 1,
    id: raw.calendarId,
    market: "XNYS",
    timezone: "America/New_York",
    calendar_version: 1,
    created_at: raw.timestamp,
  },
] as const satisfies TradingCalendarListResponse;

export const calendarDetail = {
  calendar: calendarList[0],
  sessions: [
    {
      schema_version: 1,
      id: raw.sessionId,
      calendar_id: raw.calendarId,
      trading_date: "2026-08-11",
      open_time: "2026-08-11T01:30:00Z",
      close_time: "2026-08-11T08:00:00Z",
      session_type: "regular",
    },
  ],
} as const satisfies TradingCalendarDetailResponse;

const replaySession = {
  schema_version: 1,
  replay_id: raw.replayId,
  status: "paused",
  start_time: "2026-08-11T01:30:00Z",
  current_time: raw.eventTime,
  cursor: {
    schema_version: 1,
    replay_id: raw.replayId,
    event_stream_digest: raw.streamDigest,
    position: 2,
    last_event_id: raw.eventId,
    current_event_time: raw.eventTime,
    status: "paused",
  },
} as const;

export const replayList = [replaySession] as const satisfies ReplaySessionListResponse;

export const replayDetail = {
  record_schema_version: 1,
  session: replaySession,
  event_count: 2,
  events: [
    {
      schema_version: 1,
      event_id: "market-event-1",
      instrument_id: raw.instrumentId,
      event_time: "2026-08-11T01:30:00Z",
      event_type: "trade",
      payload: { price: "4" },
      source: "demo",
    },
    {
      schema_version: 1,
      event_id: raw.eventId,
      instrument_id: raw.instrumentId,
      event_time: raw.eventTime,
      event_type: "trade",
      payload: { price: "5" },
      source: "demo",
    },
  ],
} as const satisfies MarketDataReplayDetailResponse;
