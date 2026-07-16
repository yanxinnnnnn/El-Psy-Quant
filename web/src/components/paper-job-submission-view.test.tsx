import { fireEvent, render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperJobSubmissionView } from "./paper-job-submission-view";
import type { DemoWorkspaceDescriptorResponse } from "@/lib/api-client";

const demoApiMock = vi.hoisted(() => ({ fetchDemoWorkspace: vi.fn() }));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, fetchDemoWorkspace: demoApiMock.fetchDemoWorkspace };
});

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

afterEach(() => {
  vi.unstubAllGlobals();
  demoApiMock.fetchDemoWorkspace.mockReset();
  push.mockReset();
});

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "submit-request" },
  });
}

const queuedJob = {
  job_id: "11111111-1111-4111-8111-111111111111",
  run_id: "run-155",
  status: "queued",
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T10:00:00Z",
  attempt_count: 0,
  latest_attempt: null,
  result_available: false,
  result_url: null,
};

async function fillBaseFields(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Run ID"), "run-155");
  await user.type(screen.getByLabelText("Created timestamp"), "2026-07-15T10:00:00Z");
  const starting = screen.getByRole("group", { name: "Starting account state" });
  await user.type(within(starting).getByLabelText("Timestamp"), "2026-07-15T10:00:00Z");
  await user.type(within(starting).getByLabelText("Starting cash"), "1000.5");
  await user.type(within(starting).getByLabelText("Current cash"), "1000.5");
  const ending = screen.getByRole("group", { name: "Ending account state" });
  await user.type(within(ending).getByLabelText("Timestamp"), "2026-07-15T11:00:00Z");
  await user.type(within(ending).getByLabelText("Starting cash"), "1000.5");
  await user.type(within(ending).getByLabelText("Current cash"), "900");
}

function setBaseFields() {
  fireEvent.change(screen.getByLabelText("Run ID"), { target: { value: "run-155" } });
  fireEvent.change(screen.getByLabelText("Created timestamp"), { target: { value: "2026-07-15T10:00:00Z" } });
  const starting = screen.getByRole("group", { name: "Starting account state" });
  fireEvent.change(within(starting).getByLabelText("Timestamp"), { target: { value: "2026-07-15T10:00:00Z" } });
  fireEvent.change(within(starting).getByLabelText("Starting cash"), { target: { value: "1000.5" } });
  fireEvent.change(within(starting).getByLabelText("Current cash"), { target: { value: "1000.5" } });
  const ending = screen.getByRole("group", { name: "Ending account state" });
  fireEvent.change(within(ending).getByLabelText("Timestamp"), { target: { value: "2026-07-15T11:00:00Z" } });
  fireEvent.change(within(ending).getByLabelText("Starting cash"), { target: { value: "1000.5" } });
  fireEvent.change(within(ending).getByLabelText("Current cash"), { target: { value: "900" } });
}

