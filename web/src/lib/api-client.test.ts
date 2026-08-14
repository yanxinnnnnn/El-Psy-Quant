import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  fetchEvidenceManifestDetail,
  fetchEvidenceManifests,
  fetchDemoWorkspace,
  fetchHealth,
  fetchResearchRunDetail,
  fetchResearchRuns,
  fetchStrategies,
  fetchStrategyDetail,
  type DemoWorkspaceDescriptorResponse,
  type ResearchRunDetailResponse,
  type ResearchRunListResponse,
  type EvidenceManifestDetailResponse,
  type EvidenceManifestListResponse,
  type StrategyDetailResponse,
  type StrategyListResponse,
} from "./api-client";

function demoSourceJson(relativePath: string): Record<string, unknown> {
  return JSON.parse(
    readFileSync(resolve(process.cwd(), "..", "examples", "demo_workspace", relativePath), "utf8"),
  ) as Record<string, unknown>;
}

function demoDescriptorFromVersionedSource(): Record<string, unknown> {
  const manifest = demoSourceJson("workspace-manifest.json");
  const paperJobs = manifest.paper_jobs as Array<Record<string, unknown>>;
  const submission = manifest.paper_submission_example as Record<string, unknown>;
  const portfolioReview = manifest.portfolio_review_example as Record<string, unknown>;
  const paperAccount = demoSourceJson("paper_accounts/account-journey.json");
  const paperAccountExpected = paperAccount.expected as Record<string, unknown>;
  const marketTime = demoSourceJson("market_time/replay-journey.json");
  const marketTimeCalendar = marketTime.calendar as Record<string, unknown>;
  const marketTimeSessions = marketTime.sessions as Array<Record<string, unknown>>;
  const marketTimeExpected = marketTime.expected as Record<string, unknown>;
  const strategyOrder = demoSourceJson("strategy_order/strategy-to-risk-journey.json");
  const strategyOrderExpected = strategyOrder.expected as Record<string, unknown>;
  const signalCommand = strategyOrder.signal as Record<string, unknown>;
  const intentCommand = strategyOrder.intent as Record<string, unknown>;
  const allowCommand = strategyOrder.allow_risk as Record<string, unknown>;
  const rejectCommand = strategyOrder.reject_risk as Record<string, unknown>;
  return {
    schema_version: manifest.schema_version,
    dataset_id: manifest.dataset_id,
    dataset_version: manifest.dataset_version,
    display_name: manifest.display_name,
    warning: manifest.warning,
    canonical_strategy_name: manifest.canonical_strategy_name,
    research_run: manifest.research_run,
    evidence_manifests: manifest.evidence_manifests,
    paper_jobs: paperJobs.map(({ job_id, run_id }) => ({ job_id, run_id })),
    comparison_candidate_job_ids: manifest.comparison_candidate_job_ids,
    lifecycle_proposal_example: demoSourceJson("lifecycle_records/proposal-request.json"),
    lifecycle_review_example: demoSourceJson("lifecycle_records/human-review-request.json"),
    paper_job_submission_example: {
      idempotency_key: submission.idempotency_key,
      request: demoSourceJson("paper_artifacts/submission-example.json"),
    },
    portfolio_review_example: {
      create_idempotency_key: portfolioReview.create_idempotency_key,
      request: demoSourceJson("portfolio_reviews/create-request.json"),
    },
    paper_account: {
      account_id: paperAccount.account_id,
      head_version: paperAccountExpected.head_version,
      event_types: paperAccountExpected.event_types,
      snapshot_id: paperAccountExpected.snapshot_id,
      reconciliation_id: paperAccountExpected.reconciliation_id,
    },
    market_time: {
      calendar_id: marketTimeCalendar.id,
      session_ids: marketTimeSessions.map(({ id }) => id),
      replay_id: marketTime.replay_id,
      event_count: (marketTime.events as unknown[]).length,
      event_stream_digest: marketTimeExpected.event_stream_digest,
      checkpoint: {
        status: marketTimeExpected.checkpoint_status,
        position: marketTimeExpected.checkpoint_position,
        last_event_id: marketTimeExpected.checkpoint_last_event_id,
        current_time: marketTimeExpected.checkpoint_current_time,
      },
      recovery: {
        remaining_event_ids: marketTimeExpected.recovery_remaining_event_ids,
        final_status: marketTimeExpected.recovery_final_status,
        final_position: marketTimeExpected.recovery_final_position,
        last_event_id: marketTimeExpected.recovery_last_event_id,
        current_time: marketTimeExpected.recovery_current_time,
      },
    },
    strategy_order: {
      workspace_path: "/strategy-to-risk",
      account_id: strategyOrder.account_id,
      trading_session_id: strategyOrder.trading_session_id,
      instrument_id: strategyOrder.instrument_id,
      runtime: strategyOrder.runtime,
      signal: { ...(strategyOrderExpected.signal as object), receipt: { namespace: "evaluate_strategy_signal", idempotency_key: signalCommand.idempotency_key } },
      intent: { ...(strategyOrderExpected.intent as object), receipt: { namespace: "derive_order_intent", idempotency_key: intentCommand.idempotency_key } },
      allow_decision: { ...(strategyOrderExpected.allow_decision as object), receipt: { namespace: "evaluate_pre_trade_risk", idempotency_key: allowCommand.idempotency_key } },
      reject_decision: { ...(strategyOrderExpected.reject_decision as object), receipt: { namespace: "evaluate_pre_trade_risk", idempotency_key: rejectCommand.idempotency_key } },
    },
  };
}

