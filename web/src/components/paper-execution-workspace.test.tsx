import { readFileSync } from "node:fs";

import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PaperExecutionWorkspace } from "@/components/paper-execution-workspace";
import { ApiClientError } from "@/lib/api-client";
import { render, screen, waitFor, within } from "@/test/render";
import {
  executionOrderCommand,
  executionOrderView,
  executionRaw,
  executionReconciliation,
  executionStepCommand,
} from "@/test/paper-execution-fixtures";
import { intentCommand, rejectedRiskCommand, riskCommand } from "@/test/strategy-order-fixtures";

const apiMocks = vi.hoisted(() => ({
  createPaperExecutionOrder: vi.fn(),
  fetchOrderIntents: vi.fn(),
  fetchPaperExecutionAttempts: vi.fn(),
  fetchPaperExecutionFills: vi.fn(),
  fetchPaperExecutionOrderDetail: vi.fn(),
  fetchPaperExecutionOrders: vi.fn(),
  fetchPaperExecutionReconciliation: vi.fn(),
  fetchPreTradeRiskDecisions: vi.fn(),
  stepPaperExecutionOrder: vi.fn(),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...original, ...apiMocks };
});

function result<T>(data: T) {
  return Promise.resolve({ data, requestId: executionRaw.requestId });
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMocks.fetchPreTradeRiskDecisions.mockReturnValue(result({
    schema_version: 1,
    items: [riskCommand.decision, rejectedRiskCommand.decision],
    next_cursor: null,
  }));
  apiMocks.fetchOrderIntents.mockReturnValue(result({
    schema_version: 1,
    items: [intentCommand.result],
    next_cursor: null,
  }));
  apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({
    schema_version: 1,
    items: [executionOrderView],
    next_cursor: null,
  }));
  apiMocks.fetchPaperExecutionOrderDetail.mockReturnValue(result(executionOrderView));
  apiMocks.fetchPaperExecutionAttempts.mockReturnValue(result({ schema_version: 1, items: [], next_cursor: null }));
  apiMocks.fetchPaperExecutionFills.mockReturnValue(result({ schema_version: 1, items: [], next_cursor: null }));
  apiMocks.fetchPaperExecutionReconciliation.mockReturnValue(result(executionReconciliation));
  apiMocks.createPaperExecutionOrder.mockReturnValue(result(executionOrderCommand));
  apiMocks.stepPaperExecutionOrder.mockReturnValue(result(executionStepCommand));
});

async function completeCreateDraft(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByRole("option", { name: new RegExp(riskCommand.decision.decision_id) });
  await user.selectOptions(screen.getByLabelText("Allowed historical Decision and matching Intent"), riskCommand.decision.decision_id);
  await user.type(screen.getByLabelText("Slippage (basis-point string)"), "1.2500");
  await user.type(screen.getByLabelText("Commission (basis-point string)"), "2.5000");
  await user.type(screen.getByLabelText("Fee (basis-point string)"), "0.1250");
  await user.type(screen.getByLabelText("Buy tax (basis-point string)"), "0.0000");
  await user.type(screen.getByLabelText("Sell tax (basis-point string)"), "1.7500");
}

