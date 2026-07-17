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

const apiMocks = vi.hoisted(() => ({
  fetchDemoWorkspace: vi.fn(),
  fetchEvidenceManifests: vi.fn(),
  fetchHealth: vi.fn(),
  fetchPaperJobs: vi.fn(),
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
  schema_version: 1,
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
};

function notConfigured() {
  return new ApiClientError({
    status: 404,
    code: "demo_workspace_not_configured",
    publicMessage: "Demo workspace is not configured",
    requestId: "identity-request",
  });
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

  it("creates an explicit repeated ordered comparison URL and preserves duplicate selections", async () => {
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

    await user.click(checkboxes[1]);
    await user.click(checkboxes[0]);
    await user.click(checkboxes[2]);

    expect(
      within(results as HTMLElement).getByRole("link", {
        name: "Open ordered comparison",
      }),
    ).toHaveAttribute(
      "href",
      "/comparisons?job_id=result-b&job_id=duplicate-result&job_id=duplicate-result",
    );
    const order = within(results as HTMLElement).getByRole("list", {
      name: "Explicit comparison selection order",
    });
    expect(
      within(order).getAllByRole("listitem").map((item) => item.textContent),
    ).toEqual(["result-b", "duplicate-result", "duplicate-result"]);
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
    expect(apiMocks.fetchDemoWorkspace).toHaveBeenCalledTimes(1);
  });

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
