import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  fetchHealth,
  fetchResearchRunDetail,
  fetchResearchRuns,
  fetchStrategies,
  fetchStrategyDetail,
  type ResearchRunDetailResponse,
  type ResearchRunListResponse,
  type StrategyDetailResponse,
  type StrategyListResponse,
} from "./api-client";

function response(
  body: unknown,
  { status = 200, requestId = "request-123" }: { status?: number; requestId?: string } = {},
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    },
  });
}

describe("fetchHealth", () => {
  it("returns typed health data and the server request ID", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ status: "ok", service: "el-psy-quant", api_version: "v1" }),
    );

    await expect(fetchHealth(fetcher)).resolves.toEqual({
      data: { status: "ok", service: "el-psy-quant", api_version: "v1" },
      requestId: "request-123",
    });
    expect(fetcher).toHaveBeenCalledWith("/api/backend/api/v1/health", {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  });

  it("translates the stable backend envelope without leaking extra fields", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(
        {
          error: { code: "service_unavailable", message: "Service unavailable" },
          request_id: "body-request-id",
          private_detail: "C:\\private\\database.sqlite3",
        },
        { status: 503, requestId: "header-request-id" },
      ),
    );

    await expect(fetchHealth(fetcher)).rejects.toMatchObject({
      status: 503,
      code: "service_unavailable",
      publicMessage: "Service unavailable",
      requestId: "header-request-id",
    });
  });

  it.each([
    [new Response("not-json", { status: 200 }), "api_response_invalid"],
    [response({ status: "almost" }), "api_response_invalid"],
    [new Response("private raw failure", { status: 502 }), "api_request_failed"],
  ])("sanitizes malformed response %#", async (malformed, code) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(malformed);

    try {
      await fetchHealth(fetcher);
      throw new Error("expected fetchHealth to reject");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect(error).toMatchObject({ code });
      expect(String(error)).not.toContain("private raw failure");
    }
  });

  it("sanitizes network failures", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(
      new Error("connect ECONNREFUSED with private details"),
    );

    await expect(fetchHealth(fetcher)).rejects.toMatchObject({
      status: 0,
      code: "api_unavailable",
      publicMessage: "The local API is unavailable.",
      requestId: null,
    });
  });
});

const strategy = {
  name: "moving_average_crossover",
  display_name: "Moving Average Crossover",
  description: "Description",
};

const runSummary = {
  experiment_slug: "my-experiment",
  run_id: "run_1",
  experiment_name: "My Experiment",
  strategy: "moving_average_crossover",
  data_source: "cache" as const,
  symbols: ["AAPL"],
};

const runDetail = {
  manifest_schema_version: 1 as const,
  metrics_schema_version: 1 as const,
  experiment_slug: "my-experiment",
  run_id: "run_1",
  experiment_name: "My Experiment",
  strategy: "moving_average_crossover",
  data: { source: "cache" as const, symbols: ["AAPL"] },
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
      final_equity: 1100,
      total_return: 0.1,
      max_drawdown: -0.02,
      periods: 20,
      cagr: null,
      annualized_volatility: null,
      sharpe_ratio: null,
    },
  ],
};

describe("business endpoint clients", () => {
  it("uses generated success types and fixed same-origin list paths", async () => {
    const strategyFetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ strategies: [strategy] }));
    const researchFetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ runs: [runSummary] }));

    const strategies: StrategyListResponse = (
      await fetchStrategies(strategyFetcher)
    ).data;
    const runs: ResearchRunListResponse = (await fetchResearchRuns(researchFetcher)).data;

    expect(strategies.strategies[0].name).toBe("moving_average_crossover");
    expect(runs.runs[0].run_id).toBe("run_1");
    expect(strategyFetcher).toHaveBeenCalledWith("/api/backend/api/v1/strategies", {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    expect(researchFetcher).toHaveBeenCalledWith("/api/backend/api/v1/research-runs", {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  });

  it("path-segment encodes exact strategy, experiment, and run identifiers", async () => {
    const strategyFetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({
        ...strategy,
        parameters: [
          { name: "fast_window", value_type: "integer", required: true, default: null },
        ],
      }),
    );
    const researchFetcher = vi.fn<typeof fetch>().mockResolvedValue(response(runDetail));

    const detail: StrategyDetailResponse = (
      await fetchStrategyDetail("moving / average?", strategyFetcher)
    ).data;
    const research: ResearchRunDetailResponse = (
      await fetchResearchRunDetail("my / experiment", "run ? 1", researchFetcher)
    ).data;

    expect(detail.parameters).toHaveLength(1);
    expect(research.metrics).toHaveLength(1);
    expect(strategyFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/strategies/moving%20%2F%20average%3F",
    );
    expect(researchFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/research-runs/my%20%2F%20experiment/run%20%3F%201",
    );
  });

  it("preserves bounded backend errors and request IDs", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(
        {
          error: {
            code: "research_artifact_root_unavailable",
            message: "Research artifact root is unavailable",
          },
          request_id: "body-id",
          private_detail: "C:\\private\\artifacts",
        },
        { status: 503, requestId: "header-id" },
      ),
    );

    await expect(fetchResearchRuns(fetcher)).rejects.toMatchObject({
      status: 503,
      code: "research_artifact_root_unavailable",
      publicMessage: "Research artifact root is unavailable",
      requestId: "header-id",
    });
  });

  it.each([
    [fetchStrategies, { strategies: [{ ...strategy, display_name: 42 }] }],
    [fetchResearchRuns, { runs: [{ ...runSummary, symbols: "AAPL" }] }],
  ])("sanitizes malformed business response %#", async (request, body) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(body));

    await expect(request(fetcher)).rejects.toMatchObject({
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId: "request-123",
    });
  });
});
