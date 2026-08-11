import { NextIntlClientProvider } from "next-intl";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StrategyToRiskWorkspace } from "@/components/strategy-to-risk-workspace";
import { loadMessages } from "@/i18n/messages";
import { ApiClientError } from "@/lib/api-client";
import { fireEvent, render, screen, waitFor, within } from "@/test/render";
import {
  calendarDetail,
  calendarList,
  intentCommand,
  noActionCommand,
  paperAccountDetail,
  paperAccountList,
  raw,
  rejectedRiskCommand,
  replayDetail,
  replayList,
  riskCommand,
  signalCommand,
} from "@/test/strategy-order-fixtures";

const apiMocks = vi.hoisted(() => ({
  fetchPaperAccounts: vi.fn(),
  fetchTradingCalendars: vi.fn(),
  fetchMarketDataReplays: vi.fn(),
  fetchPaperAccountDetail: vi.fn(),
  fetchTradingCalendarDetail: vi.fn(),
  fetchMarketDataReplayDetail: vi.fn(),
  evaluateStrategySignal: vi.fn(),
  createOrderIntent: vi.fn(),
  createPreTradeRiskDecision: vi.fn(),
}));

vi.mock("@/lib/api-client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api-client")>()),
  ...apiMocks,
}));

function apiResult<Data>(data: Data) {
  return Promise.resolve({ data, requestId: raw.requestId });
}

beforeEach(() => {
  apiMocks.fetchPaperAccounts.mockReturnValue(apiResult(paperAccountList));
  apiMocks.fetchTradingCalendars.mockReturnValue(apiResult(calendarList));
  apiMocks.fetchMarketDataReplays.mockReturnValue(apiResult(replayList));
  apiMocks.fetchPaperAccountDetail.mockReturnValue(apiResult(paperAccountDetail));
  apiMocks.fetchTradingCalendarDetail.mockReturnValue(apiResult(calendarDetail));
  apiMocks.fetchMarketDataReplayDetail.mockReturnValue(apiResult(replayDetail));
  apiMocks.evaluateStrategySignal.mockReturnValue(apiResult(signalCommand));
  apiMocks.createOrderIntent.mockReturnValue(apiResult(intentCommand));
  apiMocks.createPreTradeRiskDecision.mockReturnValue(apiResult(riskCommand));
});

