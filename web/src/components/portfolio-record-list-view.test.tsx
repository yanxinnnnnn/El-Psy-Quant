import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PortfolioRecordListView } from "./portfolio-record-list-view";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "portfolio-list-request" },
  });
}

const availableJob = {
  job_id: "available / job",
  run_id: "run-available",
  status: "succeeded",
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T11:00:00Z",
  attempt_count: 1,
  latest_attempt: {
    attempt_id: "attempt-1",
    attempt_number: 1,
    status: "succeeded",
    started_timestamp: "2026-07-15T10:00:00Z",
    completed_timestamp: "2026-07-15T11:00:00Z",
    error_code: null,
  },
  result_available: true,
  result_url: "/must-not-be-followed",
};

const unavailableJob = {
  ...availableJob,
  job_id: "unavailable job",
  run_id: "run-unavailable",
  result_available: false,
  result_url: null,
};

describe("PortfolioRecordListView", () => {
  it("uses only the fixed succeeded filter and bounded limit, then refreshes manually", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioRecordListView />);
    await screen.findByRole("heading", { name: "No succeeded paper jobs" });
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/paper-jobs?status=succeeded&limit=50",
    );
    await user.selectOptions(screen.getByLabelText("Limit"), "200");
    expect(fetcher).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Apply limit" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    expect(fetcher.mock.calls[1][0]).toBe(
      "/api/backend/api/v1/paper-jobs?status=succeeded&limit=200",
    );
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
    expect(fetcher.mock.calls.every(([url]) => String(url).includes("status=succeeded"))).toBe(true);
  });

  it("preserves API order and exposes results only from backend availability", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([unavailableJob, availableJob]));
    vi.stubGlobal("fetch", fetcher);
    render(<PortfolioRecordListView />);
    await screen.findByRole("heading", { name: "run-unavailable" });
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual([
      "run-unavailable",
      "run-available",
    ]);
    const unavailableCard = screen.getByRole("heading", { name: "run-unavailable" }).closest("li");
    const availableCard = screen.getByRole("heading", { name: "run-available" }).closest("li");
    expect(unavailableCard).not.toBeNull();
    expect(availableCard).not.toBeNull();
    expect(within(unavailableCard as HTMLElement).queryByRole("link", { name: /Inspect result/ })).not.toBeInTheDocument();
    expect(within(unavailableCard as HTMLElement).getByText(/no backend-owned result available/)).toBeVisible();
    expect(within(availableCard as HTMLElement).getByRole("link", { name: "Inspect result for run-available" })).toHaveAttribute(
      "href",
      "/portfolio-records/available%20%2F%20job",
    );
    expect(within(availableCard as HTMLElement).getByRole("link", { name: "Open paper job available / job" })).toHaveAttribute(
      "href",
      "/paper-jobs/available%20%2F%20job",
    );
    expect(screen.queryByText("/must-not-be-followed")).not.toBeInTheDocument();
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/result"))).toHaveLength(0);
  });

  it.each([
    ["product_database_unavailable", "Product database unavailable"],
    ["internal_server_error", "Portfolio records unavailable"],
  ])("renders bounded %s with request ID and manual retry", async (code, title) => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response({ error: { code, message: "Safe list failure" }, request_id: "body" }, 503))
      .mockResolvedValueOnce(response([]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioRecordListView />);
    expect(await screen.findByRole("heading", { name: title })).toBeVisible();
    expect(screen.getByText("Request portfolio-list-request")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "No succeeded paper jobs" })).toBeVisible();
  });

  it("localizes Portfolio Records while preserving job order, raw status, IDs, and UTC timestamps", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(response([unavailableJob, availableJob])),
    );

    render(<PortfolioRecordListView />, { locale: "zh-CN" });

    expect(screen.getByRole("heading", { name: "模拟结果可用性" })).toBeVisible();
    await screen.findByRole("heading", { name: "run-unavailable" });
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual([
      "run-unavailable",
      "run-available",
    ]);
    const availableCard = screen.getByRole("heading", { name: "run-available" }).closest("li");
    expect(availableCard).not.toBeNull();
    expect(within(availableCard as HTMLElement).getByText("available / job")).toBeVisible();
    expect(within(availableCard as HTMLElement).getByText("succeeded")).toBeVisible();
    expect(within(availableCard as HTMLElement).getByText("2026-07-15T10:00:00Z")).toBeVisible();
    expect(within(availableCard as HTMLElement).getByRole("link", { name: "检查 run-available 的结果" })).toHaveAttribute(
      "href",
      "/portfolio-records/available%20%2F%20job",
    );
  });
});
