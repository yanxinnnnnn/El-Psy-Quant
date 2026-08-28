import { readFileSync } from "node:fs";

import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PaperRuntimeCreateView } from "@/components/paper-runtime-create-view";
import { PaperRuntimeDetailView } from "@/components/paper-runtime-detail-view";
import { PaperRuntimeListView } from "@/components/paper-runtime-list-view";
import { ApiClientError, type PaperRuntimeResponse } from "@/lib/api-client";
import { executionOrderView } from "@/test/paper-execution-fixtures";
import {
  paperRuntime,
  paperRuntimeAudit,
  paperRuntimeCheckpoints,
  paperRuntimeCommand,
  paperRuntimeHealth,
  paperRuntimeReconciliation,
  paperRuntimeWork,
  runtimeRaw,
} from "@/test/paper-runtime-fixtures";
import { render, screen, waitFor, within } from "@/test/render";

const apiMocks = vi.hoisted(() => ({
  createPaperRuntime: vi.fn(),
  fetchPaperExecutionOrders: vi.fn(),
  fetchPaperRuntimes: vi.fn(),
  fetchPaperRuntimeDetail: vi.fn(),
  fetchPaperRuntimeHealth: vi.fn(),
  fetchPaperRuntimeReconciliation: vi.fn(),
  fetchPaperRuntimeAudit: vi.fn(),
  fetchPaperRuntimeWork: vi.fn(),
  fetchPaperRuntimeCheckpoints: vi.fn(),
  startPaperRuntime: vi.fn(),
  stopPaperRuntime: vi.fn(),
  resumePaperRuntime: vi.fn(),
  recoverPaperRuntime: vi.fn(),
  stepPaperExecutionOrder: vi.fn(),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...original, ...apiMocks };
});

function result<T>(data: T) { return Promise.resolve({ data, requestId: runtimeRaw.requestId }); }
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => { resolve = resolvePromise; reject = rejectPromise; });
  return { promise, resolve, reject };
}
function runtime(character: string, overrides: Partial<PaperRuntimeResponse> = {}): PaperRuntimeResponse {
  return { ...paperRuntime, runtime_id: `prt_${character.repeat(64)}`, runtime_binding_digest: character.repeat(64), ...overrides };
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({ schema_version: 1, items: [executionOrderView], next_cursor: null }));
  apiMocks.fetchPaperRuntimes.mockReturnValue(result({ schema_version: 1, items: [paperRuntime], next_cursor: null }));
  apiMocks.fetchPaperRuntimeDetail.mockReturnValue(result(paperRuntime));
  apiMocks.fetchPaperRuntimeHealth.mockReturnValue(result(paperRuntimeHealth));
  apiMocks.fetchPaperRuntimeReconciliation.mockReturnValue(result(paperRuntimeReconciliation));
  apiMocks.fetchPaperRuntimeAudit.mockReturnValue(result(paperRuntimeAudit));
  apiMocks.fetchPaperRuntimeWork.mockReturnValue(result(paperRuntimeWork));
  apiMocks.fetchPaperRuntimeCheckpoints.mockReturnValue(result(paperRuntimeCheckpoints));
  apiMocks.createPaperRuntime.mockReturnValue(result(paperRuntimeCommand));
  apiMocks.startPaperRuntime.mockReturnValue(result(paperRuntimeCommand));
  apiMocks.stopPaperRuntime.mockReturnValue(result(paperRuntimeCommand));
  apiMocks.resumePaperRuntime.mockReturnValue(result(paperRuntimeCommand));
  apiMocks.recoverPaperRuntime.mockReturnValue(result(paperRuntimeCommand));
});

