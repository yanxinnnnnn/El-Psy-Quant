import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResearchRunDetailView } from "./research-run-detail-view";
import { ResearchRunListView } from "./research-run-list-view";
import { StrategyDetailView } from "./strategy-detail-view";
import { StrategyListView } from "./strategy-list-view";

vi.mock("next/navigation", () => ({
  usePathname: () => "/strategies",
}));

afterEach(() => {
  vi.unstubAllGlobals();
});

function apiResponse(
  body: unknown,
  { status = 200, requestId = "request-123" }: { status?: number; requestId?: string } = {},
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
  });
}

const strategy = {
  name: "moving_average_crossover",
  display_name: "Moving Average Crossover",
  description: "Produces research results from moving-average crossover signals.",
};

const runSummary = {
  experiment_slug: "my-experiment",
  run_id: "run_1",
  experiment_name: "My Experiment",
  strategy: "moving_average_crossover",
  data_source: "cache",
  symbols: ["AAPL", "MSFT"],
};

const runDetail = {
  manifest_schema_version: 1,
  metrics_schema_version: 1,
  experiment_slug: "my-experiment",
  run_id: "run_1",
  experiment_name: "My Experiment",
  strategy: "moving_average_crossover",
  data: { source: "cache", symbols: ["AAPL", "MSFT"] },
  parameters: {
    fast_window: 10,
    slow_window: 20,
    initial_capital: 1000,
    transaction_cost_rate: 0.001,
    slippage_rate: 0.002,
  },
  evaluation: { periods_per_year: 252, annual_risk_free_rate: 0.02 },
  artifacts: {
    config: "config.yaml",
    metadata: "metadata.json",
    summary: "results/summary.csv",
    metrics: "results/metrics.json",
    logs_dir: "logs",
  },
  metrics: [
    {
      symbol: "AAPL",
      initial_equity: 1000,
      final_equity: 1125,
      total_return: 0.125,
      max_drawdown: -0.025,
      periods: 100,
      cagr: null,
      annualized_volatility: null,
      sharpe_ratio: null,
    },
  ],
};

describe("StrategyListView", () => {
  it("renders loading and then backend-ordered strategy data", async () => {
    let resolveFetch: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetcher);

    render(<StrategyListView />);
    const statusRegions = screen.getAllByRole("status");
    expect(statusRegions).toHaveLength(1);
    expect(statusRegions[0]).toHaveAttribute("aria-busy", "true");
    expect(statusRegions[0]).toHaveTextContent("Loading the built-in strategy");
    expect(screen.getByText("Loading the built-in strategy catalog…")).not.toHaveAttribute(
      "role",
    );

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    resolveFetch?.(apiResponse({ strategies: [strategy] }));
    expect(await screen.findByRole("heading", { name: "Moving Average Crossover" })).toBeVisible();
    expect(screen.getByText("moving_average_crossover")).toBeVisible();
    expect(screen.getByRole("link", { name: /Inspect Moving Average/i })).toHaveAttribute(
      "href",
      "/strategies/moving_average_crossover",
    );
  });

  it("distinguishes a successful empty catalog", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(apiResponse({ strategies: [] })),
    );

    render(<StrategyListView />);
    expect(await screen.findByRole("heading", { name: "No built-in strategies are available" })).toBeVisible();
  });

  it("shows a safe failure and manually retries", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("C:\\private\\network"))
      .mockResolvedValueOnce(apiResponse({ strategies: [strategy] }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<StrategyListView />);
    expect(await screen.findByRole("alert")).toHaveTextContent("local API is unavailable");
    expect(screen.queryByText(/private/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "Moving Average Crossover" })).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});