function mutableDemoDescriptor(): DemoWorkspaceDescriptorResponse {
  return structuredClone(
    demoDescriptorFromVersionedSource(),
  ) as unknown as DemoWorkspaceDescriptorResponse;
}

type DemoDescriptorMutation = (descriptor: DemoWorkspaceDescriptorResponse) => void;

const malformedPortfolioReviewExamples: Array<[string, DemoDescriptorMutation]> = [
  ["unsupported evidence reference type", (descriptor) => {
    descriptor.portfolio_review_example.request.source.components[0]
      .evidence_references[0].reference_type = "unsupported_reference_type";
  }],
  ["blank idempotency key", (descriptor) => {
    descriptor.portfolio_review_example.create_idempotency_key = "   ";
  }],
  ["component without research-origin evidence", (descriptor) => {
    descriptor.portfolio_review_example.request.source.components[0]
      .evidence_references[0].reference_type = "promotion_record";
  }],
  ["duplicate component identity", (descriptor) => {
    const components = descriptor.portfolio_review_example.request.source.components;
    components[1].component_id = components[0].component_id;
  }],
  ["duplicate evidence identity", (descriptor) => {
    const evidence = descriptor.portfolio_review_example.request.source.components[0]
      .evidence_references;
    evidence[1] = structuredClone(evidence[0]);
  }],
  ["fewer than two components", (descriptor) => {
    descriptor.portfolio_review_example.request.source.components.pop();
  }],
  ["observation width mismatch", (descriptor) => {
    descriptor.portfolio_review_example.request.source.return_observations[0]
      .component_returns.pop();
  }],
  ["fewer than three observations", (descriptor) => {
    descriptor.portfolio_review_example.request.source.return_observations.splice(2);
  }],
  ["timezone-naive observation", (descriptor) => {
    descriptor.portfolio_review_example.request.source.return_observations[0].timestamp =
      "2026-01-02T00:00:00";
  }],
  ["non-increasing observations", (descriptor) => {
    const observations = descriptor.portfolio_review_example.request.source.return_observations;
    observations[1].timestamp = "2026-01-01T00:00:00Z";
  }],
  ["missing scenario weight", (descriptor) => {
    delete descriptor.portfolio_review_example.request.baseline_scenario
      .weights["demo-msft-sleeve"];
  }],
  ["extra scenario weight", (descriptor) => {
    descriptor.portfolio_review_example.request.proposed_scenario
      .weights["extra-component"] = 0;
  }],
  ["negative scenario weight", (descriptor) => {
    const weights = descriptor.portfolio_review_example.request.baseline_scenario.weights;
    weights["demo-aapl-sleeve"] = -0.1;
    weights["demo-msft-sleeve"] = 1.1;
  }],
  ["non-unit scenario weight total", (descriptor) => {
    descriptor.portfolio_review_example.request.baseline_scenario
      .weights["demo-aapl-sleeve"] = 0.7;
  }],
  ["boolean scenario weight", (descriptor) => {
    descriptor.portfolio_review_example.request.baseline_scenario
      .weights["demo-aapl-sleeve"] = true as unknown as number;
  }],
  ["missing proposed component", (descriptor) => {
    descriptor.portfolio_review_example.request.proposed_scenario.proposed_component_id =
      "missing-component";
  }],
  ["unchanged proposed component", (descriptor) => {
    const request = descriptor.portfolio_review_example.request;
    request.proposed_scenario.weights = structuredClone(
      request.baseline_scenario.weights,
    );
  }],
  ["identical scenario IDs", (descriptor) => {
    const request = descriptor.portfolio_review_example.request;
    request.proposed_scenario.scenario_id = request.baseline_scenario.scenario_id;
  }],
  ["blank normalized identity", (descriptor) => {
    descriptor.portfolio_review_example.request.source.components[0].component_id = " ";
  }],
  ["extra nested key", (descriptor) => {
    const source = descriptor.portfolio_review_example.request.source;
    (source.components[0] as unknown as Record<string, unknown>).unexpected = true;
  }],
];

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

