import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperJobListView } from "./paper-job-list-view";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "list-request" },
  });
}

const baseJob = {
  job_id: "11111111-1111-4111-8111-111111111111",
  run_id: "run-first",
  status: "failed",
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T11:00:00Z",
  attempt_count: 2,
  latest_attempt: {
    attempt_id: "22222222-2222-4222-8222-222222222222",
    attempt_number: 2,
    status: "failed",
    started_timestamp: "2026-07-15T10:30:00Z",
    completed_timestamp: "2026-07-15T11:00:00Z",
    error_code: "output_conflict",
  },
  result_available: false,
  result_url: null,
};

describe("PaperJobListView", () => {
  it("uses one loading region then preserves API order and backend attempt/result fields", async () => {
    let resolveFetch: ((response: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(() => new Promise((resolve) => { resolveFetch = resolve; }));
    vi.stubGlobal("fetch", fetcher);
    render(<PaperJobListView />);
    expect(screen.getAllByRole("status")).toHaveLength(1);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    resolveFetch?.(response([baseJob, { ...baseJob, job_id: "33333333-3333-4333-8333-333333333333", run_id: "run-second", status: "succeeded", attempt_count: 3, result_available: true, result_url: "/api/v1/paper-jobs/33333333-3333-4333-8333-333333333333/result" }]));
    await screen.findByRole("heading", { name: "run-first" });
    expect(screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent)).toEqual(["run-first", "run-second"]);
    const first = screen.getByRole("heading", { name: "run-first" }).closest("li");
    expect(first).not.toBeNull();
    expect(within(first as HTMLElement).getByText("#2 failed")).toBeVisible();
    expect(within(first as HTMLElement).getByText("Output conflict (output_conflict)")).toBeVisible();
    expect(within(first as HTMLElement).getByText("No")).toBeVisible();
  });

  it("constructs approved filter queries and refreshes only on explicit clicks", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobListView />);
    await screen.findByRole("heading", { name: "No paper jobs match this filter" });
    expect(fetcher.mock.calls[0][0]).toBe("/api/backend/api/v1/paper-jobs?limit=50");
    await user.selectOptions(screen.getByLabelText("Status"), "running");
    await user.selectOptions(screen.getByLabelText("Limit"), "200");
    expect(fetcher).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    expect(fetcher.mock.calls[1][0]).toBe("/api/backend/api/v1/paper-jobs?status=running&limit=200");
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
  });

  it.each([
    ["product_database_unavailable", "Product database unavailable"],
    ["internal_server_error", "Paper jobs unavailable"],
  ])("renders bounded %s with request ID and manual retry", async (code, title) => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response({ error: { code, message: "Safe list failure" }, request_id: "body-id" }, 503))
      .mockResolvedValueOnce(response([]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobListView />);
    expect(await screen.findByRole("heading", { name: title })).toBeVisible();
    expect(screen.getByText("Request list-request")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "No paper jobs match this filter" })).toBeVisible();
  });
});