describe("PaperJobSubmissionView", () => {
  it("starts blank without fabricated positions, orders, fills, or raw JSON", () => {
    render(<PaperJobSubmissionView />);
    expect(screen.getByLabelText("Run ID")).toHaveValue("");
    expect(screen.getAllByText("No positions added.")).toHaveLength(2);
    expect(screen.getByText("No orders added.")).toBeVisible();
    expect(screen.getByText("No fills added.")).toBeVisible();
    expect(screen.queryByRole("textbox", { name: /json/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit queued job" })).toBeVisible();
    expect(screen.getByRole("group", { name: "Run identity" })).toBeVisible();
    expect(screen.getByRole("group", { name: "Starting account state" })).toBeVisible();
    expect(screen.getByRole("group", { name: "Ending account state" })).toBeVisible();
    expect(screen.getByText(/replay-safe submission identity/)).toBeVisible();
    expect(screen.getAllByText(/explicit UTC timestamp/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Required").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Optional").length).toBeGreaterThan(0);
  });

  it("loads a submission example only from the backend descriptor and never submits it", async () => {
    const paperJobSubmissionExample = {
      idempotency_key: "descriptor-idempotency-key",
      request: {
        run_id: "descriptor-run-id",
        created_timestamp: "2026-01-18T14:00:00Z",
        starting_account_state: {
          timestamp: "2026-01-18T13:55:00Z",
          starting_cash: 50000,
          current_cash: 49900,
          positions: { AAPL: 1 },
        },
        ending_account_state: {
          timestamp: "2026-01-18T14:05:00Z",
          starting_cash: 50000,
          current_cash: 49900,
          positions: { AAPL: 1 },
        },
        orders: [{
          order_id: "descriptor-order",
          timestamp: "2026-01-18T14:01:00Z",
          symbol: "AAPL",
          side: "buy",
          quantity: 1,
          status: "filled",
        }],
        fills: [{
          timestamp: "2026-01-18T14:01:30Z",
          symbol: "AAPL",
          side: "buy",
          quantity: 1,
          price: 100,
          order_id: "descriptor-order",
        }],
      },
    };
    demoApiMock.fetchDemoWorkspace.mockResolvedValue({
      data: { paper_job_submission_example: paperJobSubmissionExample } as unknown as DemoWorkspaceDescriptorResponse,
      requestId: "descriptor-request",
    });
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);

    await user.click(screen.getByRole("button", { name: "Load demo example" }));

    expect(await screen.findByLabelText("Run ID")).toHaveValue("descriptor-run-id");
    expect(screen.getByLabelText(/Idempotency key/)).toHaveValue("descriptor-idempotency-key");
    expect(within(screen.getByRole("group", { name: "Starting account state" })).getByLabelText("Symbol")).toHaveValue("AAPL");
    expect(within(screen.getByRole("group", { name: "Orders" })).getByLabelText("Order ID")).toHaveValue("descriptor-order");
    expect(demoApiMock.fetchDemoWorkspace).toHaveBeenCalledTimes(1);
    expect(fetcher).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it("blocks duplicate position symbols before submission", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    await fillBaseFields(user);
    const starting = screen.getByRole("group", { name: "Starting account state" });
    await user.click(within(starting).getByRole("button", { name: "Add position" }));
    await user.click(within(starting).getByRole("button", { name: "Add position" }));
    const symbols = within(starting).getAllByLabelText("Symbol");
    const quantities = within(starting).getAllByLabelText("Quantity");
    await user.type(symbols[0], "AAPL");
    await user.type(symbols[1], "AAPL");
    await user.type(quantities[0], "1");
    await user.type(quantities[1], "2");
    await user.click(screen.getByRole("button", { name: "Submit queued job" }));
    expect(await screen.findByText("Duplicate position symbols are not allowed in one account state.")).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects whitespace-only starting cash without sending a request", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    setBaseFields();
    const starting = screen.getByRole("group", { name: "Starting account state" });
    fireEvent.change(within(starting).getByLabelText("Starting cash"), { target: { value: "   " } });

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));

    expect(await within(starting).findByText("Enter a finite decimal number.")).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects whitespace-only position quantity without sending a request", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    setBaseFields();
    const starting = screen.getByRole("group", { name: "Starting account state" });
    await user.click(within(starting).getByRole("button", { name: "Add position" }));
    fireEvent.change(within(starting).getByLabelText("Symbol"), { target: { value: "AAPL" } });
    fireEvent.change(within(starting).getByLabelText("Quantity"), { target: { value: " \t " } });

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));

    expect(await within(starting).findByText("Enter a finite decimal number.")).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects whitespace-only order and fill numeric fields without sending a request", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    setBaseFields();
    const orders = screen.getByRole("group", { name: "Orders" });
    await user.click(within(orders).getByRole("button", { name: "Add order" }));
    const orderRow = within(orders).getByText("Order 1").closest("div") as HTMLElement;
    for (const [label, value] of [["Order ID", "order-a"], ["Timestamp", "2026-07-15T10:00:00Z"], ["Symbol", "AAPL"], ["Side", "buy"], ["Status", "submitted"]]) {
      fireEvent.change(within(orderRow).getByLabelText(label), { target: { value } });
    }
    fireEvent.change(within(orderRow).getByLabelText("Quantity"), { target: { value: "   " } });

    const fills = screen.getByRole("group", { name: "Fills" });
    await user.click(within(fills).getByRole("button", { name: "Add fill" }));
    const fillRow = within(fills).getByText("Fill 1").closest("div") as HTMLElement;
    for (const [label, value] of [["Timestamp", "2026-07-15T10:01:00Z"], ["Symbol", "AAPL"], ["Side", "buy"]]) {
      fireEvent.change(within(fillRow).getByLabelText(label), { target: { value } });
    }
    fireEvent.change(within(fillRow).getByLabelText("Quantity"), { target: { value: "\t" } });
    fireEvent.change(within(fillRow).getByLabelText("Price"), { target: { value: " " } });

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));

    expect(await screen.findAllByText("Enter a finite decimal number.")).toHaveLength(3);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("applies the existing backend cash, quantity, and price bounds", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    setBaseFields();
    const starting = screen.getByRole("group", { name: "Starting account state" });
    fireEvent.change(within(starting).getByLabelText("Current cash"), { target: { value: "-1" } });

    const orders = screen.getByRole("group", { name: "Orders" });
    await user.click(within(orders).getByRole("button", { name: "Add order" }));
    const orderRow = within(orders).getByText("Order 1").closest("div") as HTMLElement;
    for (const [label, value] of [["Order ID", "order-a"], ["Timestamp", "2026-07-15T10:00:00Z"], ["Symbol", "AAPL"], ["Side", "buy"], ["Quantity", "0"], ["Status", "submitted"]]) {
      fireEvent.change(within(orderRow).getByLabelText(label), { target: { value } });
    }

    const fills = screen.getByRole("group", { name: "Fills" });
    await user.click(within(fills).getByRole("button", { name: "Add fill" }));
    const fillRow = within(fills).getByText("Fill 1").closest("div") as HTMLElement;
    for (const [label, value] of [["Timestamp", "2026-07-15T10:01:00Z"], ["Symbol", "AAPL"], ["Side", "buy"], ["Quantity", "1"], ["Price", "-0.01"]]) {
      fireEvent.change(within(fillRow).getByLabelText(label), { target: { value } });
    }

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));

    expect(await screen.findAllByText("Enter a finite non-negative decimal number.")).toHaveLength(2);
    expect(screen.getByText("Enter a positive finite decimal number.")).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it.each(["Infinity", "NaN", "0x10", "0b10", "1e3"])("rejects unsupported numeric syntax %s", async (value) => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    setBaseFields();
    const starting = screen.getByRole("group", { name: "Starting account state" });
    fireEvent.change(within(starting).getByLabelText("Starting cash"), { target: { value } });

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));

    expect(await within(starting).findByText("Enter a finite decimal number.")).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("converts finite numbers, preserves row order, sends null fill order ID, and never runs", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(queuedJob));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    await fillBaseFields(user);
    fireEvent.change(within(screen.getByRole("group", { name: "Ending account state" })).getByLabelText("Current cash"), { target: { value: "900.25" } });
    await user.type(screen.getByLabelText(/Idempotency key/), "founder-key-155");

    const orders = screen.getByRole("group", { name: "Orders" });
    await user.click(within(orders).getByRole("button", { name: "Add order" }));
    await user.click(within(orders).getByRole("button", { name: "Add order" }));
    for (const [index, orderId] of ["order-a", "order-b"].entries()) {
      const row = within(orders).getByText(`Order ${index + 1}`).closest("div");
      expect(row).not.toBeNull();
      await user.type(within(row as HTMLElement).getByLabelText("Order ID"), orderId);
      await user.type(within(row as HTMLElement).getByLabelText("Timestamp"), `2026-07-15T10:0${index}:00Z`);
      await user.type(within(row as HTMLElement).getByLabelText("Symbol"), "AAPL");
      await user.type(within(row as HTMLElement).getByLabelText("Side"), "buy");
      await user.type(within(row as HTMLElement).getByLabelText("Quantity"), index === 0 ? "1" : "2");
      await user.type(within(row as HTMLElement).getByLabelText("Status"), "submitted");
    }
    const fills = screen.getByRole("group", { name: "Fills" });
    await user.click(within(fills).getByRole("button", { name: "Add fill" }));
    const fillRow = within(fills).getByText("Fill 1").closest("div");
    expect(fillRow).not.toBeNull();
    await user.type(within(fillRow as HTMLElement).getByLabelText("Timestamp"), "2026-07-15T10:05:00Z");
    await user.type(within(fillRow as HTMLElement).getByLabelText("Symbol"), "AAPL");
    await user.type(within(fillRow as HTMLElement).getByLabelText("Side"), "buy");
    await user.type(within(fillRow as HTMLElement).getByLabelText("Quantity"), ".5");
    await user.type(within(fillRow as HTMLElement).getByLabelText("Price"), "123.45");

    await user.click(screen.getByRole("button", { name: "Submit queued job" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith(`/paper-jobs/${queuedJob.job_id}`));
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher.mock.calls[0][0]).toBe("/api/backend/api/v1/paper-jobs");
    const init = fetcher.mock.calls[0][1] as RequestInit;
    const payload = JSON.parse(String(init.body));
    expect(payload.starting_account_state.starting_cash).toBe(1000.5);
    expect(payload.ending_account_state.current_cash).toBe(900.25);
    expect(payload.orders.map((order: { order_id: string }) => order.order_id)).toEqual(["order-a", "order-b"]);
    expect(payload.orders.map((order: { quantity: number }) => order.quantity)).toEqual([1, 2]);
    expect(payload.fills[0]).toMatchObject({ quantity: 0.5, price: 123.45, order_id: null });
    expect(init.headers).toMatchObject({ "Idempotency-Key": "founder-key-155" });
    expect(String(fetcher.mock.calls[0][0])).not.toContain("/run");
  }, 20_000);

  it("prevents duplicate pending submissions and keeps bounded server errors safe", async () => {
    let resolveFetch: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(() => new Promise((resolve) => { resolveFetch = resolve; }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobSubmissionView />);
    await fillBaseFields(user);
    const submit = screen.getByRole("button", { name: "Submit queued job" });
    await user.click(submit);
    expect(await screen.findByRole("button", { name: "Submitting queued job…" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Submitting queued job…" }));
    expect(fetcher).toHaveBeenCalledTimes(1);
    resolveFetch?.(response({ error: { code: "paper_job_idempotency_conflict", message: "Safe conflict" }, request_id: "body" }, 409));
    expect(await screen.findByText("Idempotency key conflicts with another request")).toBeVisible();
    expect(screen.getByText("Request submit-request")).toBeVisible();
  });
});
