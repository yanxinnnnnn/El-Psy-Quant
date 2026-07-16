import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PaperJobResponse, PaperJobResultResponse } from "@/lib/api-client";
import { paperJobResultFixture } from "@/test/paper-job-result-fixture";
import { ComparisonWorkspace } from "./comparison-workspace";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

afterEach(() => {
  vi.unstubAllGlobals();
  push.mockReset();
});

function response(body: unknown, status = 200, requestId = "comparison-request"): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
  });
}

function job(jobId: string, runId: string, resultAvailable = true): PaperJobResponse {
  return {
    job_id: jobId,
    run_id: runId,
    status: "succeeded",
    submitted_timestamp: "2026-07-15T10:00:00Z",
    updated_timestamp: "2026-07-15T11:00:00Z",
    attempt_count: 1,
    latest_attempt: {
      attempt_id: `attempt-${jobId}`,
      attempt_number: 1,
      status: "succeeded",
      started_timestamp: "2026-07-15T10:00:00Z",
      completed_timestamp: "2026-07-15T11:00:00Z",
      error_code: null,
    },
    result_available: resultAvailable,
    result_url: resultAvailable ? `/must-not-be-followed/${jobId}` : null,
  };
}

function result(jobId: string, runId: string): PaperJobResultResponse {
  const base = structuredClone(paperJobResultFixture);
  return {
    ...base,
    job_id: jobId,
    run_id: runId,
    result_summary: { ...base.result_summary, run_id: runId },
  };
}

function deferred<ResponseValue>() {
  let resolve: ((value: ResponseValue) => void) | undefined;
  const promise = new Promise<ResponseValue>((innerResolve) => { resolve = innerResolve; });
  return { promise, resolve: (value: ResponseValue) => resolve?.(value) };
}