describe("fetchDemoWorkspace", () => {
  it("accepts the path-free descriptor assembled from the versioned backend source", async () => {
    const descriptor = demoDescriptorFromVersionedSource();
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(descriptor));

    const result = await fetchDemoWorkspace(fetcher);

    expect(result.data.dataset_id).toBe(descriptor.dataset_id);
    expect(result.data.schema_version).toBe(5);
    expect(result.data.dataset_version).toBe(5);
    expect(result.data.comparison_candidate_job_ids).toHaveLength(2);
    expect(result.data.portfolio_review_example.request.review_id).toBe(
      "demo-portfolio-review-001",
    );
    expect(result.data.paper_account).toMatchObject({
      account_id: "demo-paper-account-001",
      head_version: 5,
      snapshot_id: "demo-paper-account-snapshot-001",
      reconciliation_id: "demo-paper-account-reconciliation-001",
    });
    expect(result.data.market_time).toMatchObject({
      calendar_id: "demo-xnys-2026-v1",
      replay_id: "demo-market-replay-001",
      event_count: 5,
      checkpoint: { status: "paused", position: 4 },
      recovery: { final_status: "completed", final_position: 5 },
    });
    expect(result.data.strategy_order).toMatchObject({
      workspace_path: "/strategy-to-risk",
      account_id: "demo-paper-account-001",
      instrument_id: "XNYS:AAPL",
      allow_decision: { outcome: "allow", reason_codes: [] },
      reject_decision: {
        outcome: "reject",
        reason_codes: ["maximum_order_quantity_exceeded"],
      },
    });
    expect(fetcher).toHaveBeenCalledWith("/api/backend/api/v1/demo-workspace", {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    expect(JSON.stringify(result.data)).not.toMatch(/[A-Za-z]:\\|\/data\/workspace/);
  });

  it("rejects a descriptor with non-distinct comparison candidates", async () => {
    const descriptor = demoDescriptorFromVersionedSource();
    const candidates = descriptor.comparison_candidate_job_ids as string[];
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response({
      ...descriptor,
      comparison_candidate_job_ids: [candidates[0], candidates[0]],
    }));

    await expect(fetchDemoWorkspace(fetcher)).rejects.toMatchObject({
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
    });
  });

  it.each([
    ["wrong head", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.paper_account.head_version = 4;
    }],
    ["wrong event order", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.paper_account.event_types.reverse();
    }],
    ["blank snapshot identity", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.paper_account.snapshot_id = "   ";
    }],
  ])("rejects malformed Demo Paper Account identity: %s", async (_name, mutate) => {
    const descriptor = mutableDemoDescriptor();
    mutate(descriptor);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(descriptor));

    await expect(fetchDemoWorkspace(fetcher)).rejects.toMatchObject({
      status: 200,
      code: "api_response_invalid",
    });
  });

  it.each([
    ["wrong digest", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.market_time.event_stream_digest = "not-a-digest";
    }],
    ["completed checkpoint", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.market_time.checkpoint.status = "completed" as "paused";
    }],
    ["incomplete recovery", (descriptor: DemoWorkspaceDescriptorResponse) => {
      descriptor.market_time.recovery.remaining_event_ids.pop();
    }],
  ])("rejects malformed Demo market-time evidence: %s", async (_name, mutate) => {
    const descriptor = mutableDemoDescriptor();
    mutate(descriptor);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(descriptor));

    await expect(fetchDemoWorkspace(fetcher)).rejects.toMatchObject({
      status: 200,
      code: "api_response_invalid",
    });
  });

  it.each(malformedPortfolioReviewExamples)(
    "rejects malformed successful Demo descriptor: %s",
    async (_caseName, mutate) => {
      const descriptor = mutableDemoDescriptor();
      mutate(descriptor);
      const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(descriptor));

      await expect(fetchDemoWorkspace(fetcher)).rejects.toMatchObject({
        status: 200,
        code: "api_response_invalid",
        publicMessage: "The local API returned an invalid response.",
        requestId: "request-123",
      });
      expect(fetcher).toHaveBeenCalledTimes(1);
    },
  );
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

