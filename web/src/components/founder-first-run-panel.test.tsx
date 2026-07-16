import { render, screen, waitFor, within } from "@/test/render";
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

function evidenceJourneyLinks(): HTMLAnchorElement[] {
  return screen.getAllByRole("link").filter(
    (link): link is HTMLAnchorElement => link instanceof HTMLAnchorElement && link.pathname.startsWith("/evidence-manifests/"),
  );
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
    expect(screen.getAllByText("Demo only — disposable example evidence, not real user data or trading advice.")).toHaveLength(2);
    expect(screen.queryByText(descriptor.warning)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review the canonical strategy definition/ })).toHaveAttribute(
      "href",
      "/strategies/strategy-from-api",
    );
    const manifestLinks = evidenceJourneyLinks();
    expect(manifestLinks.map((link) => link.getAttribute("href"))).toEqual([
      "/evidence-manifests/report_artifact_manifest/report-from-api",
      "/evidence-manifests/strategy_decision_manifest/decision-from-api",
      "/evidence-manifests/strategy_review_workflow_manifest/review-from-api",
    ]);
    for (const [index, [label, rawType]] of [
      ["3. Inspect report artifact manifest", "report_artifact_manifest"],
      ["4. Inspect strategy decision manifest", "strategy_decision_manifest"],
      ["5. Inspect strategy review workflow manifest", "strategy_review_workflow_manifest"],
    ].entries()) {
      expect(within(manifestLinks[index]).getByText(label)).toBeVisible();
      expect(within(manifestLinks[index]).getByText(rawType, { selector: "code" })).toBeVisible();
    }
    expect(screen.getByRole("link", { name: /Compare the two ordered demo results/ })).toHaveAttribute(
      "href",
      "/comparisons?job_id=job-from-api-a&job_id=job-from-api-b",
    );
    expect(apiMocks.fetchResearchRuns).not.toHaveBeenCalled();
  });

  it("localizes the Demo header and guided journey in Simplified Chinese without mutating descriptor identities", async () => {
    apiMocks.fetchDemoWorkspace.mockResolvedValue({ data: descriptor, requestId: "demo-request" });

    render(<WorkspaceShell><FounderFirstRunPanel /></WorkspaceShell>, { locale: "zh-CN" });

    expect(await screen.findByLabelText("演示工作区：可丢弃的示例证据，并非真实用户数据")).toBeVisible();
    expect(screen.getAllByText("仅供演示——可丢弃的示例证据，不是真实用户数据，也不构成交易建议。")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "从策略到人工决策证据" })).toBeVisible();
    expect(screen.getByRole("link", { name: /审查规范策略定义/ })).toHaveAttribute(
      "href",
      "/strategies/strategy-from-api",
    );
    const manifestLinks = evidenceJourneyLinks();
    expect(manifestLinks.map((link) => link.getAttribute("href"))).toEqual([
      "/evidence-manifests/report_artifact_manifest/report-from-api",
      "/evidence-manifests/strategy_decision_manifest/decision-from-api",
      "/evidence-manifests/strategy_review_workflow_manifest/review-from-api",
    ]);
    for (const [index, [label, rawType]] of [
      ["3. 检查报告制品清单", "report_artifact_manifest"],
      ["4. 检查策略决策清单", "strategy_decision_manifest"],
      ["5. 检查策略审查工作流清单", "strategy_review_workflow_manifest"],
    ].entries()) {
      expect(within(manifestLinks[index]).getByText(label)).toBeVisible();
      expect(within(manifestLinks[index]).getByText(rawType, { selector: "code" })).toBeVisible();
    }
    expect(screen.getByRole("link", { name: /对比两个有序演示结果/ })).toHaveAttribute(
      "href",
      "/comparisons?job_id=job-from-api-a&job_id=job-from-api-b",
    );
    expect(screen.getByText("每个链接都来自经过验证的后端描述符。浏览器中没有硬编码演示身份或证据载荷。")).toBeVisible();
    expect(screen.queryByText(/固件身份/)).not.toBeInTheDocument();
    expect(screen.queryByText(descriptor.warning)).not.toBeInTheDocument();
  });

  it.each([
    ["en", "3. Inspect evidence manifest"],
    ["zh-CN", "3. 检查证据清单"],
  ] as const)("uses the bounded %s manifest fallback while preserving an unknown raw type and artifact link", async (locale, label) => {
    const rawManifestType = "future_manifest_type";
    const unknownDescriptor = {
      ...descriptor,
      evidence_manifests: [
        { manifest_type: rawManifestType, artifact_key: "future-artifact-key" },
      ],
    } as unknown as DemoWorkspaceDescriptorResponse;
    apiMocks.fetchDemoWorkspace.mockResolvedValue({ data: unknownDescriptor, requestId: "demo-request" });

    render(<FounderFirstRunPanel />, { locale });

    const localizedLabel = await screen.findByText(label);
    const link = localizedLabel.closest("a");
    expect(link).not.toBeNull();
    expect(link).toHaveAttribute(
      "href",
      "/evidence-manifests/future_manifest_type/future-artifact-key",
    );
    expect(within(link as HTMLAnchorElement).getByText(rawManifestType, { selector: "code" })).toBeVisible();
  });

  it("explains a healthy standard workspace with no loaded evidence", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
    apiMocks.fetchResearchRuns.mockResolvedValue({ data: { runs: [] }, requestId: "research" });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs" });

    render(<WorkspaceShell><FounderFirstRunPanel /></WorkspaceShell>);

    expect(await screen.findByRole("heading", { name: /application is running, but no workspace evidence/ })).toBeVisible();
    expect(screen.getByRole("status", { name: "Workspace environment: paper trading" })).toHaveTextContent("Paper environment");
    expect(screen.queryByText("Demo Workspace")).not.toBeInTheDocument();
    expect(screen.getByText(/Empty is a valid first-run state/)).toBeVisible();
    expect(screen.getByText(/never seeds data, writes artifacts, or initializes storage/)).toBeVisible();
  });

  it("keeps a healthy empty Standard Workspace distinct in Simplified Chinese", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
    apiMocks.fetchResearchRuns.mockResolvedValue({ data: { runs: [] }, requestId: "research" });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs" });

    render(<FounderFirstRunPanel />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "应用正在运行，但尚未加载工作区证据。" })).toBeVisible();
    expect(screen.getByText(/暂无数据是有效的首次运行状态/)).toBeVisible();
    expect(screen.queryByText("错误码：demo_workspace_not_configured")).not.toBeInTheDocument();
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

    expect(await screen.findByRole("heading", { name: "Research artifact root unavailable" })).toBeVisible();
    expect(screen.getByText("The configured research artifact root could not be inspected.")).toBeVisible();
    expect(screen.getByText("Verify the configured research storage and retry without deleting data.")).toBeVisible();
    expect(screen.getByText("Error code: research_artifact_root_unavailable")).toBeVisible();
    expect(screen.getByText("Research artifact root is unavailable").closest("details")).not.toBeNull();
    await waitFor(() => expect(screen.getByText("Request research-failure")).toBeVisible());
  });

  it("localizes a Demo discovery failure while preserving its stable code, request ID, and safe backend detail", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(new ApiClientError({
      status: 503,
      code: "demo_workspace_unavailable",
      publicMessage: "Demo descriptor is unavailable",
      requestId: "demo-failure",
    }));

    render(<FounderFirstRunPanel />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "演示工作区不可用" })).toBeVisible();
    expect(screen.getByText("无法从已配置的隔离工作区读取演示描述符。")).toBeVisible();
    expect(screen.getByText("请确认隔离演示工作区已启动，然后重试工作区识别。")).toBeVisible();
    expect(screen.getByText("错误码：demo_workspace_unavailable")).toBeVisible();
    expect(screen.getByText("请求 demo-failure")).toBeVisible();
    expect(screen.getByText("Demo descriptor is unavailable").closest("details")).not.toBeNull();
    expect(screen.getByRole("button", { name: "重试工作区识别" })).toBeVisible();
  });

  it("localizes an unavailable Standard evidence root without treating it as an empty workspace", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(notConfigured());
    apiMocks.fetchResearchRuns.mockRejectedValue(new ApiClientError({
      status: 503,
      code: "evidence_artifact_root_unavailable",
      publicMessage: "Evidence artifact root is unavailable",
      requestId: "evidence-failure",
    }));
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    apiMocks.fetchPaperJobs.mockResolvedValue({ data: [], requestId: "jobs" });

    render(<FounderFirstRunPanel />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "证据根目录不可用" })).toBeVisible();
    expect(screen.getByText("无法检查已配置的证据制品目录。")).toBeVisible();
    expect(screen.getByText("错误码：evidence_artifact_root_unavailable")).toBeVisible();
    expect(screen.getByText("请求 evidence-failure")).toBeVisible();
    expect(screen.getByText("Evidence artifact root is unavailable").closest("details")).not.toBeNull();
    expect(screen.queryByRole("heading", { name: /尚未加载工作区证据/ })).not.toBeInTheDocument();
  });

  it("uses the bounded localized fallback for an unknown Demo error code", async () => {
    apiMocks.fetchDemoWorkspace.mockRejectedValue(new ApiClientError({
      status: 503,
      code: "unexpected_demo_failure",
      publicMessage: "Safe unknown backend message",
      requestId: "unknown-failure",
    }));

    render(<FounderFirstRunPanel />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "工作区身份不可用" })).toBeVisible();
    expect(screen.getByText("无法通过本地 API 边界完成该请求。")).toBeVisible();
    expect(screen.getByText("请确认本地服务状态，然后重试请求。")).toBeVisible();
    expect(screen.getByText("错误码：unexpected_demo_failure")).toBeVisible();
    expect(screen.getByText("Safe unknown backend message").closest("details")).not.toBeNull();
  });
});