async function selectAuthorities() {
  const account = await screen.findByRole("combobox", { name: "Paper Account" });
  fireEvent.change(account, { target: { value: raw.accountId } });
  fireEvent.click(screen.getByRole("button", { name: "Load selected account anchors" }));
  await screen.findByText(raw.accountChainDigest);

  fireEvent.change(
    screen.getByRole("combobox", { name: "Trading calendar" }),
    { target: { value: raw.calendarId } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Load calendar sessions" }));
  await waitFor(() =>
    expect(screen.getByRole("combobox", { name: "Trading session" })).toBeEnabled(),
  );
  fireEvent.change(
    screen.getByRole("combobox", { name: "Trading session" }),
    { target: { value: raw.sessionId } },
  );

  fireEvent.change(
    screen.getByRole("combobox", { name: "Market-data replay" }),
    { target: { value: raw.replayId } },
  );
  fireEvent.click(screen.getByRole("button", { name: "Load current replay anchors" }));
  await screen.findByText(raw.streamDigest);
  fireEvent.change(screen.getByRole("textbox", { name: "Instrument ID" }), {
    target: { value: raw.instrumentId },
  });
}

async function evaluateSignal() {
  fireEvent.click(screen.getByRole("button", { name: "Evaluate Signal" }));
  await screen.findByText(raw.signalId);
}

describe("Founder Strategy-to-Risk workspace", () => {
  it("starts without fabricated authority and never posts on mount or selection", async () => {
    render(<StrategyToRiskWorkspace />);

    expect(await screen.findByRole("heading", { name: "Strategy-to-Risk Workspace" })).toBeVisible();
    expect(screen.getByText("No Signal authority has been returned. Nothing is inferred or fabricated.")).toBeVisible();
    expect(screen.getByText("No Intent or no-action authority has been returned.")).toBeVisible();
    expect(screen.getByText("No Risk Decision authority has been returned.")).toBeVisible();
    expect(apiMocks.evaluateStrategySignal).not.toHaveBeenCalled();
    expect(apiMocks.createOrderIntent).not.toHaveBeenCalled();
    expect(apiMocks.createPreTradeRiskDecision).not.toHaveBeenCalled();

    fireEvent.change(
      screen.getByRole("combobox", { name: "Paper Account" }),
      { target: { value: raw.accountId } },
    );
    fireEvent.change(
      screen.getByRole("combobox", { name: "Trading calendar" }),
      { target: { value: raw.calendarId } },
    );
    fireEvent.change(
      screen.getByRole("combobox", { name: "Market-data replay" }),
      { target: { value: raw.replayId } },
    );
    expect(apiMocks.evaluateStrategySignal).not.toHaveBeenCalled();
    expect(apiMocks.createOrderIntent).not.toHaveBeenCalled();
    expect(apiMocks.createPreTradeRiskDecision).not.toHaveBeenCalled();
  });

  it("constructs the exact Signal → Intent → Risk commands and renders complete allow evidence", async () => {
    render(<StrategyToRiskWorkspace />);
    await selectAuthorities();

    await evaluateSignal();
    expect(apiMocks.evaluateStrategySignal).toHaveBeenCalledWith(
      {
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
      },
      expect.stringMatching(/^s204-signal-/),
    );

    fireEvent.click(screen.getByRole("button", { name: "Derive Intent" }));
    await screen.findByText(raw.intentId);
    const intentRequest = apiMocks.createOrderIntent.mock.calls[0][0];
    expect(intentRequest).toEqual({
      signal_id: raw.signalId,
      account: {
        account_id: raw.accountId,
        expected_account_head_version: 1,
        expected_account_head_event_id: raw.accountEventId,
        expected_account_head_chain_digest: raw.accountChainDigest,
      },
      intent_policy_version: "target_position_quantity_delta_v1",
      actor: "founder",
    });
    expect(intentRequest).not.toHaveProperty("side");
    expect(intentRequest).not.toHaveProperty("requested_quantity");
    expect(intentRequest).not.toHaveProperty("cash");
    expect(screen.getByText("buy")).toBeVisible();
    expect(screen.getAllByText("100").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByRole("textbox", { name: "Maximum order quantity" }), {
      target: { value: "200" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Maximum order notional" }), {
      target: { value: "2000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Evaluate Risk" }));
    await screen.findByText(raw.decisionId);
    const riskRequest = apiMocks.createPreTradeRiskDecision.mock.calls[0][0];
    expect(riskRequest.account).toEqual({
      expected_account_head_version: 1,
      expected_account_head_event_id: raw.accountEventId,
      expected_account_head_chain_digest: raw.accountChainDigest,
    });
    expect(riskRequest.account).not.toHaveProperty("account_id");
    expect(riskRequest.market).toEqual({
      expected_calendar_id: raw.calendarId,
      expected_calendar_version: 1,
      expected_trading_session_id: raw.sessionId,
      expected_replay_id: raw.replayId,
      expected_event_stream_digest: raw.streamDigest,
      expected_cursor_position: 2,
      expected_current_event_id: raw.eventId,
      expected_current_event_time_utc: raw.eventTime,
      expected_instrument_id: raw.instrumentId,
    });
    expect(riskRequest).not.toHaveProperty("price");
    expect(riskRequest).not.toHaveProperty("notional");
    expect(riskRequest).not.toHaveProperty("rules");
    expect(riskRequest).not.toHaveProperty("outcome");
    expect(riskRequest).not.toHaveProperty("reason_codes");

    const rules = screen.getByRole("heading", { name: "Four ordered risk-rule records" }).closest("section");
    expect(rules).not.toBeNull();
    const ruleItems = within(rules as HTMLElement).getAllByRole("listitem");
    expect(ruleItems).toHaveLength(4);
    expect(ruleItems.map((item) => item.textContent)).toEqual([
      expect.stringContaining("insufficient_position_quantity"),
      expect.stringContaining("maximum_order_quantity_exceeded"),
      expect.stringContaining("maximum_order_notional_exceeded"),
      expect.stringContaining("insufficient_available_cash"),
    ]);
    expect(screen.getByText(/Valid pre-trade allow evidence/)).toBeVisible();
    expect(screen.queryByRole("button", { name: /execute|trade|fill|route|cancel order/i })).not.toBeInTheDocument();
  });

  it("treats no-action as terminal and never enables Risk", async () => {
    apiMocks.createOrderIntent.mockReturnValue(apiResult(noActionCommand));
    render(<StrategyToRiskWorkspace />);
    await selectAuthorities();
    await evaluateSignal();
    fireEvent.click(screen.getByRole("button", { name: "Derive Intent" }));

    expect(await screen.findByText(raw.noActionId)).toBeVisible();
    expect(screen.getByText("target_already_satisfied")).toBeVisible();
    expect(screen.getByRole("button", { name: "Evaluate Risk" })).toBeDisabled();
    expect(screen.getByText("The no-action result is terminal; there is no Intent to evaluate for risk.")).toBeVisible();
    expect(apiMocks.createPreTradeRiskDecision).not.toHaveBeenCalled();
  });

  it("reuses one key for an exact retry and rotates after a settled material change", async () => {
    apiMocks.evaluateStrategySignal
      .mockRejectedValueOnce(new ApiClientError({
        status: 0,
        code: "api_unavailable",
        publicMessage: "The local API is unavailable.",
        requestId: null,
      }))
      .mockReturnValueOnce(apiResult(signalCommand))
      .mockReturnValueOnce(apiResult({
        ...signalCommand,
        signal: {
          ...signalCommand.signal,
          target_position_quantity: "101",
          strategy_runtime_reference: {
            ...signalCommand.signal.strategy_runtime_reference,
            parameters: {
              ...signalCommand.signal.strategy_runtime_reference.parameters,
              target_position_quantity: "101",
            },
          },
        },
      }));
    render(<StrategyToRiskWorkspace />);
    await selectAuthorities();

    fireEvent.click(screen.getByRole("button", { name: "Evaluate Signal" }));
    await screen.findByRole("button", { name: "Retry the unchanged Signal draft" });
    fireEvent.click(screen.getByRole("button", { name: "Retry the unchanged Signal draft" }));
    await screen.findByText(raw.signalId);

    const firstKey = apiMocks.evaluateStrategySignal.mock.calls[0][1];
    const retryKey = apiMocks.evaluateStrategySignal.mock.calls[1][1];
    expect(retryKey).toBe(firstKey);

    const target = screen.getByRole("textbox", { name: "Target position quantity" });
    fireEvent.change(target, { target: { value: "101" } });
    fireEvent.click(screen.getByRole("button", { name: "Evaluate Signal" }));
    await waitFor(() => expect(apiMocks.evaluateStrategySignal).toHaveBeenCalledTimes(3));
    expect(apiMocks.evaluateStrategySignal.mock.calls[2][1]).not.toBe(firstKey);
  });

  it("preserves evidence and drafts on stale authority without auto-refresh or retry", async () => {
    apiMocks.createOrderIntent.mockRejectedValue(new ApiClientError({
      status: 409,
      code: "strategy_order_stale_authority",
      publicMessage: "Strategy-to-risk authority is stale",
      requestId: "stale-request-id",
    }));
    render(<StrategyToRiskWorkspace />);
    await selectAuthorities();
    await evaluateSignal();
    fireEvent.click(screen.getByRole("button", { name: "Derive Intent" }));

    expect(await screen.findByText(/strategy_order_stale_authority/)).toBeVisible();
    expect(screen.getByText("Strategy-to-risk authority is stale")).toBeVisible();
    expect(screen.getByText(/stale-request-id/)).toBeVisible();
    expect(screen.getByText(raw.signalId)).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Target position quantity" })).toHaveValue("100");
    expect(apiMocks.createOrderIntent).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchPaperAccountDetail).toHaveBeenCalledTimes(1);

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(apiMocks.createOrderIntent).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchPaperAccountDetail).toHaveBeenCalledTimes(1);
  });

  it("renders reject as complete immutable evidence rather than an API error", async () => {
    apiMocks.createPreTradeRiskDecision.mockReturnValue(apiResult(rejectedRiskCommand));
    render(<StrategyToRiskWorkspace />);
    await selectAuthorities();
    await evaluateSignal();
    fireEvent.click(screen.getByRole("button", { name: "Derive Intent" }));
    await screen.findByText(raw.intentId);
    fireEvent.change(screen.getByRole("textbox", { name: "Maximum order quantity" }), {
      target: { value: "200" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Maximum order notional" }), {
      target: { value: "2000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Evaluate Risk" }));

    expect(await screen.findByText(/Valid pre-trade reject evidence/)).toBeVisible();
    expect(screen.getAllByText("insufficient_available_cash").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Reject is valid immutable product evidence, not an API error. All ordered rule and reason evidence remains visible.")).toBeVisible();
  });

  it("preserves raw evidence and sends no POST when the locale changes", async () => {
    function LocaleHarness() {
      const [locale, setLocale] = useState<"en" | "zh-CN">("en");
      return (
        <NextIntlClientProvider locale={locale} messages={loadMessages(locale)}>
          <button type="button" onClick={() => setLocale("zh-CN")}>switch locale</button>
          <StrategyToRiskWorkspace />
        </NextIntlClientProvider>
      );
    }

    render(<LocaleHarness />);
    await selectAuthorities();
    await evaluateSignal();
    const postsBefore = apiMocks.evaluateStrategySignal.mock.calls.length;

    fireEvent.click(screen.getByRole("button", { name: "switch locale" }));
    expect(await screen.findByRole("heading", { name: "策略到风控工作区" })).toBeVisible();
    expect(screen.getByText(raw.signalId)).toBeVisible();
    expect(screen.getByText(raw.signalDigest)).toBeVisible();
    expect(screen.getAllByText("100").length).toBeGreaterThan(0);
    expect(screen.getByText(raw.timestamp)).toBeVisible();
    expect(apiMocks.evaluateStrategySignal).toHaveBeenCalledTimes(postsBefore);
    expect(apiMocks.createOrderIntent).not.toHaveBeenCalled();
    expect(apiMocks.createPreTradeRiskDecision).not.toHaveBeenCalled();
  });
});