const evidenceSummary = {
  manifest_type: "report_artifact_manifest" as const,
  artifact_key: "founder-report",
  manifest_id: "report-1",
  reference_count: 1,
  created_by: null,
  created_timestamp: "2026-07-15T10:00:00Z",
  label: "Founder report",
  description: null,
};

const evidenceDetail = {
  manifest_type: "report_artifact_manifest" as const,
  artifact_key: "founder-report",
  schema_version: 1 as const,
  manifest_id: "report-1",
  references: [
    {
      schema_version: 1 as const,
      reference_type: "research_summary",
      reference_id: "run-1",
      label: null,
      description: null,
    },
  ],
  label: "Founder report",
  description: null,
  created_by: null,
  created_timestamp: "2026-07-15T10:00:00Z",
  notes: null,
};

describe("business endpoint clients", () => {
  it("uses generated success types and fixed same-origin list paths", async () => {
    const strategyFetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ strategies: [strategy] }));
    const researchFetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ runs: [runSummary] }));
    const evidenceFetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ manifests: [evidenceSummary] }));

    const strategies: StrategyListResponse = (
      await fetchStrategies(strategyFetcher)
    ).data;
    const runs: ResearchRunListResponse = (await fetchResearchRuns(researchFetcher)).data;
    const evidence: EvidenceManifestListResponse = (
      await fetchEvidenceManifests(evidenceFetcher)
    ).data;

    expect(strategies.strategies[0].name).toBe("moving_average_crossover");
    expect(runs.runs[0].run_id).toBe("run_1");
    expect(evidence.manifests[0].manifest_id).toBe("report-1");
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
    expect(evidenceFetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/evidence-manifests",
      {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
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
    const evidenceFetcher = vi.fn<typeof fetch>().mockResolvedValue(response(evidenceDetail));

    const detail: StrategyDetailResponse = (
      await fetchStrategyDetail("moving / average?", strategyFetcher)
    ).data;
    const research: ResearchRunDetailResponse = (
      await fetchResearchRunDetail("my / experiment", "run ? 1", researchFetcher)
    ).data;
    const evidence: EvidenceManifestDetailResponse = (
      await fetchEvidenceManifestDetail(
        "report / artifact?",
        "founder / report?",
        evidenceFetcher,
      )
    ).data;

    expect(detail.parameters).toHaveLength(1);
    expect(research.metrics).toHaveLength(1);
    expect(evidence.manifest_type).toBe("report_artifact_manifest");
    expect(strategyFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/strategies/moving%20%2F%20average%3F",
    );
    expect(researchFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/research-runs/my%20%2F%20experiment/run%20%3F%201",
    );
    expect(evidenceFetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/evidence-manifests/report%20%2F%20artifact%3F/founder%20%2F%20report%3F",
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
    [fetchEvidenceManifests, { manifests: [{ ...evidenceSummary, reference_count: "1" }] }],
  ])("sanitizes malformed business response %#", async (request, body) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(body));

    await expect(request(fetcher)).rejects.toMatchObject({
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId: "request-123",
    });
  });

  it.each([
    [
      "discriminator-mismatched variant",
      { ...evidenceDetail, manifest_type: "strategy_decision_manifest" },
    ],
    [
      "malformed reference",
      { ...evidenceDetail, references: [{ ...evidenceDetail.references[0], label: 42 }] },
    ],
  ])("sanitizes an evidence detail with a %s", async (_label, body) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(body));

    await expect(
      fetchEvidenceManifestDetail("report_artifact_manifest", "founder-report", fetcher),
    ).rejects.toMatchObject({
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId: "request-123",
    });
  });
});
