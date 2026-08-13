// @vitest-environment node

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
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
  type PreTradeRiskDecisionCommandResponse,
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

function source(path: string) {
  return readFileSync(resolve(process.cwd(), path), "utf8");
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

type RiskCommandMutation = (
  body: PreTradeRiskDecisionCommandResponse,
) => void;

function malformedRiskCommand(
  mutate: RiskCommandMutation,
): PreTradeRiskDecisionCommandResponse {
  const body: PreTradeRiskDecisionCommandResponse = structuredClone(riskCommand);
  mutate(body);
  return body;
}

function riskRule(
  body: PreTradeRiskDecisionCommandResponse,
  index: number,
) {
  const rule = body.decision.input_snapshot.rule_evidence[index];
  if (rule === undefined) {
    throw new Error(`Missing risk rule fixture at index ${index}`);
  }
  return rule;
}

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

  it("accepts the server's valid zero Signal output without deriving it in the browser", async () => {
    const flatSignal = {
      ...signalCommand,
      signal: {
        ...signalCommand.signal,
        target_position_quantity: "0",
      },
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response(flatSignal, 201));

    await expect(
      evaluateStrategySignal(signalRequest, "signal-key", fetchMock),
    ).resolves.toMatchObject({
      data: { signal: { target_position_quantity: "0" } },
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

  it.each<[string, RiskCommandMutation]>([
    ["signed zero", (body) => {
      body.decision.input_snapshot.requested_quantity = "-0";
    }],
    ["negative account cash", (body) => {
      body.decision.input_snapshot.account_reference.cash_balance = "-1";
      body.decision.input_snapshot.account_reference.available_cash = "-1";
      body.decision.input_snapshot.verified_available_cash = "-1";
    }],
    ["negative account current quantity", (body) => {
      body.decision.input_snapshot.account_reference.current_instrument_quantity = "-1";
      body.decision.input_snapshot.verified_current_instrument_quantity = "-1";
    }],
    ["negative verified current quantity", (body) => {
      body.decision.input_snapshot.verified_current_instrument_quantity = "-1";
    }],
    ["available cash different from cash balance", (body) => {
      body.decision.input_snapshot.account_reference.available_cash = "999";
      body.decision.input_snapshot.verified_available_cash = "999";
    }],
    ["zero maximum order quantity", (body) => {
      body.decision.input_snapshot.risk_policy_reference.maximum_order_quantity = "0";
    }],
    ["negative maximum order notional", (body) => {
      body.decision.input_snapshot.risk_policy_reference.maximum_order_notional = "-1";
    }],
    ["zero reference price", (body) => {
      body.decision.input_snapshot.price_reference.reference_price = "0";
    }],
    ["negative reference price", (body) => {
      body.decision.input_snapshot.price_reference.reference_price = "-1";
    }],
    ["price event outside consumed prefix", (body) => {
      body.decision.input_snapshot.price_reference.price_event_position = 3;
    }],
    ["account instrument different from market", (body) => {
      body.decision.input_snapshot.account_reference.instrument_id = "OTHER";
    }],
    ["price instrument different from market", (body) => {
      body.decision.input_snapshot.price_reference.instrument_id = "OTHER";
    }],
    ["non-applicable failed rule", (body) => {
      riskRule(body, 0).passed = false;
    }],
    ["non-applicable observed value", (body) => {
      riskRule(body, 0).observed_value = "0";
    }],
    ["non-applicable threshold value", (body) => {
      riskRule(body, 0).threshold_value = "100";
    }],
    ["applicable rule missing observed value", (body) => {
      riskRule(body, 1).observed_value = null;
    }],
    ["applicable rule missing threshold value", (body) => {
      riskRule(body, 1).threshold_value = null;
    }],
    ["applicable maximum rule has zero observed quantity", (body) => {
      riskRule(body, 1).observed_value = "0";
    }],
    ["applicable cash rule has negative observed money", (body) => {
      riskRule(body, 3).observed_value = "-1";
    }],
  ])(
    "rejects domain-invalid Risk success: %s without exposing downstream authority",
    async (_name, mutate) => {
      const body = malformedRiskCommand(mutate);
      const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response(body, 201));
      let downstreamAuthority: unknown;

      try {
        const result = await createPreTradeRiskDecision(
          riskRequest,
          "risk-key",
          fetchMock,
        );
        downstreamAuthority = result.data;
      } catch (error) {
        expect(error).toMatchObject({
          code: "api_response_invalid",
          requestId: raw.requestId,
        });
      }

      expect(downstreamAuthority).toBeUndefined();
    },
  );

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

describe("Sprint 204 Web authority boundary", () => {
  it("uses generated contracts as the M33 transport type source", () => {
    const client = source("src/lib/api-client.ts");
    const validators = source("src/lib/strategy-order-validators.ts");
    expect(client).toContain('import type { paths } from "@/generated/api-types"');
    expect(client).toContain("type StrategySignalEvaluateRequest = PostRequestBody");
    expect(client).toContain("type PreTradeRiskDecisionCreateRequest = PostRequestBody");
    expect(validators).toContain('import type { components } from "@/generated/api-types"');
    expect(validators).not.toMatch(/\bany\b/);
  });

  it("introduces no parallel browser authority or mutation client", () => {
    const workspace = source("src/components/strategy-to-risk-workspace.tsx");
    expect(workspace).not.toMatch(/\bfetch\s*\(/);
    expect(workspace).not.toMatch(/postPaperAccount|createPaperAccount|runMarket|advanceReplay|pauseReplay|resumeReplay/);
    expect(workspace).not.toMatch(/sqlite|python process|qmt|miniqmt|broker adapter/i);
    expect(workspace).not.toMatch(/\bany\b/);
  });

  it("keeps account identity out of the dedicated Risk request block", () => {
    const workspace = source("src/components/strategy-to-risk-workspace.tsx");
    const riskBlock = workspace.slice(
      workspace.indexOf("const riskRequest"),
      workspace.indexOf("const riskFingerprint"),
    );
    const accountBlock = riskBlock.slice(
      riskBlock.indexOf("account: {"),
      riskBlock.indexOf("market: {"),
    );
    expect(accountBlock).toContain("expected_account_head_version");
    expect(accountBlock).toContain("expected_account_head_event_id");
    expect(accountBlock).toContain("expected_account_head_chain_digest");
    expect(accountBlock).not.toContain("account_id");
  });
});
