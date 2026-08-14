import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FounderDashboard } from "@/components/founder-dashboard";
import { PaperJobStatusValue } from "@/components/domain-values";
import { WorkspaceShell } from "@/components/workspace-shell";
import {
  ApiClientError,
  type DemoWorkspaceDescriptorResponse,
  type PaperJobResponse,
} from "@/lib/api-client";
import { comparisonSelectionErrorKey } from "@/lib/comparisons";

const apiMocks = vi.hoisted(() => ({
  fetchDemoWorkspace: vi.fn(),
  fetchEvidenceManifestDetail: vi.fn(),
  fetchEvidenceManifests: vi.fn(),
  fetchHealth: vi.fn(),
  fetchPaperJobs: vi.fn(),
  fetchPortfolioReviews: vi.fn(),
  fetchResearchRuns: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, ...apiMocks };
});

const proposal = {
  proposal_id: "proposal-from-descriptor",
  source_snapshot: {
    snapshot_id: "snapshot-from-descriptor",
    strategy_id: "strategy-from-descriptor",
    lifecycle_state: "research_review",
    rationale: "Descriptor source",
    declared_by: "demo-founder",
    declared_timestamp: "2026-07-01T00:00:00Z",
    notes: [],
    warnings: ["Demo only"],
  },
  target_state: "paper_review",
  rationale: "Request explicit review",
  evidence_references: [],
  requested_by: "demo-founder",
  requested_timestamp: "2026-07-01T00:01:00Z",
  notes: [],
  warnings: ["Non-executing"],
};

const descriptor: DemoWorkspaceDescriptorResponse = {
  schema_version: 5,
  dataset_id: "dataset-from-descriptor",
  dataset_version: 7,
  display_name: "Descriptor Demo Name",
  warning: "Backend warning",
  canonical_strategy_name: "strategy-from-descriptor",
  research_run: {
    experiment_slug: "experiment-from-descriptor",
    run_id: "research-run-from-descriptor",
  },
  evidence_manifests: [
    {
      manifest_type: "report_artifact_manifest",
      artifact_key: "report-from-descriptor",
    },
    {
      manifest_type: "strategy_decision_manifest",
      artifact_key: "decision-from-descriptor",
    },
  ],
  paper_jobs: [
    { job_id: "demo-job-a", run_id: "demo-run-a" },
    { job_id: "demo-job-b", run_id: "demo-run-b" },
  ],
  comparison_candidate_job_ids: ["demo-job-b", "demo-job-a"],
  lifecycle_proposal_example: proposal,
  lifecycle_review_example: {
    transition_record_id: "decision-record-from-descriptor",
    proposal,
    review_outcome: "deferred",
    rationale: "More evidence required",
    resulting_snapshot: null,
    reviewed_by: "demo-founder",
    reviewed_timestamp: "2026-07-01T00:02:00Z",
    notes: [],
    warnings: ["No transition applied"],
  },
  paper_job_submission_example: {
    idempotency_key: "submission-from-descriptor",
    request: {
      run_id: "submission-run",
      created_timestamp: "2026-07-01T00:03:00Z",
      starting_account_state: {
        timestamp: "2026-07-01T00:03:00Z",
        starting_cash: 1000,
        current_cash: 1000,
        positions: {},
      },
      ending_account_state: {
        timestamp: "2026-07-01T00:04:00Z",
        starting_cash: 1000,
        current_cash: 1000,
        positions: {},
      },
      orders: [],
      fills: [],
    },
  },
  portfolio_review_example: {
    create_idempotency_key: "portfolio-review-from-descriptor",
    request: {
      review_id: "review-from-descriptor",
      source: {
        source_id: "source-from-descriptor",
        components: [],
        return_observations: [],
        evaluation_frequency: "daily",
        periods_per_year: 252,
        created_by: "demo-founder",
        created_timestamp: "2026-07-01T00:00:00Z",
        assumptions: [],
        warnings: [],
        missing_evidence: [],
      },
      baseline_scenario: {
        scenario_id: "baseline-from-descriptor",
        weights: {},
        rationale: "Demo baseline",
        assumptions: [],
        warnings: [],
      },
      proposed_scenario: {
        scenario_id: "proposed-from-descriptor",
        weights: {},
        rationale: "Demo proposed",
        assumptions: [],
        warnings: [],
        proposed_component_id: "component-from-descriptor",
      },
      analysis: {
        created_by: "demo-founder",
        created_timestamp: "2026-07-01T00:01:00Z",
        assumptions: [],
        warnings: [],
        missing_evidence: [],
      },
    },
  },
  paper_account: {
    account_id: "paper-account-from-descriptor",
    head_version: 5,
    event_types: [
      "account_created",
      "cash_movement_posted",
      "position_adjustment_posted",
      "account_frozen",
      "account_reactivated",
    ],
    snapshot_id: "paper-account-snapshot-from-descriptor",
    reconciliation_id: "paper-account-reconciliation-from-descriptor",
  },
  market_time: {
    calendar_id: "calendar-from-descriptor",
    session_ids: ["session-from-descriptor-a", "session-from-descriptor-b"],
    replay_id: "replay-from-descriptor",
    event_count: 4,
    event_stream_digest: "c".repeat(64),
    checkpoint: {
      status: "paused",
      position: 2,
      last_event_id: "event-from-descriptor-b",
      current_time: "2026-07-28T13:30:30+00:00",
    },
    recovery: {
      remaining_event_ids: [
        "event-from-descriptor-c",
        "event-from-descriptor-d",
      ],
      final_status: "completed",
      final_position: 4,
      last_event_id: "event-from-descriptor-d",
      current_time: "2026-07-28T13:31:30+00:00",
    },
  },
  strategy_order: {
    workspace_path: "/strategy-to-risk",
    account_id: "paper-account-from-descriptor",
    trading_session_id: "session-from-descriptor-a",
    instrument_id: "XNYS:AAPL",
    runtime: { fast_window: 2, slow_window: 3, target_position_quantity: "10" },
    signal: { id: `sig_${"1".repeat(64)}`, digest: "1".repeat(64), receipt: { namespace: "evaluate_strategy_signal", idempotency_key: "demo-signal" } },
    intent: { id: `oi_${"2".repeat(64)}`, digest: "2".repeat(64), receipt: { namespace: "derive_order_intent", idempotency_key: "demo-intent" } },
    allow_decision: { id: `risk_decision_${"3".repeat(64)}`, digest: "3".repeat(64), outcome: "allow", reason_codes: [], receipt: { namespace: "evaluate_pre_trade_risk", idempotency_key: "demo-risk-allow" } },
    reject_decision: { id: `risk_decision_${"4".repeat(64)}`, digest: "4".repeat(64), outcome: "reject", reason_codes: ["maximum_order_quantity_exceeded"], receipt: { namespace: "evaluate_pre_trade_risk", idempotency_key: "demo-risk-reject" } },
  },
};

