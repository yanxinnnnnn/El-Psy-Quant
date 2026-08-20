import { readFileSync } from "node:fs";

import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PaperExecutionWorkspace } from "@/components/paper-execution-workspace";
import {
  ApiClientError,
  type PaperExecutionAttemptResponse,
  type PaperExecutionFillResponse,
  type PaperExecutionOrderViewResponse,
} from "@/lib/api-client";
import { render, screen, waitFor, within } from "@/test/render";
import {
  executionAttempt,
  executionFill,
  executionOrderCommand,
  executionOrderView,
  executionRaw,
  executionReconciliation,
  executionStepCommand,
} from "@/test/paper-execution-fixtures";
import { intentCommand, rejectedRiskCommand, riskCommand } from "@/test/strategy-order-fixtures";

const apiMocks = vi.hoisted(() => ({
  createPaperExecutionOrder: vi.fn(),
  fetchOrderIntentDetail: vi.fn(),
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

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

function orderView(character: string, createdAt: string): PaperExecutionOrderViewResponse {
  const orderId = `peo_${character.repeat(64)}`;
  const orderDigest = character.repeat(64);
  return {
    ...executionOrderView,
    order: {
      ...executionOrderView.order,
      execution_order_id: orderId,
      execution_order_digest: orderDigest,
      created_at: createdAt,
    },
    state: {
      ...executionOrderView.state,
      execution_order_reference: {
        ...executionOrderView.state.execution_order_reference,
        execution_order_id: orderId,
        execution_order_digest: orderDigest,
      },
    },
  };
}

function attempt(character: string, version: number): PaperExecutionAttemptResponse {
  return {
    ...executionAttempt,
    attempt_id: `pea_${character.repeat(64)}`,
    attempt_digest: character.repeat(64),
    execution_version_before: version,
    execution_version_after: version + 1,
    created_at: `2026-08-11T02:0${version}:00Z`,
  };
}

function fill(character: string, createdAt: string): PaperExecutionFillResponse {
  return {
    ...executionFill,
    fill_id: `pef_${character.repeat(64)}`,
    fill_digest: character.repeat(64),
    created_at: createdAt,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMocks.fetchPreTradeRiskDecisions.mockReturnValue(result({
    schema_version: 1,
    items: [riskCommand.decision, rejectedRiskCommand.decision],
    next_cursor: null,
  }));
  apiMocks.fetchOrderIntentDetail.mockReturnValue(result(intentCommand.result));
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

  it("discovers candidates by Decision pages and resolves every exact referenced Intent detail", async () => {
    const user = userEvent.setup();
    const secondIntent = {
      ...intentCommand.result,
      intent_id: `oi_${"7".repeat(64)}`,
      intent_digest: "8".repeat(64),
    };
    const secondDecision = {
      ...riskCommand.decision,
      decision_id: `risk_decision_${"9".repeat(64)}`,
      decision_digest: "0".repeat(64),
      input_snapshot: {
        ...riskCommand.decision.input_snapshot,
        intent_reference: {
          ...riskCommand.decision.input_snapshot.intent_reference,
          intent_id: secondIntent.intent_id,
          intent_digest: secondIntent.intent_digest,
        },
      },
    };
    apiMocks.fetchPreTradeRiskDecisions
      .mockReturnValueOnce(result({ schema_version: 1, items: [riskCommand.decision], next_cursor: "decision-page-2+/=" }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [secondDecision], next_cursor: null }));
    apiMocks.fetchOrderIntentDetail.mockImplementation((intentId: string) => result(
      intentId === secondIntent.intent_id ? secondIntent : intentCommand.result,
    ));

    render(<PaperExecutionWorkspace />);

    expect(await screen.findByRole("option", { name: new RegExp(riskCommand.decision.decision_id) })).toBeVisible();
    expect(apiMocks.fetchOrderIntentDetail).toHaveBeenCalledWith(intentCommand.result.intent_id);
    expect(apiMocks.fetchOrderIntentDetail).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Load next bounded page" }));
    expect(await screen.findByRole("option", { name: new RegExp(secondDecision.decision_id) })).toBeVisible();
    expect(apiMocks.fetchPreTradeRiskDecisions).toHaveBeenLastCalledWith({
      outcome: "allow",
      limit: 50,
      cursor: "decision-page-2+/=",
    });
    expect(apiMocks.fetchOrderIntentDetail).toHaveBeenLastCalledWith(secondIntent.intent_id);
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

  it("keeps out-of-order A to B selection responses scoped to the latest Order authority", async () => {
    const user = userEvent.setup();
    const orderA = executionOrderView;
    const orderB = orderView("7", "2026-08-11T02:02:00Z");
    const aDetail = deferred<Awaited<ReturnType<typeof result<PaperExecutionOrderViewResponse>>>>();
    const bDetail = deferred<Awaited<ReturnType<typeof result<PaperExecutionOrderViewResponse>>>>();
    const aAttempts = deferred<Awaited<ReturnType<typeof result<{ schema_version: 1; items: []; next_cursor: null }>>>>();
    const bAttempts = deferred<Awaited<ReturnType<typeof result<{ schema_version: 1; items: []; next_cursor: null }>>>>();
    const aFills = deferred<Awaited<ReturnType<typeof result<{ schema_version: 1; items: []; next_cursor: null }>>>>();
    const bFills = deferred<Awaited<ReturnType<typeof result<{ schema_version: 1; items: []; next_cursor: null }>>>>();
    apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({ schema_version: 1, items: [orderA, orderB], next_cursor: null }));
    apiMocks.fetchPaperExecutionOrderDetail.mockImplementation((orderId: string) => orderId === orderA.order.execution_order_id ? aDetail.promise : bDetail.promise);
    apiMocks.fetchPaperExecutionAttempts.mockImplementation((orderId: string) => orderId === orderA.order.execution_order_id ? aAttempts.promise : bAttempts.promise);
    apiMocks.fetchPaperExecutionFills.mockImplementation(({ execution_order_id: orderId }: { execution_order_id: string }) => orderId === orderA.order.execution_order_id ? aFills.promise : bFills.promise);

    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    const inspect = within(table).getAllByRole("button", { name: "Inspect" });
    await user.click(inspect[0]);
    await user.click(inspect[1]);

    bDetail.resolve({ data: orderB, requestId: executionRaw.requestId });
    bAttempts.resolve({ data: { schema_version: 1, items: [], next_cursor: null }, requestId: executionRaw.requestId });
    bFills.resolve({ data: { schema_version: 1, items: [], next_cursor: null }, requestId: executionRaw.requestId });
    const step = await screen.findByRole("button", { name: "Process next event" });
    expect(step).toBeEnabled();

    aDetail.resolve({ data: orderA, requestId: executionRaw.requestId });
    aAttempts.resolve({ data: { schema_version: 1, items: [], next_cursor: null }, requestId: executionRaw.requestId });
    aFills.resolve({ data: { schema_version: 1, items: [], next_cursor: null }, requestId: executionRaw.requestId });
    await user.click(screen.getByRole("button", { name: "Run reconciliation check" }));
    expect(apiMocks.fetchPaperExecutionReconciliation).toHaveBeenCalledWith(orderB.order.execution_order_id);
    expect(screen.getByRole("button", { name: "Process next event" })).toBeEnabled();
  });

  it("ignores a late paginated history response after selection changes", async () => {
    const user = userEvent.setup();
    const orderA = executionOrderView;
    const orderB = orderView("7", "2026-08-11T02:02:00Z");
    const firstA = attempt("4", 0);
    const lateA = attempt("5", 1);
    const firstB = attempt("6", 0);
    const latePage = deferred<Awaited<ReturnType<typeof result<{ schema_version: 1; items: PaperExecutionAttemptResponse[]; next_cursor: null }>>>>();
    apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({ schema_version: 1, items: [orderA, orderB], next_cursor: null }));
    apiMocks.fetchPaperExecutionOrderDetail.mockImplementation((orderId: string) => result(orderId === orderA.order.execution_order_id ? orderA : orderB));
    apiMocks.fetchPaperExecutionAttempts.mockImplementation((orderId: string, filters: { cursor?: string }) => {
      if (orderId === orderB.order.execution_order_id) return result({ schema_version: 1, items: [firstB], next_cursor: null });
      if (filters.cursor) return latePage.promise;
      return result({ schema_version: 1, items: [firstA], next_cursor: "attempt-a-page-2" });
    });

    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    await user.click(within(table).getAllByRole("button", { name: "Inspect" })[0]);
    const attemptsSection = screen.getByRole("heading", { name: "Execution Attempts" }).closest("section")!;
    await within(attemptsSection).findByText(firstA.attempt_id);
    await user.click(within(attemptsSection).getByRole("button", { name: "Load next bounded page" }));
    await user.click(within(table).getAllByRole("button", { name: "Inspect" })[1]);
    expect(await screen.findByText(firstB.attempt_id)).toBeVisible();
    const selectedBAttempts = screen.getByRole("heading", { name: "Execution Attempts" }).closest("section")!;

    latePage.resolve({ data: { schema_version: 1, items: [lateA], next_cursor: null }, requestId: executionRaw.requestId });
    await waitFor(() => expect(within(selectedBAttempts).queryByText(lateA.attempt_id)).not.toBeInTheDocument());
    expect(within(selectedBAttempts).getByText(firstB.attempt_id)).toBeVisible();
  });

  it("does not let a pending A Step overwrite B after the Founder changes selection", async () => {
    const user = userEvent.setup();
    const orderA = executionOrderView;
    const orderB = orderView("7", "2026-08-11T02:02:00Z");
    const pendingStep = deferred<{ data: typeof executionStepCommand; requestId: string }>();
    apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({ schema_version: 1, items: [orderA, orderB], next_cursor: null }));
    apiMocks.fetchPaperExecutionOrderDetail.mockImplementation((orderId: string) => result(orderId === orderA.order.execution_order_id ? orderA : orderB));
    apiMocks.stepPaperExecutionOrder.mockReturnValueOnce(pendingStep.promise);

    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    const inspect = within(table).getAllByRole("button", { name: "Inspect" });
    await user.click(inspect[0]);
    await user.click(await screen.findByRole("button", { name: "Process next event" }));
    await user.click(within(table).getAllByRole("button", { name: "Inspect" })[1]);
    await waitFor(() => expect(within(table).getAllByRole("button", { name: "Inspect" })[1]).toHaveAttribute("aria-pressed", "true"));
    await waitFor(() => expect(screen.getByRole("button", { name: "Process next event" })).toBeDisabled());

    pendingStep.resolve({ data: executionStepCommand, requestId: executionRaw.requestId });
    await waitFor(() => expect(screen.getByRole("button", { name: "Process next event" })).toBeEnabled());
    expect(screen.queryByText("Committed one-event Step authority")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Run reconciliation check" }));
    expect(apiMocks.fetchPaperExecutionReconciliation).toHaveBeenLastCalledWith(orderB.order.execution_order_id);
    expect(apiMocks.fetchPaperExecutionOrderDetail).toHaveBeenCalledTimes(2);
  });

  it("reloads paginated Attempt and newest-first Fill history from S212 after Step", async () => {
    const user = userEvent.setup();
    const initialOrder: PaperExecutionOrderViewResponse = {
      ...executionOrderView,
      state: { ...executionOrderView.state, execution_version: 2 },
    };
    const updatedOrder: PaperExecutionOrderViewResponse = {
      ...initialOrder,
      state: { ...initialOrder.state, execution_version: 3 },
    };
    const firstAttempt = attempt("4", 0);
    const steppedAttempt = attempt("5", 2);
    const laterPageAttempt = attempt("6", 1);
    const olderFill = fill("4", "2026-08-11T02:01:00Z");
    const newestFill = fill("5", "2026-08-11T02:03:00Z");
    const oldestFill = fill("6", "2026-08-11T02:00:00Z");
    const stepCommand = {
      ...executionStepCommand,
      result: {
        ...executionStepCommand.result,
        attempt: steppedAttempt,
        fill: newestFill,
        order_state: updatedOrder.state,
      },
    };
    apiMocks.fetchPaperExecutionOrderDetail
      .mockReturnValueOnce(result(initialOrder))
      .mockReturnValueOnce(result(updatedOrder));
    apiMocks.fetchPaperExecutionAttempts
      .mockReturnValueOnce(result({ schema_version: 1, items: [firstAttempt], next_cursor: "attempt-before-step" }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [firstAttempt, steppedAttempt], next_cursor: "attempt-after-step" }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [laterPageAttempt], next_cursor: null }));
    apiMocks.fetchPaperExecutionFills
      .mockReturnValueOnce(result({ schema_version: 1, items: [olderFill], next_cursor: "fill-before-step" }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [newestFill, olderFill], next_cursor: "fill-after-step" }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [oldestFill], next_cursor: null }));
    apiMocks.stepPaperExecutionOrder.mockReturnValue(result(stepCommand));

    render(<PaperExecutionWorkspace />);
    const table = await screen.findByRole("table", { name: /Durable Paper Execution orders/ });
    await user.click(within(table).getByRole("button", { name: "Inspect" }));
    await screen.findByText(firstAttempt.attempt_id);
    await user.click(screen.getByRole("button", { name: "Process next event" }));
    expect(await screen.findByText("Committed one-event Step authority")).toBeVisible();

    const attemptsSection = screen.getByRole("heading", { name: "Execution Attempts" }).closest("section")!;
    const fillsSection = screen.getByRole("heading", { name: "Execution Fills" }).closest("section")!;
    await waitFor(() => expect(within(attemptsSection).getByText(steppedAttempt.attempt_id)).toBeVisible());
    expect(apiMocks.fetchPaperExecutionAttempts).toHaveBeenNthCalledWith(2, executionRaw.orderId, { limit: 25 });
    expect(apiMocks.fetchPaperExecutionFills).toHaveBeenNthCalledWith(2, { execution_order_id: executionRaw.orderId, limit: 25 });
    expect(fillsSection.textContent!.indexOf(newestFill.fill_id)).toBeLessThan(fillsSection.textContent!.indexOf(olderFill.fill_id));

    await user.click(within(attemptsSection).getByRole("button", { name: "Load next bounded page" }));
    await user.click(within(fillsSection).getByRole("button", { name: "Load next bounded page" }));
    expect(await within(attemptsSection).findByText(laterPageAttempt.attempt_id)).toBeVisible();
    expect(await within(fillsSection).findByText(oldestFill.fill_id)).toBeVisible();
    expect(apiMocks.fetchPaperExecutionAttempts).toHaveBeenNthCalledWith(3, executionRaw.orderId, { limit: 25, cursor: "attempt-after-step" });
    expect(apiMocks.fetchPaperExecutionFills).toHaveBeenNthCalledWith(3, { execution_order_id: executionRaw.orderId, limit: 25, cursor: "fill-after-step" });
    expect(attemptsSection.textContent!.match(new RegExp(steppedAttempt.attempt_id, "g"))).toHaveLength(1);
    expect(fillsSection.textContent!.match(new RegExp(newestFill.fill_id, "g"))).toHaveLength(1);
  });

  it("hydrates durable histories and server Order ordering for a replayed progressed create", async () => {
    const user = userEvent.setup();
    const newerOrder = orderView("7", "2026-08-11T03:00:00Z");
    const progressedOrder: PaperExecutionOrderViewResponse = {
      ...executionOrderView,
      state: {
        ...executionOrderView.state,
        execution_version: 1,
        status: "partially_filled",
        cumulative_filled_quantity: "3.2500",
        remaining_quantity: "6.9800",
      },
    };
    const replayedCreate = { ...executionOrderCommand, replayed: true, result: progressedOrder };
    apiMocks.fetchPaperExecutionOrders
      .mockReturnValueOnce(result({ schema_version: 1, items: [newerOrder], next_cursor: null }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [newerOrder, progressedOrder], next_cursor: null }));
    apiMocks.fetchPaperExecutionOrderDetail.mockReturnValue(result(progressedOrder));
    apiMocks.fetchPaperExecutionAttempts.mockReturnValue(result({ schema_version: 1, items: [executionAttempt], next_cursor: null }));
    apiMocks.fetchPaperExecutionFills.mockReturnValue(result({ schema_version: 1, items: [executionFill], next_cursor: null }));
    apiMocks.createPaperExecutionOrder.mockReturnValue(result(replayedCreate));

    render(<PaperExecutionWorkspace />);
    await completeCreateDraft(user);
    await user.click(screen.getByRole("button", { name: "Create execution order" }));

    expect(await screen.findByText("Exact create command converged")).toBeVisible();
    const attemptsSection = screen.getByRole("heading", { name: "Execution Attempts" }).closest("section")!;
    const fillsSection = screen.getByRole("heading", { name: "Execution Fills" }).closest("section")!;
    expect(await within(attemptsSection).findByText(executionRaw.attemptId)).toBeVisible();
    expect(await within(fillsSection).findByText(executionRaw.fillId)).toBeVisible();
    expect(apiMocks.fetchPaperExecutionAttempts).toHaveBeenCalledWith(executionRaw.orderId, { limit: 25 });
    expect(apiMocks.fetchPaperExecutionFills).toHaveBeenCalledWith({ execution_order_id: executionRaw.orderId, limit: 25 });
    const ordersTable = screen.getByRole("table", { name: /Durable Paper Execution orders/ });
    await waitFor(() => expect(ordersTable).toHaveTextContent(executionRaw.orderId));
    expect(ordersTable.textContent!.indexOf(newerOrder.order.execution_order_id)).toBeLessThan(ordersTable.textContent!.indexOf(executionRaw.orderId));
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
