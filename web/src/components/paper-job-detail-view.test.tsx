import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperJobDetailView } from "./paper-job-detail-view";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "detail-request" },
  });
}

const jobId = "11111111-1111-4111-8111-111111111111";
const baseJob = {
  job_id: jobId,
  run_id: "run-155",
  status: "queued",
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T10:00:00Z",
  attempt_count: 0,
  latest_attempt: null,
  result_available: false,
  result_url: null,
};

function initialFetcher(job: unknown = baseJob, attempts: unknown = []) {
  return vi.fn<typeof fetch>().mockImplementation((input) => {
    const url = String(input);
    return Promise.resolve(response(url.endsWith("/attempts") ? attempts : job));
  });
}

describe("PaperJobDetailView", () => {
  it.each([
    ["queued", ["Run", "Cancel"]],
    ["running", ["Recover"]],
    ["failed", ["Retry"]],
    ["succeeded", []],
    ["canceled", []],
  ])("shows only status-dependent controls for %s", async (status, expected) => {
    const fetcher = initialFetcher({ ...baseJob, status });
    vi.stubGlobal("fetch", fetcher);
    render(<PaperJobDetailView jobId={jobId} />);
    await screen.findByRole("heading", { name: "run-155" });
    for (const action of ["Run", "Cancel", "Recover", "Retry"]) {
      const button = screen.queryByRole("button", { name: action });
      if (expected.includes(action)) expect(button).toBeVisible();
      else expect(button).not.toBeInTheDocument();
    }
  });

  it("preserves attempt order and nullable values independently from job detail", async () => {
    const attempts = [
      { attempt_id: "a-first", attempt_number: 1, status: "interrupted", started_timestamp: "2026-07-15T10:00:00Z", completed_timestamp: null, error_code: "interrupted_without_output" },
      { attempt_id: "a-second", attempt_number: 2, status: "succeeded", started_timestamp: "2026-07-15T11:00:00Z", completed_timestamp: "2026-07-15T11:01:00Z", error_code: null },
    ];
    const fetcher = initialFetcher({ ...baseJob, status: "succeeded", attempt_count: 2, latest_attempt: attempts[1], result_available: true, result_url: `/api/v1/paper-jobs/${jobId}/result` }, attempts);
    vi.stubGlobal("fetch", fetcher);
    render(<PaperJobDetailView jobId={jobId} />);
    const region = await screen.findByRole("region", { name: "Attempts in exact API order" });
    expect(region).toHaveAttribute("tabindex", "0");
    const table = await screen.findByRole("table", { name: "Attempts in exact API order" });
    expect(within(region).getByRole("table", { name: "Attempts in exact API order" })).toBe(table);
    expect(table.querySelector("caption")).toHaveTextContent("Attempts in exact API order");
    expect(within(table).getAllByRole("columnheader").map((cell) => cell.textContent)).toEqual([
      "Attempt ID",
      "Number",
      "Status",
      "Started",
      "Completed",
      "Error code",
    ]);
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows.map((row) => within(row).getByRole("rowheader").textContent)).toEqual(["a-first", "a-second"]);
    expect(rows[0]).toHaveTextContent("a-first");
    expect(rows[1]).toHaveTextContent("a-second");
    const interruptedBadge = within(rows[0]).getByText("Interrupted").closest(".status-badge");
    expect(interruptedBadge).toHaveClass("status-badge--warning");
    expect(within(interruptedBadge as HTMLElement).getByText("interrupted", { selector: "code" })).toBeVisible();
    expect(within(rows[1]).getByText("succeeded", { selector: "code" })).toBeVisible();
    expect(rows[0]).toHaveTextContent("Not available");
    expect(rows[0]).toHaveTextContent("Interrupted without output (interrupted_without_output)");
    expect(screen.getByRole("link", { name: "Inspect portfolio record for run-155" })).toHaveAttribute(
      "href",
      `/portfolio-records/${jobId}`,
    );
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/result"))).toHaveLength(0);
  });

  it("uses the localized Simplified Chinese caption and interrupted attempt label", async () => {
    const interruptedAttempt = {
      attempt_id: "attempt-interrupted",
      attempt_number: 1,
      status: "interrupted",
      started_timestamp: "2026-07-15T10:00:00Z",
      completed_timestamp: null,
      error_code: "interrupted_without_output",
    };
    vi.stubGlobal("fetch", initialFetcher({
      ...baseJob,
      status: "failed",
      attempt_count: 1,
      latest_attempt: interruptedAttempt,
    }, [interruptedAttempt]));

    render(<PaperJobDetailView jobId={jobId} />, { locale: "zh-CN" });

    const region = await screen.findByRole("region", { name: "按准确 API 顺序排列的尝试记录" });
    expect(region).toHaveAttribute("tabindex", "0");
    const badge = within(region).getByText("已中断").closest(".status-badge");
    expect(badge).toHaveClass("status-badge--warning");
    expect(within(badge as HTMLElement).getByText("interrupted", { selector: "code" })).toBeVisible();
  });

  it("shows no result link when backend-owned availability is false", async () => {
    const fetcher = initialFetcher({
      ...baseJob,
      status: "succeeded",
      result_available: false,
      result_url: null,
    });
    vi.stubGlobal("fetch", fetcher);
    render(<PaperJobDetailView jobId={jobId} />);
    await screen.findByRole("heading", { name: "run-155" });
    expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /Inspect portfolio record/ })).not.toBeInTheDocument();
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/result"))).toHaveLength(0);
  });

  it("renders a bounded not-found state without retry", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input) => Promise.resolve(
      response(String(input).endsWith("/attempts") ? [] : { error: { code: "paper_job_not_found", message: "Paper job was not found" }, request_id: "body" }, String(input).endsWith("/attempts") ? 200 : 404),
    ));
    vi.stubGlobal("fetch", fetcher);
    render(<PaperJobDetailView jobId={jobId} />);
    expect(await screen.findByRole("heading", { name: "Paper job not found" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Return to paper jobs" })).toHaveAttribute("href", "/paper-jobs");
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("locks every mutation after accepted Run until Refresh reloads detail and attempts", async () => {
    const runningAttempt = {
      attempt_id: "attempt-running",
      attempt_number: 1,
      status: "running",
      started_timestamp: "2026-07-15T10:01:00Z",
      completed_timestamp: null,
      error_code: null,
    };
    const runningJob = {
      ...baseJob,
      status: "running",
      updated_timestamp: "2026-07-15T10:01:00Z",
      attempt_count: 1,
      latest_attempt: runningAttempt,
    };
    let detailReads = 0;
    let attemptsReads = 0;
    let resolveRun: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) {
        attemptsReads += 1;
        return Promise.resolve(response(attemptsReads === 1 ? [] : [runningAttempt]));
      }
      if (init?.method === "POST") {
        return new Promise((resolve) => { resolveRun = resolve; });
      }
      detailReads += 1;
      return Promise.resolve(response(detailReads === 1 ? baseJob : runningJob));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);
    await screen.findByRole("button", { name: "Run" });
    await user.click(screen.getByRole("button", { name: "Run" }));
    expect(screen.getByRole("heading", { name: "Confirm Run for run-155" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Confirm Run" }));
    const pending = await screen.findByRole("button", { name: "Run pending…" });
    expect(pending).toBeDisabled();
    await user.click(pending);
    expect(fetcher.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
    resolveRun?.(response(runningJob, 202));
    expect(
      await screen.findByText(/The job was synchronously claimed as running/),
    ).toBeVisible();
    expect(screen.getByText(/attempt #1 \(attempt-running\)/)).toBeVisible();
    const claimedAttempts = await screen.findByRole("table", {
      name: "Attempts in exact API order",
    });
    expect(within(claimedAttempts).getAllByRole("row")).toHaveLength(2);
    expect(
      within(claimedAttempts).getByRole("rowheader", {
        name: "attempt-running",
      }),
    ).toBeVisible();
    expect(screen.queryByText("No attempts exist.")).not.toBeInTheDocument();
    expect(fetcher.mock.calls[2][0]).toBe(`/api/backend/api/v1/paper-jobs/${jobId}/run`);
    expect(screen.getByText(/Displayed job state is stale/)).toBeVisible();
    expect(screen.getByText(/Refresh status is required/)).toBeVisible();
    for (const action of ["Run", "Cancel", "Retry", "Recover"]) {
      expect(screen.queryByRole("button", { name: action })).not.toBeInTheDocument();
    }
    expect(detailReads).toBe(1);
    expect(attemptsReads).toBe(1);
    expect(fetcher.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Refresh status" })).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Refresh status" }));

    expect(await screen.findByRole("button", { name: "Recover" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Run" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();
    expect(detailReads).toBe(2);
    expect(attemptsReads).toBe(2);
    expect(fetcher.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
    const refreshedAttempts = screen.getByRole("table", {
      name: "Attempts in exact API order",
    });
    expect(within(refreshedAttempts).getAllByRole("row")).toHaveLength(2);
    expect(
      within(refreshedAttempts).getAllByRole("rowheader", {
        name: "attempt-running",
      }),
    ).toHaveLength(1);
  });

  it("Retry returns queued without calling Run", async () => {
    const failedAttempt = {
      attempt_id: "attempt-failed",
      attempt_number: 1,
      status: "failed",
      started_timestamp: "2026-07-15T11:00:00Z",
      completed_timestamp: "2026-07-15T11:01:00Z",
      error_code: "workflow_validation_failed",
    };
    const failed = {
      ...baseJob,
      status: "failed",
      attempt_count: 1,
      latest_attempt: failedAttempt,
    };
    const queued = {
      ...failed,
      status: "queued",
      updated_timestamp: "2026-07-15T12:00:00Z",
    };
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) return Promise.resolve(response([failedAttempt]));
      if (init?.method === "POST") return Promise.resolve(response(queued));
      return Promise.resolve(response(failed));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);
    await user.click(await screen.findByRole("button", { name: "Retry" }));
    await user.click(screen.getByRole("button", { name: "Confirm Retry" }));
    expect(await screen.findByText(/returned to queued/)).toBeVisible();
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/run"))).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Run" })).toBeVisible();
    const attempts = screen.getByRole("table", {
      name: "Attempts in exact API order",
    });
    expect(within(attempts).getAllByRole("row")).toHaveLength(2);
    expect(
      within(attempts).getByRole("rowheader", { name: "attempt-failed" }),
    ).toBeVisible();
  });

  it("Recover reconciles the terminal attempt in both summary and audit", async () => {
    const runningAttempt = {
      attempt_id: "attempt-recovered",
      attempt_number: 1,
      status: "running",
      started_timestamp: "2026-07-15T10:00:00Z",
      completed_timestamp: null,
      error_code: null,
    };
    const interruptedAttempt = {
      ...runningAttempt,
      status: "interrupted",
      completed_timestamp: "2026-07-15T10:05:00Z",
      error_code: "interrupted_without_output",
    };
    const running = {
      ...baseJob,
      status: "running",
      attempt_count: 1,
      latest_attempt: runningAttempt,
    };
    const requeued = {
      ...running,
      status: "queued",
      updated_timestamp: "2026-07-15T10:05:00Z",
      latest_attempt: interruptedAttempt,
    };
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) {
        return Promise.resolve(response([runningAttempt]));
      }
      if (init?.method === "POST") {
        return Promise.resolve(
          response({ recovery_outcome: "requeued", job: requeued }),
        );
      }
      return Promise.resolve(response(running));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);

    await user.click(await screen.findByRole("button", { name: "Recover" }));
    await user.type(
      screen.getByLabelText("Stale before (exact UTC)"),
      "2026-07-15T10:00:00Z",
    );
    await user.click(screen.getByRole("button", { name: "Confirm Recover" }));

    expect(await screen.findByText(/Recovery outcome: requeued/)).toBeVisible();
    const attempts = screen.getByRole("table", {
      name: "Attempts in exact API order",
    });
    expect(within(attempts).getAllByRole("row")).toHaveLength(2);
    const row = within(attempts)
      .getByRole("rowheader", { name: "attempt-recovered" })
      .closest("tr");
    expect(row).not.toBeNull();
    expect(within(row as HTMLElement).getByText("interrupted", {
      selector: "code",
    })).toBeVisible();
    expect(within(row as HTMLElement).queryByText("running", {
      selector: "code",
    })).not.toBeInTheDocument();
    expect(screen.getAllByText("interrupted", { selector: "code" }).length).toBeGreaterThanOrEqual(2);
  });

  it("Recover rejects incompatible UTC input then sends the exact Founder-supplied valid value", async () => {
    const running = { ...baseJob, status: "running" };
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) return Promise.resolve(response([]));
      if (init?.method === "POST") {
        return Promise.resolve(
          response({ recovery_outcome: "requeued", job: running }),
        );
      }
      return Promise.resolve(response(running));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);
    await user.click(await screen.findByRole("button", { name: "Recover" }));
    await user.type(screen.getByLabelText("Stale before (exact UTC)"), "2026-07-15T10:00:00");
    await user.click(screen.getByRole("button", { name: "Confirm Recover" }));
    expect(await screen.findByText(/Enter exact UTC/)).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(2);
    await user.clear(screen.getByLabelText("Stale before (exact UTC)"));
    await user.type(screen.getByLabelText("Stale before (exact UTC)"), "2026-02-30T10:00:00Z");
    await user.click(screen.getByRole("button", { name: "Confirm Recover" }));
    expect(fetcher).toHaveBeenCalledTimes(2);
    await user.clear(screen.getByLabelText("Stale before (exact UTC)"));
    await user.type(screen.getByLabelText("Stale before (exact UTC)"), "2026-07-15T09:59:59Z");
    await user.click(screen.getByRole("button", { name: "Confirm Recover" }));
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(
      within(
        screen.getByRole("group", { name: "Confirm Recover for run-155" }),
      ).getByText(baseJob.updated_timestamp, { selector: "code" }),
    ).toBeVisible();
    await user.clear(screen.getByLabelText("Stale before (exact UTC)"));
    await user.type(screen.getByLabelText("Stale before (exact UTC)"), "2026-07-15T10:00:00.123+00:00");
    await user.click(screen.getByRole("button", { name: "Confirm Recover" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
    expect(JSON.parse(String((fetcher.mock.calls[2][1] as RequestInit).body))).toEqual({ stale_before: "2026-07-15T10:00:00.123+00:00" });
    expect(await screen.findByText(/Recovery outcome: requeued/)).toBeVisible();
  });

  it("keeps loaded job data visible when attempts and mutation requests fail", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) return Promise.resolve(response({ error: { code: "product_database_unavailable", message: "Attempts unavailable" }, request_id: "body" }, 503));
      if (init?.method === "POST") return Promise.resolve(response({ error: { code: "paper_job_state_conflict", message: "State conflict" }, request_id: "body" }, 409));
      return Promise.resolve(response(baseJob));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);
    expect(await screen.findByRole("heading", { name: "run-155" })).toBeVisible();
    expect(await screen.findByText("Attempts unavailable")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Run" }));
    await user.click(screen.getByRole("button", { name: "Confirm Run" }));
    expect(await screen.findByText("Paper job state changed")).toBeVisible();
    expect(screen.getByText(/Refresh status manually/)).toBeVisible();
    expect(screen.getByRole("heading", { name: "run-155" })).toBeVisible();
    expect(screen.getAllByText("Request detail-request").length).toBeGreaterThanOrEqual(2);
  });

  it("preserves settled job and attempt evidence when a mutation fails", async () => {
    const priorAttempt = {
      attempt_id: "attempt-prior",
      attempt_number: 1,
      status: "interrupted",
      started_timestamp: "2026-07-15T09:00:00Z",
      completed_timestamp: "2026-07-15T09:05:00Z",
      error_code: "interrupted_without_output",
    };
    const queued = {
      ...baseJob,
      attempt_count: 1,
      latest_attempt: priorAttempt,
    };
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/attempts")) {
        return Promise.resolve(response([priorAttempt]));
      }
      if (init?.method === "POST") {
        return Promise.resolve(
          response({
            error: {
              code: "paper_job_state_conflict",
              message: "State conflict",
            },
            request_id: "body",
          }, 409),
        );
      }
      return Promise.resolve(response(queued));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperJobDetailView jobId={jobId} />);

    await user.click(await screen.findByRole("button", { name: "Run" }));
    await user.click(screen.getByRole("button", { name: "Confirm Run" }));

    expect(await screen.findByText("Paper job state changed")).toBeVisible();
    expect(screen.getByRole("heading", { name: "run-155" })).toBeVisible();
    const attempts = screen.getByRole("table", {
      name: "Attempts in exact API order",
    });
    expect(within(attempts).getAllByRole("row")).toHaveLength(2);
    expect(
      within(attempts).getByRole("rowheader", { name: "attempt-prior" }),
    ).toBeVisible();
    expect(
      screen.getAllByText("queued", { selector: "code" }).length,
    ).toBeGreaterThanOrEqual(1);
  });
});