function notConfigured() {
  return new ApiClientError({
    status: 404,
    code: "demo_workspace_not_configured",
    publicMessage: "Demo workspace is not configured",
    requestId: "identity-request",
  });
}

function apiFailure(
  code: string,
  requestId: string,
  status = 503,
): ApiClientError {
  return new ApiClientError({
    status,
    code,
    publicMessage: `Bounded failure: ${code}`,
    requestId,
  });
}

function deferred<Data>() {
  let resolve!: (value: Data) => void;
  const promise = new Promise<Data>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

function job(
  jobId: string,
  runId: string,
  status: PaperJobResponse["status"],
  {
    resultAvailable = false,
    attemptStatus = null,
  }: {
    resultAvailable?: boolean;
    attemptStatus?: "running" | "succeeded" | "failed" | "interrupted" | null;
  } = {},
): PaperJobResponse {
  return {
    job_id: jobId,
    run_id: runId,
    status,
    submitted_timestamp: "2026-07-01T01:00:00Z",
    updated_timestamp: "2026-07-01T01:01:00Z",
    attempt_count: attemptStatus === null ? 0 : 1,
    latest_attempt:
      attemptStatus === null
        ? null
        : {
            attempt_id: `attempt-${jobId}`,
            attempt_number: 1,
            status: attemptStatus,
            started_timestamp: "2026-07-01T01:00:10Z",
            completed_timestamp:
              attemptStatus === "running" ? null : "2026-07-01T01:00:50Z",
            error_code:
              attemptStatus === "failed" ? "workflow_validation_failed" : null,
          },
    result_available: resultAvailable,
    result_url: resultAvailable ? `/api/v1/paper-jobs/${jobId}/result` : null,
  };
}

const researchRuns = [
  {
    experiment_slug: "experiment-a",
    run_id: "research-a",
    experiment_name: "Research A",
    strategy: "moving_average_crossover",
    data_source: "csv" as const,
    symbols: ["AAA"],
  },
  {
    experiment_slug: "experiment-a",
    run_id: "research-a",
    experiment_name: "Research A duplicate",
    strategy: "moving_average_crossover",
    data_source: "csv" as const,
    symbols: ["AAA"],
  },
];

const manifests = [
  {
    artifact_key: "artifact-a",
    manifest_type: "report_artifact_manifest" as const,
    schema_version: 1 as const,
    manifest_id: "manifest-a",
    reference_count: 2,
    created_by: "founder",
    created_timestamp: "2026-07-01T02:00:00Z",
    label: "Report A",
    description: null,
  },
  {
    artifact_key: "artifact-a",
    manifest_type: "report_artifact_manifest" as const,
    schema_version: 1 as const,
    manifest_id: "manifest-a",
    reference_count: 2,
    created_by: "founder",
    created_timestamp: "2026-07-01T02:00:00Z",
    label: "Report A duplicate",
    description: null,
  },
];

function arrangeStandard({
  jobs = [
    job("job-queued", "run-queued", "queued"),
    job("job-failed", "run-failed", "failed", { attemptStatus: "failed" }),
    job("job-result", "run-result", "succeeded", {
      resultAvailable: true,
      attemptStatus: "succeeded",
    }),
  ],
}: {
  jobs?: PaperJobResponse[];
} = {}) {
  apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
  apiMocks.fetchHealth.mockResolvedValue({
    data: { status: "ok", service: "el-psy-quant", api_version: "v1" },
    requestId: "health-request",
  });
  apiMocks.fetchResearchRuns.mockResolvedValue({
    data: { runs: researchRuns },
    requestId: "research-request",
  });
  apiMocks.fetchEvidenceManifests.mockResolvedValue({
    data: { manifests },
    requestId: "evidence-request",
  });
  apiMocks.fetchEvidenceManifestDetail.mockImplementation(
    (manifestType: string, artifactKey: string) =>
      Promise.resolve({
        data: {
          manifest_type: manifestType,
          artifact_key: artifactKey,
          manifest_id: `detail-${artifactKey}`,
          schema_version: 1,
        },
        requestId: `evidence-detail-${artifactKey}`,
      }),
  );
  apiMocks.fetchPaperJobs.mockResolvedValue({
    data: jobs,
    requestId: "jobs-request",
  });
}

function renderDashboard(locale: "en" | "zh-CN" = "en") {
  return render(
    <WorkspaceShell>
      <FounderDashboard />
    </WorkspaceShell>,
    { locale },
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMocks.fetchPortfolioReviews.mockResolvedValue({
    data: [],
    requestId: "portfolio-reviews-request",
  });
});

describe("FounderDashboard", () => {
  it("renders Standard identity, separates process health from readiness, and preserves job order and duplicates", async () => {
    const duplicateJobs = [
      job("duplicate-job", "run-first", "queued"),
      job("duplicate-job", "run-second", "failed", { attemptStatus: "failed" }),
      job("result-job", "run-third", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
    ];
    arrangeStandard({ jobs: duplicateJobs });

    renderDashboard();

    expect(
      await screen.findByRole("heading", { name: "What workspace am I in?" }),
    ).toBeVisible();
    expect(screen.getByText("Standard Workspace")).toBeVisible();
    expect(
      screen.getByText(
        "The FastAPI process responded. Research, evidence, and product-database readiness are reported separately.",
      ),
    ).toBeVisible();
    expect(screen.getByText("Configured and populated")).toBeVisible();

    const activity = screen
      .getByRole("heading", { name: "What Paper Job activity exists?" })
      .closest("section");
    expect(activity).not.toBeNull();
    const runHeadings = within(activity as HTMLElement).getAllByRole("heading", {
      level: 3,
    });
    expect(runHeadings.map((heading) => heading.textContent)).toEqual([
      "run-first",
      "run-second",
      "run-third",
    ]);
    expect(
      within(activity as HTMLElement).getAllByText("duplicate-job", {
        selector: "code",
      }),
    ).toHaveLength(2);
    expect(
      within(activity as HTMLElement).getByRole("link", {
        name: "Inspect Portfolio Record",
      }),
    ).toHaveAttribute("href", "/portfolio-records/result-job");
    expect(apiMocks.fetchPaperJobs).toHaveBeenCalledWith({
      status: null,
      limit: 8,
    });
    for (const command of ["Run", "Retry", "Recover", "Cancel", "Submit"]) {
      expect(
        within(activity as HTMLElement).queryByRole("button", {
          name: command,
        }),
      ).not.toBeInTheDocument();
    }
  });

  it("keeps successful regions visible during a research failure and retries only that source", async () => {
    arrangeStandard();
    apiMocks.fetchResearchRuns
      .mockRejectedValueOnce(
        new ApiClientError({
          status: 503,
          code: "research_artifact_root_unavailable",
          publicMessage: "Research root unavailable",
          requestId: "research-failed-request",
        }),
      )
      .mockResolvedValueOnce({
        data: { runs: researchRuns },
        requestId: "research-retry-request",
      });
    const user = userEvent.setup();

    renderDashboard();

    expect(await screen.findByText("Partially available")).toBeVisible();
    expect(screen.getAllByText(/research_artifact_root_unavailable/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/research-failed-request/).length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "Saved evidence manifests in source order" }),
    ).toBeVisible();
    expect(screen.getByText("Report A")).toBeVisible();

    await user.click(
      screen.getByRole("button", { name: "Retry research runs" }),
    );
    await waitFor(() =>
      expect(screen.getByText("Research A")).toBeVisible(),
    );
    expect(apiMocks.fetchResearchRuns).toHaveBeenCalledTimes(2);
    expect(apiMocks.fetchEvidenceManifests).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchPaperJobs).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchHealth).toHaveBeenCalledTimes(1);
  });

  it("distinguishes invalid data, keeps stable technical identity, and does not relabel it as empty", async () => {
    arrangeStandard();
    apiMocks.fetchEvidenceManifests.mockRejectedValue(
      new ApiClientError({
        status: 200,
        code: "api_response_invalid",
        publicMessage: "The local API returned an invalid response.",
        requestId: "invalid-evidence-request",
      }),
    );

    renderDashboard();

    expect(await screen.findByText("Invalid response")).toBeVisible();
    expect(screen.getAllByText(/api_response_invalid/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/invalid-evidence-request/).length).toBeGreaterThan(0);
    expect(screen.getByText("Partially available")).toBeVisible();
    expect(screen.getByText("Research A")).toBeVisible();
  });

  it.each([
    ["api_response_invalid", "health-invalid-request"],
    ["api_unavailable", "health-unavailable-request"],
  ])(
    "reports health %s with successful business reads as partially available",
    async (code, requestId) => {
      arrangeStandard();
      apiMocks.fetchHealth.mockRejectedValue(
        apiFailure(code, requestId, code === "api_response_invalid" ? 200 : 503),
      );

      renderDashboard();

      expect(await screen.findByText("Partially available")).toBeVisible();
      expect(screen.queryByText("Configured and populated")).not.toBeInTheDocument();
      expect(screen.queryByText("Configured and empty")).not.toBeInTheDocument();
      expect(screen.getAllByText(new RegExp(code)).length).toBeGreaterThan(0);
      expect(screen.getAllByText(new RegExp(requestId)).length).toBeGreaterThan(0);
      expect(screen.getByText("Research A")).toBeVisible();
      expect(screen.getByText("Report A")).toBeVisible();
      expect(screen.getByText("job-queued")).toBeVisible();
    },
  );

  it.each([
    ["api_unavailable", "API unreachable"],
    ["api_response_invalid", "Dependencies unavailable"],
  ])(
    "uses the bounded %s error-only readiness classification",
    async (healthCode, expectedSummary) => {
      apiMocks.fetchDemoWorkspace.mockRejectedValue(
        apiFailure("product_database_unavailable", "identity-failure"),
      );
      apiMocks.fetchHealth.mockRejectedValue(
        apiFailure(healthCode, "health-failure"),
      );
      apiMocks.fetchResearchRuns.mockRejectedValue(
        apiFailure("research_artifact_root_unavailable", "research-failure"),
      );
      apiMocks.fetchEvidenceManifests.mockRejectedValue(
        apiFailure("evidence_artifact_root_unavailable", "evidence-failure"),
      );
      apiMocks.fetchPaperJobs.mockRejectedValue(
        apiFailure("product_database_unavailable", "jobs-failure"),
      );
      apiMocks.fetchPortfolioReviews.mockRejectedValue(
        apiFailure("product_database_unavailable", "portfolio-reviews-failure"),
      );

      renderDashboard();

      expect(await screen.findByText(expectedSummary)).toBeVisible();
      expect(screen.queryByText("Partially available")).not.toBeInTheDocument();
      expect(screen.queryByText("Configured and populated")).not.toBeInTheDocument();
      expect(screen.getAllByText(/health-failure/).length).toBeGreaterThan(0);
    },
  );

  it("retains settled error evidence across readiness, attention, and technical surfaces while retrying", async () => {
    arrangeStandard();
    const healthRetry = deferred<{
      data: { status: "ok"; service: string; api_version: "v1" };
      requestId: string;
    }>();
    apiMocks.fetchHealth
      .mockReset()
      .mockRejectedValueOnce(
        apiFailure("api_unavailable", "health-initial-failure"),
      )
      .mockReturnValueOnce(healthRetry.promise);
    const user = userEvent.setup();

    renderDashboard();

    expect(await screen.findByText("Partially available")).toBeVisible();
    const readiness = screen
      .getByRole("heading", {
        name: "Is the product healthy and configured?",
      })
      .closest("section");
    expect(readiness).not.toBeNull();
    const sourceCard = within(readiness as HTMLElement)
      .getByText("API process", { selector: "strong" })
      .closest("li");
    expect(sourceCard).not.toBeNull();
    expect(
      within(sourceCard as HTMLElement).getByText("api_unavailable"),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(/health-initial-failure/),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "The workspace could not reach the local API through the same-origin gateway.",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Verify FastAPI is running on loopback, then retry.",
      ),
    ).toBeVisible();
    const backendDetail = within(sourceCard as HTMLElement)
      .getByText("Backend detail")
      .closest("details");
    expect(backendDetail).not.toBeNull();
    await user.click(within(sourceCard as HTMLElement).getByText("Backend detail"));
    expect(backendDetail).toHaveAttribute("open");
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Bounded failure: api_unavailable",
      ),
    ).toBeVisible();
    const attention = screen
      .getByRole("heading", {
        name: "Which explicit conditions may need attention?",
      })
      .closest("section");
    expect(attention).not.toBeNull();
    expect(
      within(attention as HTMLElement).getByText(
        "Product dependency needs operator attention",
      ),
    ).toBeVisible();
    const technical = screen
      .getByRole("heading", { name: "Explicit read ownership" })
      .closest("section");
    expect(technical).not.toBeNull();
    expect(
      within(technical as HTMLElement).getByText(
        "Error code: api_unavailable",
      ),
    ).toBeVisible();
    expect(
      within(technical as HTMLElement).getByText(
        "Request health-initial-failure",
      ),
    ).toBeVisible();

    await user.click(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Retry API process",
      }),
    );

    expect(screen.getByText("Partially available")).toBeVisible();
    expect(screen.queryByText("Configured and populated")).not.toBeInTheDocument();
    expect(
      within(sourceCard as HTMLElement).getByText("api_unavailable"),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(/health-initial-failure/),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Bounded failure: api_unavailable",
      ),
    ).toBeVisible();
    expect(backendDetail).toHaveAttribute("open");
    expect(
      within(sourceCard as HTMLElement).getByText(
        "The workspace could not reach the local API through the same-origin gateway.",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Verify FastAPI is running on loopback, then retry.",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByRole("status"),
    ).toHaveTextContent(
      "Checking API process again. Previous error evidence remains visible until the new read finishes.",
    );
    expect(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Retrying API process…",
      }),
    ).toBeDisabled();
    expect(
      within(attention as HTMLElement).getByText(
        "Product dependency needs operator attention",
      ),
    ).toBeVisible();
    expect(
      within(attention as HTMLElement).getByText(
        "A source refresh is pending. Attention continues to reflect the last settled evidence until that read finishes.",
      ),
    ).toBeVisible();
    expect(
      within(technical as HTMLElement).getByText(
        "Error code: api_unavailable",
      ),
    ).toBeVisible();
    expect(
      within(technical as HTMLElement).getByText(
        "Request health-initial-failure",
      ),
    ).toBeVisible();
    expect(
      within(technical as HTMLElement).getByText(
        "Checking API process again. Previous error evidence remains visible until the new read finishes.",
      ),
    ).toBeVisible();
    expect(
      within(technical as HTMLElement).getByRole("button", {
        name: "Retrying API process…",
      }),
    ).toBeDisabled();

    healthRetry.resolve({
      data: { status: "ok", service: "el-psy-quant", api_version: "v1" },
      requestId: "health-recovered",
    });
    expect(await screen.findByText("Configured and populated")).toBeVisible();
    await waitFor(() =>
      expect(
        within(sourceCard as HTMLElement).getByText(
          "The FastAPI process responded. Research, evidence, and product-database readiness are reported separately.",
        ),
      ).toBeVisible(),
    );
    expect(
      within(sourceCard as HTMLElement).queryByText("api_unavailable"),
    ).not.toBeInTheDocument();
    expect(
      within(sourceCard as HTMLElement).queryByText(/health-initial-failure/),
    ).not.toBeInTheDocument();
    expect(
      within(sourceCard as HTMLElement).queryByText(/Previous error evidence/),
    ).not.toBeInTheDocument();
    expect(
      within(sourceCard as HTMLElement).getByText(/health-recovered/),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Refresh API process",
      }),
    ).toBeEnabled();
    expect(
      within(attention as HTMLElement).queryByText(
        "Product dependency needs operator attention",
      ),
    ).not.toBeInTheDocument();
    expect(
      within(technical as HTMLElement).queryByText(
        "Error code: api_unavailable",
      ),
    ).not.toBeInTheDocument();
    expect(
      within(technical as HTMLElement).getByText(
        "Request health-recovered",
      ),
    ).toBeVisible();
  });

  it("keeps prior successful count and request identity visible while refreshing", async () => {
    arrangeStandard();
    const researchRefresh = deferred<{
      data: { runs: typeof researchRuns };
      requestId: string;
    }>();
    apiMocks.fetchResearchRuns
      .mockReset()
      .mockResolvedValueOnce({
        data: { runs: researchRuns },
        requestId: "research-initial-success",
      })
      .mockReturnValueOnce(researchRefresh.promise);
    const user = userEvent.setup();

    renderDashboard();

    const readiness = (
      await screen.findByRole("heading", {
        name: "Is the product healthy and configured?",
      })
    ).closest("section");
    expect(readiness).not.toBeNull();
    const sourceCard = within(readiness as HTMLElement)
      .getByText("Research storage", { selector: "strong" })
      .closest("li");
    expect(sourceCard).not.toBeNull();
    expect(
      await within(sourceCard as HTMLElement).findByText(
        "The request succeeded with 2 source records.",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Request research-initial-success",
      ),
    ).toBeVisible();

    await user.click(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Refresh Research storage",
      }),
    );

    expect(screen.getByText("Configured and populated")).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "The request succeeded with 2 source records.",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Request research-initial-success",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).getByRole("status"),
    ).toHaveTextContent(
      "Refreshing Research storage. Previous successful evidence remains visible until the new read finishes.",
    );
    expect(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Refreshing Research storage…",
      }),
    ).toBeDisabled();

    researchRefresh.resolve({
      data: { runs: [researchRuns[0]] },
      requestId: "research-refreshed-success",
    });
    await waitFor(() =>
      expect(
        within(sourceCard as HTMLElement).getByText(
          "The request succeeded with 1 source records.",
        ),
      ).toBeVisible(),
    );
    expect(
      within(sourceCard as HTMLElement).getByText(
        "Request research-refreshed-success",
      ),
    ).toBeVisible();
    expect(
      within(sourceCard as HTMLElement).queryByText(
        /Previous successful evidence remains visible/,
      ),
    ).not.toBeInTheDocument();
    expect(
      within(sourceCard as HTMLElement).getByRole("button", {
        name: "Refresh Research storage",
      }),
    ).toBeEnabled();
  });

  it("keeps duplicate result rows visible but generates only valid ordered distinct-ID comparisons", async () => {
    arrangeStandard({
      jobs: [
        job("duplicate-result", "run-a", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
        job("result-b", "run-b", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
        job("duplicate-result", "run-c", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
        job("result-c", "run-d", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
        job("result-d", "run-e", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
        job("result-e", "run-f", "succeeded", {
          resultAvailable: true,
          attemptStatus: "succeeded",
        }),
      ],
    });
    const user = userEvent.setup();

    renderDashboard();

    const results = (
      await screen.findByRole("heading", {
        name: "Continue explicit result review",
      })
    ).closest("section");
    expect(results).not.toBeNull();
    const checkboxes = within(results as HTMLElement).getAllByRole("checkbox");
    expect(
      within(results as HTMLElement).queryByRole("link", {
        name: "Open ordered comparison",
      }),
    ).not.toBeInTheDocument();
    expect(
      within(results as HTMLElement).getAllByText("duplicate-result", {
        selector: "code",
      }),
    ).toHaveLength(2);
    expect(
      within(results as HTMLElement)
        .getAllByRole("checkbox")
        .map((checkbox) => checkbox.parentElement?.textContent),
    ).toEqual([
      "duplicate-result · run-a",
      "result-b · run-b",
      "duplicate-result · run-c",
      "result-c · run-d",
      "result-d · run-e",
      "result-e · run-f",
    ]);

    await user.click(checkboxes[1]);
    await user.click(checkboxes[0]);

    const twoResultLink = within(results as HTMLElement).getByRole("link", {
      name: "Open ordered comparison",
    });
    expect(twoResultLink).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-b&job_id=duplicate-result",
    );
    expect(checkboxes[2]).toBeDisabled();
    expect(
      within(results as HTMLElement).getByText(
        "Job ID duplicate-result is already selected from another duplicate backend row.",
      ),
    ).toBeVisible();

    await user.click(checkboxes[3]);
    await user.click(checkboxes[4]);

    const fourResultLink = within(results as HTMLElement).getByRole("link", {
      name: "Open ordered comparison",
    });
    expect(fourResultLink).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-b&job_id=duplicate-result&job_id=result-c&job_id=result-d",
    );
    const selectedIds = new URL(
      `https://dashboard.local${fourResultLink.getAttribute("href")}`,
    ).searchParams.getAll("job_id");
    expect(selectedIds).toEqual([
      "result-b",
      "duplicate-result",
      "result-c",
      "result-d",
    ]);
    expect(comparisonSelectionErrorKey(selectedIds)).toBeNull();
    expect(checkboxes[5]).toBeDisabled();
    expect(
      within(results as HTMLElement).getByText(
        "Four distinct job IDs are selected. Deselect one before choosing result-e.",
      ),
    ).toBeVisible();

    await user.click(checkboxes[0]);
    expect(checkboxes[5]).toBeEnabled();
    await user.click(checkboxes[5]);

    expect(
      within(results as HTMLElement).getByRole("link", {
        name: "Open ordered comparison",
      }),
    ).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-b&job_id=result-c&job_id=result-d&job_id=result-e",
    );
    const order = within(results as HTMLElement).getByRole("list", {
      name: "Explicit comparison selection order",
    });
    expect(
      within(order).getAllByRole("listitem").map((item) => item.textContent),
    ).toEqual(["result-b", "result-c", "result-d", "result-e"]);
    for (const command of ["Run", "Retry", "Recover", "Cancel", "Submit"]) {
      expect(
        within(results as HTMLElement).queryByRole("button", {
          name: command,
        }),
      ).not.toBeInTheDocument();
    }
  });

  it("reconciles refreshed result selection without stale links and preserves remaining click order", async () => {
    const initialJobs = [
      job("result-a", "run-a", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
      job("result-b", "run-b", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
      job("result-c", "run-c", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
      job("result-d", "run-d", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
    ];
    const refreshedJobs = [
      job("result-d", "run-d-new-order", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
      job("result-a", "run-a-new-order", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
      job("result-b", "run-b-unavailable", "succeeded", {
        resultAvailable: false,
        attemptStatus: "succeeded",
      }),
      job("result-e", "run-e", "succeeded", {
        resultAvailable: true,
        attemptStatus: "succeeded",
      }),
    ];
    arrangeStandard({ jobs: initialJobs });
    apiMocks.fetchPaperJobs
      .mockReset()
      .mockResolvedValueOnce({ data: initialJobs, requestId: "jobs-initial" })
      .mockResolvedValueOnce({ data: refreshedJobs, requestId: "jobs-refreshed" });
    const user = userEvent.setup();

    renderDashboard();

    const results = (
      await screen.findByRole("heading", {
        name: "Continue explicit result review",
      })
    ).closest("section");
    expect(results).not.toBeNull();
    const checkboxes = within(results as HTMLElement).getAllByRole("checkbox");
    await user.click(checkboxes[2]);
    await user.click(checkboxes[0]);
    await user.click(checkboxes[1]);
    await user.click(checkboxes[3]);
    expect(
      within(results as HTMLElement).getByRole("link", {
        name: "Open ordered comparison",
      }),
    ).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-c&job_id=result-a&job_id=result-b&job_id=result-d",
    );

    await user.click(
      screen.getByRole("button", { name: "Refresh Paper Job reads" }),
    );

    await waitFor(() =>
      expect(apiMocks.fetchPaperJobs).toHaveBeenCalledTimes(2),
    );
    const refreshedResults = (
      await screen.findByRole("heading", {
        name: "Continue explicit result review",
      })
    ).closest("section");
    expect(refreshedResults).not.toBeNull();
    const reconciledLink = await within(
      refreshedResults as HTMLElement,
    ).findByRole("link", { name: "Open ordered comparison" });
    expect(reconciledLink).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-a&job_id=result-d",
    );
    const remainingIds = new URL(
      `https://dashboard.local${reconciledLink.getAttribute("href")}`,
    ).searchParams.getAll("job_id");
    expect(remainingIds).toEqual(["result-a", "result-d"]);
    expect(comparisonSelectionErrorKey(remainingIds)).toBeNull();
    expect(reconciledLink.getAttribute("href")).not.toContain("result-b");
    expect(reconciledLink.getAttribute("href")).not.toContain("result-c");
  });

  it("uses the exact Demo descriptor journey and localizes it without hardcoded fixture identities", async () => {
    apiMocks.fetchDemoWorkspace.mockResolvedValue({
      data: descriptor,
      requestId: "demo-request",
    });
    apiMocks.fetchHealth.mockResolvedValue({
      data: { status: "ok", service: "el-psy-quant", api_version: "v1" },
      requestId: "health-request",
    });
    apiMocks.fetchResearchRuns.mockResolvedValue({
      data: { runs: researchRuns },
      requestId: "research-request",
    });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({
      data: { manifests },
      requestId: "evidence-request",
    });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs-request" });

    renderDashboard("zh-CN");

    expect(await screen.findByText("Descriptor Demo Name")).toBeVisible();
    expect(screen.getByText("dataset-from-descriptor")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /检查规范策略/ }),
    ).toHaveAttribute("href", "/strategies/strategy-from-descriptor");
    expect(
      screen.getByRole("link", { name: /打开描述符有序对比/ }),
    ).toHaveAttribute(
      "href",
      "/comparisons?job_id=demo-job-b&job_id=demo-job-a",
    );
    expect(screen.getAllByText("proposal-from-descriptor").length).toBeGreaterThan(0);
    expect(screen.getByText("decision-record-from-descriptor")).toBeInTheDocument();
    expect(screen.getByText("submission-from-descriptor")).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /投资组合评审/ }).find((link) =>
        link.getAttribute("href") === "/portfolio-reviews/review-from-descriptor"
      ),
    ).toHaveAttribute(
      "href",
      "/portfolio-reviews/review-from-descriptor",
    );
    expect(
      screen.getByRole("link", { name: /检查确定性的演示市场时间重放/ }),
    ).toHaveAttribute(
      "href",
      "/market-time/replays/replay-from-descriptor",
    );
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(apiMocks.fetchDemoWorkspace).toHaveBeenCalledTimes(1);
  });

  it.each([
    {
      locale: "en" as const,
      heading: "Saved evidence manifests in source order",
      inspect: "Inspect exact manifest",
    },
    {
      locale: "zh-CN" as const,
      heading: "按来源顺序保存的证据清单",
      inspect: "检查精确清单",
    },
  ])(
    "shows complete raw Evidence Manifest identity in $locale without collapsing duplicates",
    async ({ locale, heading, inspect }) => {
      const evidenceRows = [
        ...manifests,
        {
          artifact_key: "artifact-no-label",
          manifest_type: "strategy_decision_manifest" as const,
          manifest_id: "manifest-no-label",
          reference_count: 0,
          created_by: null,
          created_timestamp: null,
          label: null,
          description: null,
        },
      ];
      arrangeStandard({ jobs: [] });
      apiMocks.fetchEvidenceManifests.mockResolvedValue({
        data: { manifests: evidenceRows },
        requestId: "evidence-complete-identity",
      });

      renderDashboard(locale);

      const evidence = (
        await screen.findByRole("heading", { name: heading })
      ).closest("section");
      expect(evidence).not.toBeNull();
      expect(within(evidence as HTMLElement).getByText("Report A")).toBeVisible();
      expect(
        within(evidence as HTMLElement).getByText("Report A duplicate"),
      ).toBeVisible();
      expect(
        within(evidence as HTMLElement).getAllByText("manifest-a", {
          selector: "code",
        }),
      ).toHaveLength(2);
      expect(
        within(evidence as HTMLElement).getAllByText("manifest-no-label"),
      ).toHaveLength(2);
      await waitFor(() =>
        expect(
          within(evidence as HTMLElement).getAllByText("1", {
            selector: "code",
          }),
        ).toHaveLength(3),
      );
      expect(
        within(evidence as HTMLElement).getAllByText(
          "report_artifact_manifest",
          { selector: "code" },
        ),
      ).toHaveLength(2);
      expect(
        within(evidence as HTMLElement).getByText(
          "strategy_decision_manifest",
          { selector: "code" },
        ),
      ).toBeVisible();
      expect(
        within(evidence as HTMLElement).getAllByText("artifact-a", {
          selector: "code",
        }),
      ).toHaveLength(2);
      expect(
        within(evidence as HTMLElement).getByText("artifact-no-label", {
          selector: "code",
        }),
      ).toBeVisible();

      const records = within(evidence as HTMLElement).getAllByRole("listitem");
      expect(records.map((record) => record.textContent?.slice(0, 25))).toEqual([
        expect.stringContaining("Report A"),
        expect.stringContaining("Report A duplicate"),
        expect.stringContaining("manifest-no-label"),
      ]);
      expect(
        within(evidence as HTMLElement)
          .getAllByRole("link", { name: inspect })
          .map((link) => link.getAttribute("href")),
      ).toEqual([
        "/evidence-manifests/report_artifact_manifest/artifact-a",
        "/evidence-manifests/report_artifact_manifest/artifact-a",
        "/evidence-manifests/strategy_decision_manifest/artifact-no-label",
      ]);
      await waitFor(() =>
        expect(apiMocks.fetchEvidenceManifestDetail).toHaveBeenCalledTimes(3),
      );
      expect(apiMocks.fetchEvidenceManifestDetail.mock.calls).toEqual([
        ["report_artifact_manifest", "artifact-a"],
        ["report_artifact_manifest", "artifact-a"],
        ["strategy_decision_manifest", "artifact-no-label"],
      ]);
    },
  );

  it("shows healthy-empty state and only the allow-listed empty-evidence attention condition", async () => {
    arrangeStandard({ jobs: [] });
    apiMocks.fetchResearchRuns.mockResolvedValue({
      data: { runs: [] },
      requestId: "research-empty",
    });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({
      data: { manifests: [] },
      requestId: "evidence-empty",
    });

    renderDashboard();

    expect(await screen.findByText("Configured and empty")).toBeVisible();
    const attention = screen
      .getByRole("heading", {
        name: "Which explicit conditions may need attention?",
      })
      .closest("section");
    expect(attention).not.toBeNull();
    expect(
      within(attention as HTMLElement).getByText(
        "Healthy workspace without research or evidence",
      ),
    ).toBeVisible();
    expect(
      within(attention as HTMLElement).queryByText(/profit|winner|recommend/i),
    ).not.toBeInTheDocument();
  });

  it("renders unknown future job status neutrally while preserving the raw value", () => {
    render(<PaperJobStatusValue value="future_status" />);

    expect(screen.getByText("Unknown job status")).toBeVisible();
    expect(screen.getByText("future_status")).toBeVisible();
    expect(screen.getByText("future_status").closest(".status-badge")).toHaveClass(
      "status-badge--neutral",
    );
  });
});