describe("StrategyDetailView", () => {
  it("renders exact metadata and descriptive parameters", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        apiResponse({
          ...strategy,
          parameters: [
            { name: "fast_window", value_type: "integer", required: true, default: null },
            { name: "initial_capital", value_type: "number", required: false, default: 1 },
          ],
        }),
      ),
    );

    render(<StrategyDetailView strategyName="moving_average_crossover" />);
    expect(await screen.findByRole("heading", { name: "Moving Average Crossover" })).toBeVisible();
    expect(screen.getByText("Exact name: moving_average_crossover")).toBeVisible();
    expect(screen.getByRole("table", { name: /Parameter metadata/i })).toBeVisible();
    expect(screen.getByText("Not available")).toBeVisible();
    expect(screen.getByRole("link", { name: "Browse research runs" })).toHaveAttribute(
      "href",
      "/research-runs",
    );
  });

  it("renders a bounded not-found view with request ID and back link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        apiResponse(
          { error: { code: "not_found", message: "Not Found" }, request_id: "body-id" },
          { status: 404, requestId: "header-id" },
        ),
      ),
    );

    render(<StrategyDetailView strategyName="unknown" />);
    expect(await screen.findByRole("heading", { name: "Strategy not found" })).toBeVisible();
    expect(screen.getByText("Request header-id")).toBeVisible();
    expect(screen.getByRole("link", { name: "Return to strategy list" })).toHaveAttribute(
      "href",
      "/strategies",
    );
  });
});

describe("ResearchRunListView", () => {
  it("renders configured research runs in API order", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(apiResponse({ runs: [runSummary] })),
    );

    render(<ResearchRunListView />);
    expect(await screen.findByRole("heading", { name: "My Experiment" })).toBeVisible();
    expect(screen.getByText("my-experiment / run_1")).toBeVisible();
    expect(screen.getByText("AAPL, MSFT")).toBeVisible();
  });

  it("distinguishes a successful empty configured root", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(apiResponse({ runs: [] })));

    render(<ResearchRunListView />);
    expect(await screen.findByRole("heading", { name: "The configured research root is empty" })).toBeVisible();
  });

  it.each([
    ["research_artifact_root_unavailable", "Research root unavailable", 503],
    ["research_artifact_invalid", "Research artifacts are invalid", 422],
  ])("renders and retries bounded %s failures", async (code, heading, status) => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        apiResponse(
          { error: { code, message: "Public research error" }, request_id: "body-id" },
          { status, requestId: "header-id" },
        ),
      )
      .mockResolvedValueOnce(apiResponse({ runs: [runSummary] }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<ResearchRunListView />);
    const alert = await screen.findByRole("alert");
    expect(screen.getByRole("heading", { name: heading })).toBeVisible();
    expect(alert).toHaveTextContent("Public research error");
    expect(screen.getByText("Request header-id")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "My Experiment" })).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("uses a neutral title for network failures and still retries safely", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("C:\\private\\network detail"))
      .mockResolvedValueOnce(apiResponse({ runs: [runSummary] }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<ResearchRunListView />);
    const alert = await screen.findByRole("alert");
    expect(screen.getByRole("heading", { name: "Research runs unavailable" })).toBeVisible();
    expect(alert).toHaveTextContent("The local API is unavailable.");
    expect(alert).not.toHaveTextContent("private");
    expect(screen.queryByText(/Request /)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "My Experiment" })).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});

describe("ResearchRunDetailView", () => {
  it("renders every saved metric field and nullable values safely", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(apiResponse(runDetail)),
    );

    render(<ResearchRunDetailView experimentSlug="my-experiment" runId="run_1" />);
    expect(await screen.findByRole("heading", { name: "My Experiment" })).toBeVisible();
    const table = screen.getByRole("table", { name: /Saved per-symbol metrics/i });
    for (const heading of [
      "Symbol",
      "Initial equity",
      "Final equity",
      "Total return",
      "Maximum drawdown",
      "Periods",
      "CAGR",
      "Annualized volatility",
      "Sharpe ratio",
    ]) {
      expect(screen.getByRole("columnheader", { name: heading })).toBeVisible();
    }
    expect(table).toHaveTextContent("12.50%");
    expect(table).toHaveTextContent("-2.50%");
    expect(screen.getAllByText("Not available")).toHaveLength(3);
    expect(screen.getByText("results/metrics.json").closest("a")).toBeNull();
  });
});