describe("Paper Execution workspace", () => {
  it("is one WorkspaceShell route and navigation destination with exact active semantics", () => {
    const page = readFileSync("src/app/paper-execution/page.tsx", "utf8");
    expect(page).toContain("<WorkspaceShell>");
    expect(page).toContain("<PaperExecutionWorkspace />");
    expect(page).not.toMatch(/\[execution|\[fill|\[attempt/);
  });

  it("offers only exact allow + matching Intent evidence and submits only the generated create contract", async () => {
    const user = userEvent.setup();
    render(<PaperExecutionWorkspace />);
    await completeCreateDraft(user);

    expect(screen.queryByRole("option", { name: new RegExp(rejectedRiskCommand.decision.decision_id) })).not.toBeInTheDocument();
    expect(screen.getByText(/does not establish current M31\/M32 freshness/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Create execution order" }));

    await waitFor(() => expect(apiMocks.createPaperExecutionOrder).toHaveBeenCalledTimes(1));
    const [request, key] = apiMocks.createPaperExecutionOrder.mock.calls[0];
    expect(request).toEqual({
      intent: { intent_id: intentCommand.result.intent_id, intent_digest: intentCommand.result.intent_digest },
      decision: { decision_id: riskCommand.decision.decision_id, decision_digest: riskCommand.decision.decision_digest },
      execution_policy: {
        max_fill_quantity_per_trade_event: null,
        slippage_bps: "1.2500",
        commission_bps: "2.5000",
        fee_bps: "0.1250",
        buy_tax_bps: "0.0000",
        sell_tax_bps: "1.7500",
      },
      actor: "founder",
    });
    expect(request).not.toHaveProperty("side");
    expect(request).not.toHaveProperty("requested_quantity");
    expect(request).not.toHaveProperty("price");
    expect(key).toMatch(/^s213-create-/);
    expect(screen.queryByText(key)).not.toBeInTheDocument();
    expect(await screen.findByText("New execution order authority")).toBeVisible();
  });

  it("keeps one hidden create key for exact retry, rotates on material change, and preserves the draft", async () => {
    const user = userEvent.setup();
    apiMocks.createPaperExecutionOrder.mockRejectedValueOnce(new ApiClientError({
      status: 409,
      code: "paper_execution_idempotency_conflict",
      publicMessage: "Exact conflict",
      requestId: "request-conflict",
    })).mockRejectedValueOnce(new ApiClientError({
      status: 503,
      code: "paper_execution_storage_busy",
      publicMessage: "Busy",
      requestId: "request-busy",
    })).mockReturnValueOnce(result(executionOrderCommand));
    render(<PaperExecutionWorkspace />);
    await completeCreateDraft(user);

    await user.click(screen.getByRole("button", { name: "Create execution order" }));
    await user.click(await screen.findByRole("button", { name: "Retry exact request" }));
    expect(apiMocks.createPaperExecutionOrder.mock.calls[0][1]).toBe(apiMocks.createPaperExecutionOrder.mock.calls[1][1]);
    expect(screen.getByLabelText("Fee (basis-point string)")).toHaveValue("0.1250");
    expect(screen.getByLabelText("Allowed historical Decision and matching Intent")).toHaveValue(riskCommand.decision.decision_id);

    await user.type(screen.getByLabelText("Fee (basis-point string)"), "1");
    await user.click(screen.getByRole("button", { name: "Create execution order" }));
    expect(apiMocks.createPaperExecutionOrder.mock.calls[2][1]).not.toBe(apiMocks.createPaperExecutionOrder.mock.calls[1][1]);
  });

  it("loads durable history, submits one Step per click, and displays exact backend evidence", async () => {
    const user = userEvent.setup();
    let resolveStep: ((value: { data: typeof executionStepCommand; requestId: string }) => void) | undefined;
    apiMocks.stepPaperExecutionOrder.mockReturnValue(new Promise((resolve) => {
      resolveStep = resolve;
    }));
    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    expect(within(table).getAllByText("10.2300").length).toBe(2);
    await user.click(within(table).getByRole("button", { name: "Inspect" }));
    await screen.findByText("Order, state, and exact M31/M32/M33 handoff");
    const step = screen.getByRole("button", { name: "Process next event" });
    await user.click(step);
    await user.click(step);
    expect(apiMocks.stepPaperExecutionOrder).toHaveBeenCalledTimes(1);

    expect(apiMocks.stepPaperExecutionOrder.mock.calls[0][0]).toBe(executionRaw.orderId);
    expect(apiMocks.stepPaperExecutionOrder.mock.calls[0][1]).toEqual({
      execution_order_digest: executionRaw.orderDigest,
      expected_execution_version: 0,
      actor: "founder",
    });
    expect(apiMocks.stepPaperExecutionOrder.mock.calls[0][1]).not.toHaveProperty("event_id");
    expect(apiMocks.stepPaperExecutionOrder.mock.calls[0][1]).not.toHaveProperty("fill");
    resolveStep?.({ data: executionStepCommand, requestId: executionRaw.requestId });
    expect(await screen.findByText("Committed one-event Step authority")).toBeVisible();
    expect(screen.getAllByText("12.34154250").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.01052861").length).toBeGreaterThan(0);
    expect(screen.getAllByText("3.2500").length).toBeGreaterThan(0);
    expect(screen.getAllByText("account-event-s213-fill").length).toBeGreaterThan(0);
  });

  it("runs reconciliation only explicitly and retains historical inspection on failure", async () => {
    const user = userEvent.setup();
    apiMocks.fetchPaperExecutionReconciliation.mockRejectedValue(new ApiClientError({
      status: 409,
      code: "paper_execution_reconciliation_required",
      publicMessage: "Mismatch retained",
      requestId: "request-reconciliation",
    }));
    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    await user.click(within(table).getByRole("button", { name: "Inspect" }));
    expect(apiMocks.fetchPaperExecutionReconciliation).not.toHaveBeenCalled();
    await user.click(await screen.findByRole("button", { name: "Run reconciliation check" }));
    expect(await screen.findByText("Paper Execution reconciliation is required")).toBeVisible();
    expect(screen.getAllByText(executionRaw.orderId).length).toBeGreaterThan(0);
    expect(screen.getByText(/Historical inspection/)).toBeVisible();
    expect(apiMocks.stepPaperExecutionOrder).not.toHaveBeenCalled();
  });

  it("renders the same exact durable values in Simplified Chinese", async () => {
    render(<PaperExecutionWorkspace />, { locale: "zh-CN" });
    expect(await screen.findByRole("heading", { name: "模拟执行" })).toBeVisible();
    expect(screen.getAllByText("10.2300").length).toBe(2);
    expect(screen.getByRole("table", { name: /持久化模拟执行订单/ })).toHaveTextContent(executionRaw.orderId);
  });
});

describe("Paper Execution browser exclusions", () => {
  it("contains no financial/execution calculation or direct M31/M32 mutation", () => {
    const source = readFileSync("src/components/paper-execution-workspace.tsx", "utf8");
    expect(source).not.toMatch(/parseFloat|parseInt|toFixed|Intl\.NumberFormat/);
    expect(source).not.toMatch(/createPaperExecutionFill|postPaperAccount|advanceReplay|resumeReplay|pauseReplay/);
    expect(source).not.toMatch(/setInterval|setTimeout|run until filled|automatic step/i);
    expect(source).not.toMatch(/\b(fetch|axios)\s*\(/);
  });
});