describe("Paper Runtime list", () => {
  it("preserves backend ordering, appends opaque pages, and resets the exact filter context", async () => {
    const user = userEvent.setup();
    const first = runtime("a", { desired_state: "running", observed_state: "ready" });
    const second = runtime("b", { desired_state: "stopped", observed_state: "blocked", block_reason_code: "authority_stale" });
    const third = runtime("c");
    apiMocks.fetchPaperRuntimes
      .mockReturnValueOnce(result({ schema_version: 1, items: [first, second], next_cursor: runtimeRaw.cursor }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [third], next_cursor: null }))
      .mockReturnValueOnce(result({ schema_version: 1, items: [second], next_cursor: null }));
    render(<PaperRuntimeListView />);

    const table = await screen.findByRole("table", { name: /backend order/ });
    expect(table.textContent!.indexOf(first.runtime_id)).toBeLessThan(table.textContent!.indexOf(second.runtime_id));
    expect(within(table).getAllByText("Requested state").length).toBeGreaterThan(0);
    expect(within(table).getAllByText("Observed runtime").length).toBeGreaterThan(0);
    expect(table).toHaveTextContent("authority_stale");
    await user.click(screen.getByRole("button", { name: "Load more" }));
    expect(await within(table).findByText(third.runtime_id)).toBeVisible();
    expect(apiMocks.fetchPaperRuntimes).toHaveBeenNthCalledWith(2, { limit: 25, cursor: runtimeRaw.cursor });

    await user.type(screen.getByLabelText("Account ID"), "account-filter");
    await user.type(screen.getByLabelText("Replay ID"), "replay-filter");
    await user.type(screen.getByLabelText("Trading session ID"), "session-filter");
    await user.selectOptions(screen.getByLabelText("Desired state"), "stopped");
    await user.selectOptions(screen.getByLabelText("Observed state"), "blocked");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => expect(apiMocks.fetchPaperRuntimes).toHaveBeenNthCalledWith(3, {
      account_id: "account-filter", replay_id: "replay-filter", trading_session_id: "session-filter", desired_state: "stopped", observed_state: "blocked", limit: 25,
    }));
    expect(screen.queryByText(third.runtime_id)).not.toBeInTheDocument();
  });
});

describe("Paper Runtime create", () => {
  it("offers only backend nonterminal Orders and preserves exact defaults and binding facts", async () => {
    const user = userEvent.setup();
    const terminal = { ...executionOrderView, state: { ...executionOrderView.state, terminal: true, status: "filled" as const } };
    apiMocks.fetchPaperExecutionOrders.mockReturnValue(result({ schema_version: 1, items: [terminal, executionOrderView], next_cursor: null }));
    render(<PaperRuntimeCreateView />);
    expect(await screen.findByDisplayValue("founder-paper-runtime")).toBeVisible();
    expect(screen.getByDisplayValue("durable-runtime-v1")).toBeVisible();
    expect(screen.getByDisplayValue("1")).toBeVisible();
    expect(screen.getByDisplayValue("founder")).toBeVisible();
    expect(screen.getAllByText("Terminal — inspection only")).toHaveLength(1);
    expect(screen.getAllByRole("radio")).toHaveLength(1);
    await user.click(screen.getByRole("radio"));
    await user.click(screen.getByRole("button", { name: "Create runtime" }));
    await waitFor(() => expect(apiMocks.createPaperRuntime).toHaveBeenCalledTimes(1));
    expect(apiMocks.createPaperRuntime.mock.calls[0][0]).toEqual({
      execution_order_id: executionOrderView.order.execution_order_id,
      execution_order_digest: executionOrderView.order.execution_order_digest,
      logical_actor: "founder-paper-runtime",
      runtime_policy_id: "durable-runtime-v1",
      runtime_policy_version: 1,
      actor: "founder",
    });
    expect(apiMocks.createPaperRuntime.mock.calls[0][1]).toMatch(/^s224-create-/);
    expect(await screen.findByText(/was not auto-Started/)).toBeVisible();
    expect(apiMocks.startPaperRuntime).not.toHaveBeenCalled();
    expect(apiMocks.stepPaperExecutionOrder).not.toHaveBeenCalled();
  });

  it("reuses one key for exact retry, rotates on material change, and preserves the refused draft", async () => {
    const user = userEvent.setup();
    apiMocks.createPaperRuntime
      .mockRejectedValueOnce(new ApiClientError({ status: 409, code: "paper_runtime_operation_conflict", publicMessage: "Order became terminal.", requestId: "conflict" }))
      .mockResolvedValueOnce({ data: paperRuntimeCommand, requestId: runtimeRaw.requestId })
      .mockResolvedValueOnce({ data: paperRuntimeCommand, requestId: runtimeRaw.requestId });
    render(<PaperRuntimeCreateView />);
    await user.click(await screen.findByRole("radio"));
    await user.click(screen.getByRole("button", { name: "Create runtime" }));
    expect(await screen.findByText("Order became terminal.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry exact request" }));
    await waitFor(() => expect(apiMocks.createPaperRuntime).toHaveBeenCalledTimes(2));
    expect(apiMocks.createPaperRuntime.mock.calls[1][1]).toBe(apiMocks.createPaperRuntime.mock.calls[0][1]);
    expect(screen.getByDisplayValue("founder-paper-runtime")).toBeVisible();
    await user.type(screen.getByDisplayValue("founder"), "-changed");
    await user.click(screen.getByRole("button", { name: "Create runtime" }));
    await waitFor(() => expect(apiMocks.createPaperRuntime).toHaveBeenCalledTimes(3));
    expect(apiMocks.createPaperRuntime.mock.calls[2][1]).not.toBe(apiMocks.createPaperRuntime.mock.calls[1][1]);
  });
});

