import { describe, expect, it, vi } from "vitest";

import {
  createOrderIntent,
  createPreTradeRiskDecision,
  evaluateStrategySignal,
  fetchOrderIntentDetail,
  fetchOrderIntents,
  fetchPreTradeRiskDecisionDetail,
  fetchPreTradeRiskDecisions,
  fetchStrategySignalDetail,
  fetchStrategySignals,
  type OrderIntentCreateRequest,
  type PreTradeRiskDecisionCreateRequest,
  type StrategySignalEvaluateRequest,
} from "@/lib/api-client";
import {
  intentCommand,
  noActionCommand,
  raw,
  rejectedRiskCommand,
  riskCommand,
  signalCommand,
} from "@/test/strategy-order-fixtures";

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "X-Request-ID": raw.requestId,
    },
  });
}

const signalRequest: StrategySignalEvaluateRequest = {
  runtime: {
    strategy_name: "moving_average_crossover",
    strategy_version: "v1",
    adapter_version: "v1",
    runtime_sizing_semantics: "target_position_quantity",
    fast_window: 20,
    slow_window: 50,
    target_position_quantity: "100",
  },
  market: {
    calendar_id: raw.calendarId,
    expected_calendar_version: 1,
    trading_session_id: raw.sessionId,
    replay_id: raw.replayId,
    expected_event_stream_digest: raw.streamDigest,
    expected_cursor_position: 2,
    expected_signal_event_id: raw.eventId,
    expected_signal_time_utc: raw.eventTime,
    instrument_id: raw.instrumentId,
  },
  actor: "founder",
};

const intentRequest: OrderIntentCreateRequest = {
  signal_id: raw.signalId,
  account: {
    account_id: raw.accountId,
    expected_account_head_version: 1,
    expected_account_head_event_id: raw.accountEventId,
    expected_account_head_chain_digest: raw.accountChainDigest,
  },
  intent_policy_version: "target_position_quantity_delta_v1",
  actor: "founder",
};

const riskRequest: PreTradeRiskDecisionCreateRequest = {
  intent_id: raw.intentId,
  policy: {
    policy_id: "long_only_cash_risk_v1",
    reference_price_policy_id: "latest_trade_price_v1",
    maximum_order_quantity: "200",
    maximum_order_notional: "2000",
  },
  account: {
    expected_account_head_version: 1,
    expected_account_head_event_id: raw.accountEventId,
    expected_account_head_chain_digest: raw.accountChainDigest,
  },
  market: {
    expected_calendar_id: raw.calendarId,
    expected_calendar_version: 1,
    expected_trading_session_id: raw.sessionId,
    expected_replay_id: raw.replayId,
    expected_event_stream_digest: raw.streamDigest,
    expected_cursor_position: 2,
    expected_current_event_id: raw.eventId,
    expected_current_event_time_utc: raw.eventTime,
    expected_instrument_id: raw.instrumentId,
  },
  actor: "founder",
};

