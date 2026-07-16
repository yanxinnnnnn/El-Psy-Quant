import { render, screen, waitFor } from "@/test/render";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FounderFirstRunPanel } from "@/components/founder-first-run-panel";
import { WorkspaceShell } from "@/components/workspace-shell";
import {
  ApiClientError,
  type DemoWorkspaceDescriptorResponse,
} from "@/lib/api-client";

const apiMocks = vi.hoisted(() => ({
  fetchDemoWorkspace: vi.fn(),
  fetchEvidenceManifests: vi.fn(),
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
  proposal_id: "proposal-from-api",
  source_snapshot: {
    snapshot_id: "snapshot-from-api",
    strategy_id: "moving_average_crossover",
    lifecycle_state: "research_review",
    rationale: "Demo source",
    declared_by: "demo-founder",
    declared_timestamp: "2026-01-17T12:00:00Z",
    notes: [],
    warnings: ["Demo only"],
  },
  target_state: "paper_review",
  rationale: "Request review",
  evidence_references: [],
  requested_by: "demo-founder",
  requested_timestamp: "2026-01-17T12:05:00Z",
  notes: [],
  warnings: ["Non-executing"],
};

const descriptor: DemoWorkspaceDescriptorResponse = {
  schema_version: 1,
  dataset_id: "dataset-from-api",
  dataset_version: 1,
  display_name: "Founder Demo Workspace",
  warning: "Disposable example evidence, not real user data.",
  canonical_strategy_name: "strategy-from-api",
  research_run: { experiment_slug: "experiment-from-api", run_id: "run-from-api" },
  evidence_manifests: [
    { manifest_type: "report_artifact_manifest", artifact_key: "report-from-api" },
    { manifest_type: "strategy_decision_manifest", artifact_key: "decision-from-api" },
    { manifest_type: "strategy_review_workflow_manifest", artifact_key: "review-from-api" },
  ],
  paper_jobs: [
    { job_id: "job-from-api-a", run_id: "paper-run-a" },
    { job_id: "job-from-api-b", run_id: "paper-run-b" },
  ],
  comparison_candidate_job_ids: ["job-from-api-a", "job-from-api-b"],
  lifecycle_proposal_example: proposal,
  lifecycle_review_example: {
    transition_record_id: "record-from-api",
    proposal,
    review_outcome: "deferred",
    rationale: "More evidence required",
    resulting_snapshot: null,
    reviewed_by: "demo-founder",
    reviewed_timestamp: "2026-01-17T12:10:00Z",
    notes: [],
    warnings: ["No transition applied"],
  },
  paper_job_submission_example: {
    idempotency_key: "submission-from-api",
    request: {
      run_id: "submission-run-from-api",
      created_timestamp: "2026-01-18T14:00:00Z",
      starting_account_state: {
        timestamp: "2026-01-18T13:55:00Z",
        starting_cash: 50000,
        current_cash: 50000,
        positions: {},
      },
      ending_account_state: {
        timestamp: "2026-01-18T14:05:00Z",
        starting_cash: 50000,
        current_cash: 50000,
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
    requestId: "workspace-request",
  });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("FounderFirstRunPanel", () => {
  it("renders persistent Demo identity and exact descriptor-provided journey links", async () => {
    apiMocks.fetchDemoWorkspace.mockResolvedValue({ data: descriptor, requestId: "demo-request" });

    render(<WorkspaceShell><FounderFirstRunPanel /></WorkspaceShell>);

    expect(await screen.findByText("Demo Workspace")).toBeVisible();
    expect(screen.getByLabelText(/Demo Workspace: disposable example evidence/)).toBeVisible();
    expect(await screen.findByRole("heading", { name: "Strategy to human decision evidence" })).toBeVisible();
    expect(screen.getByRole("link", { name: /Review the canonical strategy definition/ })).toHaveAttribute(
      "href",
      "/strategies/strategy-from-api",
    );
    expect(screen.getByRole("link", { name: /Compare the two ordered demo results/ })).toHaveAttribute(
      "href",
      "/comparisons?job_id=job-from-api-a&job_id=job-from-api-b",
    );
    expect(apiMocks.fetchResearchRuns).not.toHaveBeenCalled();
  });

  it("explains a healthy standard workspace with no loaded evidence", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
    apiMocks.fetchResearchRuns.mockResolvedValue({ data: { runs: [] }, requestId: "research" });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs" });

    render(<FounderFirstRunPanel />);

    expect(await screen.findByRole("heading", { name: /application is running, but no workspace evidence/ })).toBeVisible();
    expect(screen.getByText(/Empty is a valid first-run state/)).toBeVisible();
    expect(screen.getByText(/never seeds data, writes artifacts, or initializes storage/)).toBeVisible();
  });

  it("distinguishes unavailable workspace data from an empty standard workspace", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
    apiMocks.fetchResearchRuns.mockRejectedValue(new ApiClientError({
      status: 503,
      code: "research_artifact_root_unavailable",
      publicMessage: "Research artifact root is unavailable",
      requestId: "research-failure",
    }));
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs" });

    render(<FounderFirstRunPanel />);

    expect(await screen.findByRole("heading", { name: "Workspace data is unavailable, not empty" })).toBeVisible();
    expect(screen.getByText("Research artifact root is unavailable")).toBeVisible();
    await waitFor(() => expect(screen.getByText("Request research-failure")).toBeVisible());
  });
});