describe("ComparisonWorkspace", () => {
  it("loads only succeeded bounded candidates, preserves API order, and keeps unavailable rows unselectable", async () => {
    const jobs = [job("unavailable", "run-unavailable", false), job("available", "run-available")];
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(jobs));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);

    await screen.findByRole("heading", { name: "run-unavailable" });
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/paper-jobs?status=succeeded&limit=50",
    );
    expect(screen.getAllByRole("heading", { level: 2 }).filter((heading) => heading.textContent?.startsWith("run-")).map((heading) => heading.textContent)).toEqual([
      "run-unavailable",
      "run-available",
    ]);
    expect(screen.getByLabelText("Result unavailable is unavailable and cannot be selected")).toBeDisabled();
    expect(screen.getByText(/backend reports no result available/)).toBeVisible();
    expect(screen.queryByText("/must-not-be-followed/available")).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Limit"), "200");
    await user.click(screen.getByRole("button", { name: "Apply limit" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    expect(fetcher.mock.calls[1][0]).toBe(
      "/api/backend/api/v1/paper-jobs?status=succeeded&limit=200",
    );
    await user.click(screen.getByRole("button", { name: "Refresh candidates" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
  });

  it("applies 2–4 selections in visible API order only after the explicit action", async () => {
    const jobs = [job("first / job", "run-first"), job("second?job", "run-second"), job("third", "run-third")];
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(response(jobs)));
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-first" });

    await user.click(screen.getByLabelText("Select result second?job"));
    expect(push).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Select at least two");
    expect(push).not.toHaveBeenCalled();

    await user.click(screen.getByLabelText("Select result first / job"));
    expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(push).toHaveBeenCalledWith(
      "/comparisons?job_id=first%20%2F%20job&job_id=second%3Fjob",
    );
  });

  it("prevents selecting a fifth candidate while keeping selected controls removable", async () => {
    const jobs = [1, 2, 3, 4, 5].map((value) => job(`job-${value}`, `run-${value}`));
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(response(jobs)));
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-1" });
    for (const value of [1, 2, 3, 4]) {
      await user.click(screen.getByLabelText(`Select result job-${value}`));
    }
    expect(screen.getByLabelText(/Result job-5 cannot be selected because four/)).toBeDisabled();
    expect(screen.getByLabelText("Select result job-1")).not.toBeDisabled();
  });

  it("reconciles removed selections after refresh and applies exactly the latest visible API order", async () => {
    const initial = ["a", "b", "c", "d", "e"].map((id) => job(id, `run-${id}`));
    const refreshed = ["c", "a", "d", "e", "new"].map((id) => job(id, `run-${id}`));
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(initial))
      .mockResolvedValueOnce(response(refreshed));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-a" });
    for (const id of ["a", "b", "c"]) {
      await user.click(screen.getByLabelText(`Select result ${id}`));
    }
    expect(screen.getByText("Selected 3 of 4 maximum")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Refresh candidates" }));
    await screen.findByRole("heading", { name: "run-new" });
    expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible();
    expect(screen.getByLabelText("Select result c")).toBeChecked();
    expect(screen.getByLabelText("Select result a")).toBeChecked();
    expect(screen.getByLabelText("Select result new")).not.toBeChecked();

    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(push).toHaveBeenLastCalledWith("/comparisons?job_id=c&job_id=a");

    await user.click(screen.getByLabelText("Select result d"));
    await user.click(screen.getByLabelText("Select result e"));
    expect(screen.getByText("Selected 4 of 4 maximum")).toBeVisible();
    expect(screen.getByLabelText(/Result new cannot be selected because four/)).toBeDisabled();
  });

  it("removes a selected job whose latest backend representation becomes unavailable", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response([job("a", "run-a"), job("b", "run-b"), job("c", "run-c")]))
      .mockResolvedValueOnce(response([job("c", "run-c"), job("b", "run-b", false), job("a", "run-a")]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-a" });
    await user.click(screen.getByLabelText("Select result a"));
    await user.click(screen.getByLabelText("Select result b"));

    await user.click(screen.getByRole("button", { name: "Refresh candidates" }));
    await waitFor(() => expect(screen.getByText("Selected 1 of 4 maximum")).toBeVisible());
    expect(screen.getByLabelText("Result b is unavailable and cannot be selected")).not.toBeChecked();
    await user.click(screen.getByLabelText("Select result c"));
    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(push).toHaveBeenLastCalledWith("/comparisons?job_id=c&job_id=a");
  });

  it("reconciles selections when a bounded limit change removes candidates", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response([job("a", "run-a"), job("b", "run-b"), job("c", "run-c")]))
      .mockResolvedValueOnce(response([job("c", "run-c"), job("a", "run-a")]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-a" });
    for (const id of ["a", "b", "c"]) {
      await user.click(screen.getByLabelText(`Select result ${id}`));
    }

    await user.selectOptions(screen.getByLabelText("Limit"), "25");
    await user.click(screen.getByRole("button", { name: "Apply limit" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible());
    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(push).toHaveBeenLastCalledWith("/comparisons?job_id=c&job_id=a");
  });

  it("preserves selection through loading and failed refresh until a later success reconciles it", async () => {
    const failedRefresh = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response([job("a", "run-a"), job("b", "run-b")]))
      .mockImplementationOnce(() => failedRefresh.promise)
      .mockResolvedValueOnce(response([job("b", "run-b"), job("a", "run-a"), job("new", "run-new")]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={[]} />);
    await screen.findByRole("heading", { name: "run-a" });
    await user.click(screen.getByLabelText("Select result a"));
    await user.click(screen.getByLabelText("Select result b"));

    await user.click(screen.getByRole("button", { name: "Refresh candidates" }));
    expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible();
    failedRefresh.resolve(response({
      error: { code: "internal_server_error", message: "Safe refresh failure" },
      request_id: "refresh-failure",
    }, 503));
    expect(await screen.findByRole("heading", { name: "Comparison candidates unavailable" })).toBeVisible();
    expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("heading", { name: "run-new" });
    expect(screen.getByText("Selected 2 of 4 maximum")).toBeVisible();
    expect(screen.getByLabelText("Select result new")).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: "Compare selected results" }));
    expect(push).toHaveBeenLastCalledWith("/comparisons?job_id=b&job_id=a");
  });

  it.each([
    [["only-one"]],
    [["one", ""]],
    [["same", "same"]],
    [["1", "2", "3", "4", "5"]],
  ])("validates direct query %j before making result requests", async (jobIds) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response([]));
    vi.stubGlobal("fetch", fetcher);
    render(<ComparisonWorkspace jobIds={jobIds} />);
    expect(await screen.findByRole("heading", { name: "Comparison selection is invalid" })).toBeVisible();
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/result"))).toHaveLength(0);
  });

  it("preserves direct query order regardless of response completion order and encodes every result path", async () => {
    const firstResponse = deferred<Response>();
    const secondResponse = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      if (path.includes("second%20%2F%20job/result")) return secondResponse.promise;
      if (path.includes("first%3Fjob/result")) return firstResponse.promise;
      return Promise.reject(new Error("unexpected path"));
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ComparisonWorkspace jobIds={["second / job", "first?job"]} />);
    expect(screen.getAllByRole("status")).toHaveLength(1);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));

    firstResponse.resolve(response(result("first?job", "run-first")));
    expect(await screen.findByRole("heading", { name: "run-first" })).toBeVisible();
    secondResponse.resolve(response(result("second / job", "run-second")));
    await screen.findByRole("heading", { name: "run-second" });

    const matrix = screen.getByRole("table", { name: "Backend account and cash snapshots in selected order" });
    expect(within(matrix).getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Backend field",
      "1: second / job",
      "2: first?job",
    ]);
    expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith("/result")).map(([url]) => url)).toEqual([
      "/api/backend/api/v1/paper-jobs/second%20%2F%20job/result",
      "/api/backend/api/v1/paper-jobs/first%3Fjob/result",
    ]);
  });

  it("keeps independently encoded source links visible for every loading slot", async () => {
    const firstResponse = deferred<Response>();
    const secondResponse = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      return path.includes("loading%20%2F%20%3F") ? firstResponse.promise : secondResponse.promise;
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ComparisonWorkspace jobIds={["loading / ?", "other #value"]} />);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
    for (const heading of screen.getAllByRole("heading", { name: "Loading selected result" })) {
      expect(heading.closest("article")).toHaveAttribute("aria-busy", "true");
    }

    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job loading / ?" })).toHaveAttribute(
      "href",
      "/portfolio-records/loading%20%2F%20%3F",
    );
    expect(screen.getByRole("link", { name: "Open Paper Job for selected job loading / ?" })).toHaveAttribute(
      "href",
      "/paper-jobs/loading%20%2F%20%3F",
    );
    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job other #value" })).toHaveAttribute(
      "href",
      "/portfolio-records/other%20%23value",
    );
    expect(screen.getByRole("link", { name: "Open Paper Job for selected job other #value" })).toHaveAttribute(
      "href",
      "/paper-jobs/other%20%23value",
    );
  });

  it("suppresses a stale earlier batch when the applied comparison set changes", async () => {
    const pending = new Map<string, ReturnType<typeof deferred<Response>>>();
    for (const id of ["old-a", "old-b", "new-a", "new-b"]) pending.set(id, deferred<Response>());
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      const id = ["old-a", "old-b", "new-a", "new-b"].find((candidate) => path.includes(`/${candidate}/result`));
      return id ? pending.get(id)!.promise : Promise.reject(new Error("unexpected path"));
    });
    vi.stubGlobal("fetch", fetcher);
    const view = render(<ComparisonWorkspace jobIds={["old-a", "old-b"]} />);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(3));
    view.rerender(<ComparisonWorkspace jobIds={["new-a", "new-b"]} />);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(5));

    pending.get("new-a")!.resolve(response(result("new-a", "run-new-a")));
    pending.get("new-b")!.resolve(response(result("new-b", "run-new-b")));
    await screen.findByRole("heading", { name: "run-new-b" });
    pending.get("old-a")!.resolve(response(result("old-a", "run-old-a")));
    pending.get("old-b")!.resolve(response(result("old-b", "run-old-b")));
    await waitFor(() => expect(screen.queryByRole("heading", { name: "run-old-a" })).not.toBeInTheDocument());
  });

  it("keeps partial success, retries one failed run, and refreshes every selected result exactly once", async () => {
    const calls = new Map<string, number>();
    const retryResponse = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      const id = path.includes("job-a") ? "job-a" : "job-b";
      const count = (calls.get(id) ?? 0) + 1;
      calls.set(id, count);
      if (id === "job-b" && count === 1) {
        return Promise.resolve(response({
          error: { code: "paper_job_result_invalid", message: "Safe invalid result" },
          request_id: "body-id",
          private_path: "C:\\private\\paper.json",
        }, 409, "failed-result-request"));
      }
      if (id === "job-b" && count === 2) {
        return retryResponse.promise;
      }
      return Promise.resolve(response(
        id === "job-a" ? result("mismatched-backend-job", "run-job-a") : result(id, `run-${id}`),
      ));
    });
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<ComparisonWorkspace jobIds={["job-a", "job-b"]} />);

    expect(await screen.findByRole("heading", { name: "run-job-a" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Paper job result is invalid" })).toBeVisible();
    expect(screen.getByText("Safe invalid result")).toBeVisible();
    expect(screen.getByText("Request failed-result-request")).toBeVisible();
    expect(screen.queryByText(/private\\paper/)).not.toBeInTheDocument();
    expect(calls).toEqual(new Map([["job-a", 1], ["job-b", 1]]));
    expect(screen.getAllByText("mismatched-backend-job").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job job-a" })).toHaveAttribute("href", "/portfolio-records/job-a");
    expect(screen.getByRole("link", { name: "Open Paper Job for selected job job-a" })).toHaveAttribute("href", "/paper-jobs/job-a");
    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job job-b" })).toHaveAttribute("href", "/portfolio-records/job-b");
    expect(screen.getByRole("link", { name: "Open Paper Job for selected job job-b" })).toHaveAttribute("href", "/paper-jobs/job-b");
    expect(screen.queryByRole("link", { name: /selected job mismatched-backend-job/ })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry result for job-b" }));
    expect(await screen.findByRole("heading", { name: "Loading selected result" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job job-b" })).toHaveAttribute("href", "/portfolio-records/job-b");
    expect(screen.getByRole("link", { name: "Open Paper Job for selected job job-b" })).toHaveAttribute("href", "/paper-jobs/job-b");
    retryResponse.resolve(response(result("job-b", "run-job-b")));
    expect(await screen.findByRole("heading", { name: "run-job-b" })).toBeVisible();
    expect(calls).toEqual(new Map([["job-a", 1], ["job-b", 2]]));

    await user.click(screen.getByRole("button", { name: "Refresh comparison" }));
    await waitFor(() => expect(calls).toEqual(new Map([["job-a", 2], ["job-b", 3]])));
  });

  it("renders exact provenance, matrices, duplicate positions and changes without full orders, fills, ranks, or derived metrics", async () => {
    const second = result("job-b", "run-b");
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      return Promise.resolve(response(path.includes("job-b") ? second : result("job-a", "run-a")));
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ComparisonWorkspace jobIds={["job-a", "job-b"]} />);
    await screen.findByRole("heading", { name: "run-b" });

    expect(screen.getAllByText("Reference record schema")).toHaveLength(2);
    expect(screen.getByRole("table", { name: "Backend session summaries in selected order" })).toHaveTextContent("-91");
    expect(screen.getByRole("table", { name: "Backend result audits in selected order" })).toHaveTextContent("-92");
    const positions = screen.getByRole("table", { name: "Run 1 artifact starting positions in exact API order" });
    expect(within(positions).getAllByText("DUP")).toHaveLength(2);
    const changes = screen.getByRole("table", { name: "Run 1 session-summary position changes in exact API order" });
    expect(within(changes).getAllByText("91")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Open Portfolio Record for selected job job-a" })).toHaveAttribute("href", "/portfolio-records/job-a");
    for (const forbidden of ["Orders", "Fills", "Winner", "Rank", "Recommendation", "P&L", "Return", "Exposure", "Chart"]) {
      expect(screen.queryByRole("heading", { name: forbidden })).not.toBeInTheDocument();
    }
  });

  it("keeps successful empty position collections visible", async () => {
    const empty = result("empty", "run-empty");
    empty.artifact.starting_account_state.positions = [];
    empty.artifact.ending_account_state.positions = [];
    empty.artifact.session_summary.starting_positions = [];
    empty.artifact.session_summary.ending_positions = [];
    empty.artifact.session_summary.position_changes = [];
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url) => {
      const path = String(url);
      if (path.includes("?status=succeeded")) return Promise.resolve(response([]));
      return Promise.resolve(response(path.includes("empty") ? empty : result("other", "run-other")));
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ComparisonWorkspace jobIds={["empty", "other"]} />);
    await screen.findByRole("heading", { name: "run-empty" });
    expect(screen.getAllByText(/result request succeeded and returned no rows/)).toHaveLength(5);
  });

  it("localizes the comparison workspace while preserving candidate order and raw audit values", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(response([
        job("comparison-first", "run-comparison-first"),
        job("comparison-second", "run-comparison-second"),
      ])),
    );

    render(<ComparisonWorkspace jobIds={[]} />, { locale: "zh-CN" });

    expect(screen.getByRole("heading", { name: "模拟运行对比工作区" })).toBeVisible();
    expect(screen.getByRole("button", { name: "对比所选结果" })).toBeVisible();
    await screen.findByRole("heading", { name: "run-comparison-first" });
    expect(screen.getAllByRole("heading", { level: 2 }).filter((heading) => heading.textContent?.startsWith("run-comparison-")).map((heading) => heading.textContent)).toEqual([
      "run-comparison-first",
      "run-comparison-second",
    ]);
    const firstCard = screen.getByRole("heading", { name: "run-comparison-first" }).closest("li");
    expect(firstCard).not.toBeNull();
    expect(within(firstCard as HTMLElement).getByText("comparison-first")).toBeVisible();
    expect(within(firstCard as HTMLElement).getAllByText("succeeded").length).toBeGreaterThan(0);
    expect(within(firstCard as HTMLElement).getAllByText("2026-07-15T10:00:00Z").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("选择结果 comparison-first")).toBeVisible();
  });
});