describe("generated-contract Strategy-to-Risk API client", () => {
  it("sends the three explicit commands with exact bodies and isolated idempotency headers", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(response(signalCommand, 201))
      .mockResolvedValueOnce(response(intentCommand, 201))
      .mockResolvedValueOnce(response(riskCommand, 201));

    await evaluateStrategySignal(signalRequest, "signal-key", fetchMock);
    await createOrderIntent(intentRequest, "intent-key", fetchMock);
    await createPreTradeRiskDecision(riskRequest, "risk-key", fetchMock);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/backend/api/v1/strategy-signals/evaluate",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": "signal-key" }),
        body: JSON.stringify(signalRequest),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/backend/api/v1/order-intents",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": "intent-key" }),
        body: JSON.stringify(intentRequest),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/backend/api/v1/pre-trade-risk-decisions",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": "risk-key" }),
        body: JSON.stringify(riskRequest),
      }),
    );
    expect(riskRequest.account).toEqual({
      expected_account_head_version: 1,
      expected_account_head_event_id: raw.accountEventId,
      expected_account_head_chain_digest: raw.accountChainDigest,
    });
    expect(riskRequest.account).not.toHaveProperty("account_id");
    expect(riskRequest).not.toHaveProperty("price");
    expect(riskRequest).not.toHaveProperty("outcome");
    expect(riskRequest).not.toHaveProperty("reason_codes");
  });

  it("provides all six bounded list/detail inspection operations", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(response({ schema_version: 1, items: [signalCommand.signal], next_cursor: null }))
      .mockResolvedValueOnce(response(signalCommand.signal))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [intentCommand.result], next_cursor: null }))
      .mockResolvedValueOnce(response(intentCommand.result))
      .mockResolvedValueOnce(response({ schema_version: 1, items: [riskCommand.decision], next_cursor: null }))
      .mockResolvedValueOnce(response(riskCommand.decision));

    await fetchStrategySignals(
      { strategy_name: "moving_average_crossover", instrument_id: raw.instrumentId, limit: 25 },
      fetchMock,
    );
    await fetchStrategySignalDetail(raw.signalId, fetchMock);
    await fetchOrderIntents(
      { signal_id: raw.signalId, account_id: raw.accountId, side: "buy", limit: 25 },
      fetchMock,
    );
    await fetchOrderIntentDetail(raw.intentId, fetchMock);
    await fetchPreTradeRiskDecisions(
      { intent_id: raw.intentId, account_id: raw.accountId, outcome: "allow", limit: 25 },
      fetchMock,
    );
    await fetchPreTradeRiskDecisionDetail(raw.decisionId, fetchMock);

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `/api/backend/api/v1/strategy-signals?strategy_name=moving_average_crossover&instrument_id=${encodeURIComponent(raw.instrumentId)}&limit=25`,
      `/api/backend/api/v1/strategy-signals/${raw.signalId}`,
      `/api/backend/api/v1/order-intents?signal_id=${raw.signalId}&account_id=${raw.accountId}&side=buy&limit=25`,
      `/api/backend/api/v1/order-intents/${raw.intentId}`,
      `/api/backend/api/v1/pre-trade-risk-decisions?intent_id=${raw.intentId}&account_id=${raw.accountId}&outcome=allow&limit=25`,
      `/api/backend/api/v1/pre-trade-risk-decisions/${raw.decisionId}`,
    ]);
  });

  it("accepts complete no-action and reject evidence as valid product results", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(response(noActionCommand, 201))
      .mockResolvedValueOnce(response(rejectedRiskCommand, 201));
    await expect(createOrderIntent(intentRequest, "intent-key", fetchMock)).resolves.toMatchObject({
      data: { result_kind: "order_intent_no_action" },
    });
    await expect(
      createPreTradeRiskDecision(riskRequest, "risk-key", fetchMock),
    ).resolves.toMatchObject({
      data: { decision: { outcome: "reject" } },
    });
  });

  it.each([
    [
      "missing Signal market anchor",
      () => ({
        ...signalCommand,
        signal: {
          ...signalCommand.signal,
          market_reference: {
            ...signalCommand.signal.market_reference,
            reference_digest: undefined,
          },
        },
      }),
      (body: unknown, fetchMock: typeof fetch) =>
        evaluateStrategySignal(signalRequest, "signal-key", fetchMock),
    ],
    [
      "incompatible Intent discriminant",
      () => ({ ...intentCommand, result_kind: "order_intent_no_action" }),
      (body: unknown, fetchMock: typeof fetch) =>
        createOrderIntent(intentRequest, "intent-key", fetchMock),
    ],
    [
      "incomplete ordered risk evidence",
      () => ({
        ...riskCommand,
        decision: {
          ...riskCommand.decision,
          input_snapshot: {
            ...riskCommand.decision.input_snapshot,
            rule_evidence: riskCommand.decision.input_snapshot.rule_evidence.slice(0, 3),
          },
        },
      }),
      (body: unknown, fetchMock: typeof fetch) =>
        createPreTradeRiskDecision(riskRequest, "risk-key", fetchMock),
    ],
    [
      "inconsistent allow reasons",
      () => ({
        ...riskCommand,
        decision: {
          ...riskCommand.decision,
          reason_codes: ["insufficient_available_cash"],
        },
      }),
      (body: unknown, fetchMock: typeof fetch) =>
        createPreTradeRiskDecision(riskRequest, "risk-key", fetchMock),
    ],
  ])("fails closed for %s", async (_name, createBody, invoke) => {
    const body = createBody();
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response(body, 201));
    await expect(invoke(body, fetchMock)).rejects.toMatchObject({
      code: "api_response_invalid",
      requestId: raw.requestId,
    });
  });

  it("rejects blank or overlong idempotency values before transport", async () => {
    const fetchMock = vi.fn<typeof fetch>();
    expect(() =>
      evaluateStrategySignal(signalRequest, " ", fetchMock),
    ).toThrow(TypeError);
    expect(() =>
      evaluateStrategySignal(signalRequest, "x".repeat(129), fetchMock),
    ).toThrow(TypeError);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
