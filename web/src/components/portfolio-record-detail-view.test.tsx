import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { paperJobResultFixture } from "@/test/paper-job-result-fixture";
import { PortfolioRecordDetailView } from "./portfolio-record-detail-view";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": "portfolio-detail-request" },
  });
}

describe("PortfolioRecordDetailView", () => {
  it("uses one loading region and only the exact result endpoint", async () => {
    let resolveFetch: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(() => new Promise((resolve) => { resolveFetch = resolve; }));
    vi.stubGlobal("fetch", fetcher);
    render(<PortfolioRecordDetailView jobId="job / ?" />);
    expect(screen.getAllByRole("status")).toHaveLength(1);
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/paper-jobs/job%20%2F%20%3F/result",
    );
    resolveFetch?.(response(paperJobResultFixture));
    expect(await screen.findByRole("heading", { name: "run-156" })).toBeVisible();
  });

  it("renders every result area while preserving duplicate API rows and backend facts", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(paperJobResultFixture));
    vi.stubGlobal("fetch", fetcher);
    render(<PortfolioRecordDetailView jobId={paperJobResultFixture.job_id} />);
    await screen.findByRole("heading", { name: "run-156" });

    expect(screen.getByRole("heading", { name: "Identity and result reference" })).toBeVisible();
    expect(screen.getByText("2026-07-15T12:05:00Z")).toBeVisible();
    expect(screen.getByText("2026-07-15T09:59:00Z")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Account and cash snapshots" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Starting account state" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Ending account state" })).toBeVisible();
    expect(screen.getByText(/Account cash is not calculated total marked-to-market equity/)).toBeVisible();
    expect(screen.getByText(/Changes and counts above are backend-provided/)).toBeVisible();

    const starting = screen.getByRole("table", { name: "Starting account positions in exact API order" });
    const ending = screen.getByRole("table", { name: "Ending account positions in exact API order" });
    const summaryStarting = screen.getByRole("table", { name: "Session-summary starting positions in exact API order" });
    const summaryEnding = screen.getByRole("table", { name: "Session-summary ending positions in exact API order" });
    for (const table of [starting, ending, summaryStarting, summaryEnding]) {
      expect(within(table).getAllByRole("row")).toHaveLength(3);
      expect(within(table).getAllByText("DUP")).toHaveLength(2);
    }

    const changes = screen.getByRole("table", { name: "Position changes in exact API order" });
    expect(within(changes).getAllByRole("row")).toHaveLength(3);
    expect(within(changes).getAllByText("91")).toHaveLength(2);
    const orders = screen.getByRole("table", { name: "Orders in exact API order" });
    expect(within(orders).getAllByRole("row")).toHaveLength(3);
    expect(within(orders).getAllByText("order-duplicate")).toHaveLength(2);
    const fills = screen.getByRole("table", { name: "Fills in exact API order" });
    expect(within(fills).getAllByRole("row")).toHaveLength(3);
    expect(within(fills).getAllByText("Not available")).toHaveLength(2);

    const sessionSection = screen.getByRole("heading", { name: "Backend session summary" }).closest("section");
    expect(sessionSection).not.toBeNull();
    expect(within(sessionSection as HTMLElement).getByText("-91")).toBeVisible();
    expect(within(sessionSection as HTMLElement).getByText("41")).toBeVisible();
    expect(within(sessionSection as HTMLElement).getByText("42")).toBeVisible();
    const auditSection = screen.getByRole("heading", { name: "Backend result audit" }).closest("section");
    expect(auditSection).not.toBeNull();
    expect(within(auditSection as HTMLElement).getByText("Audit schema").nextElementSibling).toHaveTextContent("2");
    for (const value of ["-92", "51", "52", "53", "54", "55"]) {
      expect(within(auditSection as HTMLElement).getByText(value)).toBeVisible();
    }
    expect(within(auditSection as HTMLElement).getByText(/backend cross-validates/)).toBeVisible();
    expect(screen.queryByText(/result_url/i)).not.toBeInTheDocument();
  });

  it("renders successful empty states for every empty result collection", async () => {
    const empty = {
      ...paperJobResultFixture,
      artifact: {
        ...paperJobResultFixture.artifact,
        starting_account_state: { ...paperJobResultFixture.artifact.starting_account_state, positions: [] },
        ending_account_state: { ...paperJobResultFixture.artifact.ending_account_state, positions: [] },
        orders: [],
        fills: [],
        session_summary: {
          ...paperJobResultFixture.artifact.session_summary,
          starting_positions: [],
          ending_positions: [],
          position_changes: [],
        },
      },
    };
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(response(empty)));
    render(<PortfolioRecordDetailView jobId={paperJobResultFixture.job_id} />);
    await screen.findByRole("heading", { name: "run-156" });
    for (const message of [
      "No starting account positions",
      "No ending account positions",
      "No session-summary starting positions",
      "No session-summary ending positions",
      "No position changes",
      "No orders",
      "No fills",
    ]) {
      expect(screen.getByText(new RegExp(message))).toBeVisible();
    }
  });

  it.each([
    ["paper_job_result_unavailable", 409, "Paper job result unavailable"],
    ["paper_job_result_invalid", 409, "Paper job result is invalid"],
    ["product_database_unavailable", 503, "Product database unavailable"],
    ["paper_artifact_root_unavailable", 503, "Paper artifact root unavailable"],
  ])("keeps %s distinct with request ID and manual retry", async (code, status, title) => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response({ error: { code, message: `Safe ${code}` }, request_id: "body" }, status))
      .mockResolvedValueOnce(response(paperJobResultFixture));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioRecordDetailView jobId={paperJobResultFixture.job_id} />);
    expect(await screen.findByRole("heading", { name: title })).toBeVisible();
    expect(screen.getByText("Request portfolio-detail-request")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "run-156" })).toBeVisible();
  });

  it("renders not-found back navigation without a retry loop", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(response({
      error: { code: "paper_job_not_found", message: "Paper job was not found" },
      request_id: "body",
    }, 404)));
    render(<PortfolioRecordDetailView jobId="missing" />);
    expect(await screen.findByRole("heading", { name: "Paper job not found" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Return to portfolio records" })).toHaveAttribute("href", "/portfolio-records");
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it.each([
    ["malformed response", () => Promise.resolve(response({ ...paperJobResultFixture, artifact: null })), "The local API returned an invalid response.", "portfolio-detail-request"],
    ["transport failure", () => Promise.reject(new Error("network secret")), "The local API is unavailable.", null],
  ])("bounds %s and supports manual retry", async (_label, firstResponse, message, requestId) => {
    const fetcher = vi.fn<typeof fetch>()
      .mockImplementationOnce(firstResponse)
      .mockResolvedValueOnce(response(paperJobResultFixture));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioRecordDetailView jobId={paperJobResultFixture.job_id} />);
    expect(await screen.findByRole("heading", { name: "Portfolio record unavailable" })).toBeVisible();
    expect(screen.getByText(message)).toBeVisible();
    if (requestId) expect(screen.getByText(`Request ${requestId}`)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "run-156" })).toBeVisible();
  });
});