describe("Paper Runtime detail", () => {
  it("preserves successful sections on partial read failure and Refresh performs GETs only", async () => {
    const user = userEvent.setup();
    apiMocks.fetchPaperRuntimeHealth.mockRejectedValueOnce(new ApiClientError({ status: 503, code: "paper_runtime_storage_busy", publicMessage: "Health busy.", requestId: "health-busy" }));
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    expect(await screen.findByRole("heading", { name: "Durable binding" })).toBeVisible();
    expect(await screen.findByText("Health busy.")).toBeVisible();
    expect(screen.getByText(paperRuntimeReconciliation.status)).toBeVisible();
    expect(screen.getByText(paperRuntimeAudit.items[0].event_id)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(apiMocks.fetchPaperRuntimeDetail).toHaveBeenCalledTimes(2));
    expect(apiMocks.startPaperRuntime).not.toHaveBeenCalled();
    expect(apiMocks.stopPaperRuntime).not.toHaveBeenCalled();
    expect(apiMocks.resumePaperRuntime).not.toHaveBeenCalled();
    expect(apiMocks.recoverPaperRuntime).not.toHaveBeenCalled();
  });

  it("submits exact loaded Start authority once, retains its key on 409, and never silently retries", async () => {
    const user = userEvent.setup();
    const pendingStart = deferred<Awaited<ReturnType<typeof result<typeof paperRuntimeCommand>>>>();
    apiMocks.startPaperRuntime.mockReturnValue(pendingStart.promise);
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    const start = await screen.findByRole("button", { name: "Start" });
    await user.click(start);
    await user.click(start);
    await waitFor(() => expect(apiMocks.startPaperRuntime).toHaveBeenCalledTimes(1));
    expect(apiMocks.startPaperRuntime.mock.calls[0].slice(0, 3)).toEqual([
      runtimeRaw.runtimeId,
      { runtime_binding_digest: runtimeRaw.runtimeDigest, expected_runtime_version: 0, actor: "founder" },
      expect.stringMatching(/^s224-control-/),
    ]);
    const initialReads = apiMocks.fetchPaperRuntimeDetail.mock.calls.length;
    pendingStart.reject(new ApiClientError({ status: 409, code: "paper_runtime_version_conflict", publicMessage: "Loaded row is stale.", requestId: "stale" }));
    expect(await screen.findByText("Loaded row is stale.")).toBeVisible();
    expect(apiMocks.fetchPaperRuntimeDetail).toHaveBeenCalledTimes(initialReads);
    apiMocks.startPaperRuntime.mockRejectedValueOnce(new ApiClientError({ status: 409, code: "paper_runtime_version_conflict", publicMessage: "Loaded row is stale.", requestId: "stale" }));
    await user.click(screen.getByRole("button", { name: "Retry exact request" }));
    await waitFor(() => expect(apiMocks.startPaperRuntime).toHaveBeenCalledTimes(2));
    expect(apiMocks.startPaperRuntime.mock.calls[1][2]).toBe(apiMocks.startPaperRuntime.mock.calls[0][2]);
  });

  it("uses the returned command snapshot before reads and ignores an older in-flight Refresh", async () => {
    const user = userEvent.setup();
    const oldRefresh = deferred<{ data: PaperRuntimeResponse; requestId: string }>();
    const returned = { ...paperRuntime, desired_state: "running" as const, row_version: 1, updated_at: "2026-08-28T01:05:00Z" };
    const returnedCommand = { ...paperRuntimeCommand, runtime: returned };
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    const start = await screen.findByRole("button", { name: "Start" });
    apiMocks.fetchPaperRuntimeDetail.mockReturnValueOnce(oldRefresh.promise);
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    apiMocks.startPaperRuntime.mockReturnValueOnce(result(returnedCommand));
    await user.click(start);
    expect(await screen.findByRole("button", { name: "Stop" })).toBeVisible();
    expect(screen.getByText(/Acceptance is not proof/)).toBeVisible();
    oldRefresh.resolve({ data: paperRuntime, requestId: runtimeRaw.requestId });
    await waitFor(() => expect(screen.getByRole("button", { name: "Stop" })).toBeVisible());
    expect(screen.queryByRole("button", { name: "Start" })).not.toBeInTheDocument();
  });

  it.each([
    [{ desired_state: "stopped", observed_state: "ready" }, "Start"],
    [{ desired_state: "running", observed_state: "running" }, "Stop"],
    [{ desired_state: "stopped", observed_state: "stopped" }, "Resume"],
  ] as const)("shows exact lifecycle control for %o", async (overrides, label) => {
    apiMocks.fetchPaperRuntimeDetail.mockReturnValue(result({ ...paperRuntime, ...overrides }));
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    expect(await screen.findByRole("button", { name: label })).toBeVisible();
  });

  it("labels Web recover as Request recovery and suppresses all controls for blocked runtime", async () => {
    apiMocks.fetchPaperRuntimeDetail.mockReturnValue(result({ ...paperRuntime, desired_state: "running", observed_state: "running" }));
    apiMocks.fetchPaperRuntimeHealth.mockReturnValue(result({ ...paperRuntimeHealth, desired_state: "running", observed_state: "running", lease_status: "expired" }));
    const { unmount } = render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    expect(await screen.findByRole("button", { name: "Request recovery" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Recover" })).not.toBeInTheDocument();
    unmount();
    apiMocks.fetchPaperRuntimeDetail.mockReturnValue(result({ ...paperRuntime, observed_state: "blocked", block_reason_code: "authority_corrupt" }));
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />);
    expect(await screen.findByText(/inspection and Refresh only/)).toBeVisible();
    expect(screen.queryByRole("button", { name: /^(Start|Stop|Resume|Request recovery)$/ })).not.toBeInTheDocument();
  });

  it("renders the same exact runtime facts in Simplified Chinese", async () => {
    render(<PaperRuntimeDetailView runtimeId={runtimeRaw.runtimeId} />, { locale: "zh-CN" });
    expect(await screen.findByRole("heading", { name: "持久化绑定" })).toBeVisible();
    expect(screen.getAllByText(runtimeRaw.runtimeId).length).toBeGreaterThan(0);
    expect(screen.getByText(/启动和继续本身不会执行交易/)).toBeVisible();
  });
});

describe("Sprint 224 browser authority boundary", () => {
  it("contains no polling, raw JSON, Step, runner, lease, M31, or M32 mutation surface", () => {
    const sources = ["paper-runtime-list-view.tsx", "paper-runtime-create-view.tsx", "paper-runtime-detail-view.tsx"]
      .map((file) => readFileSync(`src/components/${file}`, "utf8")).join("\n");
    expect(sources).not.toMatch(/setInterval|JSON\.stringify\([^)]*,\s*null|stepPaperExecutionOrder|runPaperRuntime|claimPaperRuntime|renewPaperRuntime|releasePaperRuntime|takeOverPaperRuntime|postPaperAccount|advanceReplay|resumeReplay|pauseReplay/);
    expect(sources).not.toMatch(/\b(fetch|axios)\s*\(/);
  });

  it("keeps all three routes separate from the existing Paper Execution workspace", () => {
    for (const path of ["src/app/paper-runtimes/page.tsx", "src/app/paper-runtimes/new/page.tsx", "src/app/paper-runtimes/[runtimeId]/page.tsx"]) {
      expect(readFileSync(path, "utf8")).toContain("<WorkspaceShell>");
    }
    expect(readFileSync("src/app/paper-execution/page.tsx", "utf8")).toContain("<PaperExecutionWorkspace />");
  });
});
