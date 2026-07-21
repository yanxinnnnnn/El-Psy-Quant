import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PortfolioReviewCreateView } from "@/components/portfolio-review-create-view";
import { WorkspaceShell } from "@/components/workspace-shell";
import { ApiClientError } from "@/lib/api-client";
import { render, screen, waitFor } from "@/test/render";
import { portfolioReviewDetail } from "@/test/portfolio-review-fixtures";

const apiMocks = vi.hoisted(() => ({
  fetchDemoWorkspace: vi.fn(),
  fetchEvidenceManifestDetail: vi.fn(),
  fetchEvidenceManifests: vi.fn(),
  fetchResearchRuns: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/portfolio-reviews/new",
  useRouter: () => ({ refresh: vi.fn() }),
}));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, ...apiMocks };
});

afterEach(() => vi.unstubAllGlobals());

function renderCreate() {
  Object.values(apiMocks).forEach((mock) => mock.mockReset());
  apiMocks.fetchDemoWorkspace.mockRejectedValue(new ApiClientError({
    status: 404,
    code: "demo_workspace_not_configured",
    publicMessage: "Demo workspace is not configured",
    requestId: "workspace-request",
  }));
  apiMocks.fetchResearchRuns.mockResolvedValue({ data: { runs: [] }, requestId: "research-request" });
  apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence-request" });
  return render(
    <WorkspaceShell>
      <PortfolioReviewCreateView />
    </WorkspaceShell>,
  );
}

function demoReviewRequest() {
  return JSON.parse(
    readFileSync(
      resolve(
        process.cwd(),
        "..",
        "examples",
        "demo_workspace",
        "portfolio_reviews",
        "create-request.json",
      ),
      "utf8",
    ),
  );
}

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "portfolio-create-request",
    },
  });
}

async function completeMinimumForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/^Review ID/), "synthetic-review-175");
  await user.type(screen.getByLabelText(/^Idempotency-Key/), "Synthetic.Create:175");
  await user.type(screen.getByLabelText(/^Source ID/), "synthetic-source-175");
  await user.type(screen.getByLabelText(/^Created by/), "synthetic-founder");
  await user.type(screen.getByLabelText(/^Created timestamp/), "2026-07-20T00:30:00Z");
  await user.type(screen.getByLabelText(/^Evaluation frequency/), "synthetic-daily");

  const componentIds = screen.getAllByLabelText(/^Component ID/);
  const strategyIds = screen.getAllByLabelText(/^Strategy ID/);
  await user.type(componentIds[0], "component-a");
  await user.type(componentIds[1], "component-b");
  await user.type(strategyIds[0], "synthetic-strategy-a");
  await user.type(strategyIds[1], "synthetic-strategy-b");
  const referenceTypes = screen.getAllByLabelText(/^Reference type/);
  const referenceIds = screen.getAllByLabelText(/^Reference ID/);
  await user.selectOptions(referenceTypes[0], "research_run");
  await user.selectOptions(referenceTypes[1], "configured_run");
  await user.type(referenceIds[0], "synthetic-run-a");
  await user.type(referenceIds[1], "synthetic-run-b");

  const timestamps = screen.getAllByLabelText(/^Timestamp/);
  await user.type(timestamps[0], "2026-01-01T00:00:00Z");
  await user.type(timestamps[1], "2026-01-02T00:00:00Z");
  await user.type(timestamps[2], "2026-01-03T00:00:00Z");
  const returnsA = screen.getAllByLabelText(/^Return for component-a/);
  const returnsB = screen.getAllByLabelText(/^Return for component-b/);
  await user.type(returnsA[0], "0.1");
  await user.type(returnsB[0], "-0.1");
  await user.type(returnsA[1], "0.2");
  await user.type(returnsB[1], "-0.2");
  await user.type(returnsA[2], "0.3");
  await user.type(returnsB[2], "-0.3");

  const scenarioIds = screen.getAllByLabelText(/^Scenario ID/);
  const rationales = screen.getAllByLabelText(/^Rationale/);
  await user.type(scenarioIds[0], "synthetic-baseline");
  await user.type(scenarioIds[1], "synthetic-proposed");
  await user.type(rationales[0], "Synthetic baseline rationale");
  await user.type(rationales[1], "Synthetic proposed rationale");
  await user.type(screen.getByLabelText(/^Baseline weight for component-a/), "0.8");
  await user.type(screen.getByLabelText(/^Baseline weight for component-b/), "0.2");
  await user.type(screen.getByLabelText(/^Proposed weight for component-a/), "0.4");
  await user.type(screen.getByLabelText(/^Proposed weight for component-b/), "0.6");
  await user.selectOptions(screen.getByLabelText(/^Proposed component/), "component-b");

  await user.type(screen.getByLabelText(/^Analysis created by/), "synthetic-analyst");
  await user.type(screen.getByLabelText(/^Analysis created timestamp/), "2026-07-20T01:00:00Z");
  await user.click(screen.getByRole("checkbox"));
}

describe("PortfolioReviewCreateView", () => {
  it("builds the exact 2-component/3-observation generated request without normalization", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ outcome: "created", review: portfolioReviewDetail }, 201),
    );
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    renderCreate();
    await completeMinimumForm(user);
    expect(screen.getAllByText("Entered total: 1", { exact: true })).toHaveLength(2);
    await user.click(screen.getByRole("button", { name: "Create review" }));
    expect(await screen.findByRole("heading", {
      name: "Portfolio review created",
    })).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(1);
    const options = fetcher.mock.calls[0][1];
    expect(options?.headers).toMatchObject({
      "Idempotency-Key": "Synthetic.Create:175",
    });
    const body = JSON.parse(String(options?.body));
    expect(body.source.components.map((item: { component_id: string }) => item.component_id)).toEqual([
      "component-a",
      "component-b",
    ]);
    expect(body.source.return_observations).toEqual([
      { timestamp: "2026-01-01T00:00:00Z", component_returns: [0.1, -0.1] },
      { timestamp: "2026-01-02T00:00:00Z", component_returns: [0.2, -0.2] },
      { timestamp: "2026-01-03T00:00:00Z", component_returns: [0.3, -0.3] },
    ]);
    expect(body.baseline_scenario.weights).toEqual({
      "component-a": 0.8,
      "component-b": 0.2,
    });
    expect(body.proposed_scenario.weights).toEqual({
      "component-a": 0.4,
      "component-b": 0.6,
    });
    expect(body.proposed_scenario.proposed_component_id).toBe("component-b");
    expect(body).not.toHaveProperty("confirmation");
    expect(screen.getByRole("link", {
      name: "Inspect authoritative detail",
    })).toHaveAttribute("href", "/portfolio-reviews/synthetic-review-175");
  }, 15_000);

  it("rejects invalid drafts without a request and preserves entered values", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    renderCreate();
    await user.type(screen.getByLabelText(/^Review ID/), "preserved-review");
    await user.type(screen.getAllByLabelText(/Baseline weight/)[0], "1e3");
    await user.click(screen.getByRole("button", { name: "Create review" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No request was sent",
    );
    expect(screen.getByLabelText(/^Review ID/)).toHaveValue("preserved-review");
    expect(screen.getAllByLabelText(/Baseline weight/)[0]).toHaveValue("1e3");
    expect(screen.getAllByText(/strict finite decimal/i)[0]).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("shows exact replay and keeps navigation explicit", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ outcome: "replayed", review: portfolioReviewDetail }, 200),
    );
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    renderCreate();
    await completeMinimumForm(user);
    await user.click(screen.getByRole("button", { name: "Create review" }));

    expect(await screen.findByRole("heading", {
      name: "Portfolio review exactly replayed",
    })).toBeVisible();
    expect(screen.getByRole("link", {
      name: "Inspect authoritative detail",
    })).toHaveAttribute("href", "/portfolio-reviews/synthetic-review-175");
  }, 15_000);

  it("supports the 12-component boundary with stable dependent observation cells", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>());
    const user = userEvent.setup();
    renderCreate();
    const add = screen.getByRole("button", { name: "Add component" });
    for (let index = 0; index < 10; index += 1) {
      await user.click(add);
    }
    expect(screen.getAllByLabelText(/^Component ID/)).toHaveLength(12);
    expect(screen.getAllByLabelText(/Return for Component/)).toHaveLength(36);
    expect(add).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Remove component 12" }));
    await waitFor(() => expect(screen.getAllByLabelText(/^Component ID/)).toHaveLength(11));
    expect(screen.getAllByLabelText(/Return for Component/)).toHaveLength(33);
  });

  it("loads the exact Demo example only after replace confirmation and never submits", async () => {
    Object.values(apiMocks).forEach((mock) => mock.mockReset());
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    apiMocks.fetchDemoWorkspace.mockResolvedValue({
      data: {
        dataset_id: "founder-demo-workspace",
        display_name: "Founder Demo Workspace",
        warning: "DEMO ONLY",
        portfolio_review_example: {
          create_idempotency_key: "demo-portfolio-review-create-v1",
          request: demoReviewRequest(),
        },
      },
      requestId: "demo-descriptor-request",
    });
    apiMocks.fetchResearchRuns.mockResolvedValue({ data: { runs: [] }, requestId: "research" });
    apiMocks.fetchEvidenceManifests.mockResolvedValue({ data: { manifests: [] }, requestId: "evidence" });
    const user = userEvent.setup();
    render(
      <WorkspaceShell>
        <PortfolioReviewCreateView />
      </WorkspaceShell>,
    );

    await user.type(screen.getByLabelText(/^Review ID/), "draft-to-replace");
    const load = await screen.findByRole("button", { name: "Load exact Demo create example" });
    expect(load).toBeDisabled();
    await user.click(screen.getByLabelText(/Replace every current builder value/));
    await user.click(load);

    expect(screen.getByLabelText(/^Review ID/)).toHaveValue("demo-portfolio-review-001");
    expect(screen.getByLabelText(/^Idempotency-Key/)).toHaveValue(
      "demo-portfolio-review-create-v1",
    );
    expect(screen.getAllByLabelText(/^Component ID/).map((input) =>
      (input as HTMLInputElement).value
    )).toEqual(["demo-aapl-sleeve", "demo-msft-sleeve"]);
    expect(screen.getByText(/does not submit/)).toBeVisible();
    expect(fetcher).not.toHaveBeenCalled();
    fetcher.mockResolvedValue(response({
      error: {
        code: "portfolio_review_artifact_root_unavailable",
        message: "Portfolio review artifact root unavailable",
      },
      request_id: "demo-create-failure",
    }, 503));
    await user.click(screen.getByLabelText(/historical scenario inputs for governance review only/));
    await user.click(screen.getByRole("button", { name: "Create review" }));
    expect(
      await screen.findByText(/portfolio_review_artifact_root_unavailable/),
    ).toBeVisible();
    expect(screen.getByLabelText(/^Review ID/)).toHaveValue("demo-portfolio-review-001");
    expect(screen.getByLabelText(/^Idempotency-Key/)).toHaveValue(
      "demo-portfolio-review-create-v1",
    );
  });

  it("applies selected research metadata without changing target financial inputs", async () => {
    renderCreate();
    await screen.findByText(
      "No configured research runs are available. The manual builder remains usable.",
    );
    apiMocks.fetchResearchRuns.mockReset().mockResolvedValue({
      data: {
        runs: [{
          experiment_slug: "founder-research",
          run_id: "run-176",
          experiment_name: "Founder Run",
          strategy: "moving_average_crossover",
          data_source: "cache",
          symbols: ["AAPL", "MSFT"],
        }],
      },
      requestId: "research-176",
    });
    const user = userEvent.setup();
    await user.click(screen.getAllByRole("button", { name: "Refresh" })[0]);
    await user.type(screen.getAllByLabelText(/^Component ID/)[0], "preserved-component");
    await user.type(screen.getAllByLabelText(/Baseline weight/)[0], "0.75");
    await user.type(screen.getAllByLabelText(/Return for preserved-component/)[0], "0.012");
    const researchTarget = screen.getByLabelText(
      "Explicit target component",
    ) as HTMLSelectElement;
    await user.selectOptions(researchTarget, researchTarget.options[1]);
    await user.selectOptions(
      screen.getByLabelText("Choose one research run explicitly"),
      await screen.findByRole("option", { name: /founder-research\/run-176/ }),
    );
    await user.click(screen.getByRole("button", { name: "Apply to selected component" }));

    expect(screen.getAllByLabelText(/^Component ID/)[0]).toHaveValue("preserved-component");
    expect(screen.getAllByLabelText(/^Strategy ID/)[0]).toHaveValue(
      "moving_average_crossover",
    );
    expect(screen.getAllByLabelText(/Baseline weight/)[0]).toHaveValue("0.75");
    expect(screen.getAllByLabelText(/Return for preserved-component/)[0]).toHaveValue("0.012");
    expect(screen.getAllByLabelText(/^Reference type/).some((input) =>
      (input as HTMLSelectElement).value === "research_run"
    )).toBe(true);
    expect(screen.getAllByLabelText(/^Reference ID/).some((input) =>
      (input as HTMLInputElement).value === "founder-research/run-176"
    )).toBe(true);
  });

  it("keeps the prior research list and complete draft visible after manual refresh failure", async () => {
    Object.values(apiMocks).forEach((mock) => mock.mockReset());
    apiMocks.fetchDemoWorkspace.mockRejectedValue(new ApiClientError({
      status: 404,
      code: "demo_workspace_not_configured",
      publicMessage: "Demo workspace is not configured",
      requestId: "workspace-request",
    }));
    apiMocks.fetchResearchRuns.mockResolvedValue({
      data: {
        runs: [{
          experiment_slug: "preserved-experiment",
          run_id: "preserved-run",
          experiment_name: "Preserved Research",
          strategy: "moving_average_crossover",
          data_source: "cache",
          symbols: ["AAPL"],
        }],
      },
      requestId: "research-success",
    });
    apiMocks.fetchEvidenceManifests.mockRejectedValue(new ApiClientError({
      status: 503,
      code: "evidence_artifact_root_unavailable",
      publicMessage: "Evidence root unavailable",
      requestId: "evidence-failure",
    }));
    const user = userEvent.setup();
    render(
      <WorkspaceShell>
        <PortfolioReviewCreateView />
      </WorkspaceShell>,
    );
    expect(await screen.findByRole("option", { name: /preserved-experiment\/preserved-run/ })).toBeVisible();
    expect(await screen.findByText(/evidence_artifact_root_unavailable/)).toBeVisible();
    await user.type(screen.getByLabelText(/^Review ID/), "draft-survives-refresh");
    await user.type(screen.getAllByLabelText(/^Component ID/)[0], "draft-component");
    apiMocks.fetchResearchRuns.mockReset().mockRejectedValue(new ApiClientError({
      status: 503,
      code: "research_artifact_root_unavailable",
      publicMessage: "Research root unavailable",
      requestId: "research-refresh-failure",
    }));
    await user.click(screen.getAllByRole("button", { name: "Refresh" })[0]);

    expect(await screen.findByText(/research_artifact_root_unavailable/)).toBeVisible();
    expect(screen.getByRole("option", { name: /preserved-experiment\/preserved-run/ })).toBeVisible();
    expect(screen.getByLabelText(/^Review ID/)).toHaveValue("draft-survives-refresh");
    expect(screen.getAllByLabelText(/^Component ID/)[0]).toHaveValue("draft-component");
  });

  it("shows unsupported manifest references and refuses duplicate compatible imports", async () => {
    renderCreate();
    await screen.findByText(
      "No evidence manifests are available. The manual builder remains usable.",
    );
    apiMocks.fetchEvidenceManifests.mockReset().mockResolvedValue({
      data: {
        manifests: [{
          manifest_type: "report_artifact_manifest",
          artifact_key: "report-176",
          manifest_id: "manifest-176",
          reference_count: 2,
          created_by: null,
          created_timestamp: null,
          label: null,
          description: null,
        }],
      },
      requestId: "evidence-176",
    });
    apiMocks.fetchEvidenceManifestDetail.mockResolvedValue({
      data: {
        manifest_type: "report_artifact_manifest",
        artifact_key: "report-176",
        schema_version: 1,
        manifest_id: "manifest-176",
        references: [
          {
            schema_version: 1,
            reference_type: "report_artifact_summary",
            reference_id: "summary-176",
            label: "Compatible summary",
            description: "Exact public evidence pointer",
          },
          {
            schema_version: 1,
            reference_type: "unsupported_reference_type",
            reference_id: "unsupported-176",
            label: null,
            description: null,
          },
        ],
        label: null,
        description: null,
        created_by: null,
        created_timestamp: null,
        notes: null,
      },
      requestId: "detail-176",
    });
    const user = userEvent.setup();
    await user.click(screen.getAllByRole("button", { name: "Refresh" })[1]);
    const manifestTarget = screen.getByLabelText(
      "Explicit target component",
    ) as HTMLSelectElement;
    await user.selectOptions(manifestTarget, manifestTarget.options[1]);
    await user.selectOptions(
      screen.getByLabelText("Choose one evidence manifest explicitly"),
      await screen.findByRole("option", { name: /report-176/ }),
    );
    const supported = (await screen.findAllByText("report_artifact_summary")).find(
      (element) => element.tagName === "CODE",
    );
    if (supported === undefined) {
      throw new Error("supported manifest reference missing");
    }
    expect(supported).toBeVisible();
    const unsupported = screen.getByText("unsupported_reference_type");
    expect(unsupported).toBeVisible();
    apiMocks.fetchEvidenceManifestDetail.mockReset().mockRejectedValue(
      new ApiClientError({
        status: 404,
        code: "evidence_manifest_not_found",
        publicMessage: "Manifest not found",
        requestId: "detail-refresh-failure",
      }),
    );
    await user.click(screen.getByRole("button", {
      name: "Refresh selected manifest detail",
    }));
    expect(await screen.findByText(/evidence_manifest_not_found/)).toBeVisible();
    expect(screen.getByText("unsupported_reference_type")).toBeVisible();
    const supportedCheck = supported.closest("label")?.querySelector("input");
    const unsupportedCheck = unsupported.closest("label")?.querySelector("input");
    expect(unsupportedCheck).toBeDisabled();
    if (supportedCheck === null || supportedCheck === undefined) {
      throw new Error("supported reference checkbox missing");
    }
    await user.click(supportedCheck);
    await user.click(screen.getByRole("button", { name: "Add selected compatible references" }));
    expect(await screen.findByText(/Added 1 compatible reference/)).toBeVisible();
    const countAfterFirst = screen.getAllByLabelText(/^Reference ID/).length;
    await user.click(screen.getByRole("button", { name: "Add selected compatible references" }));
    expect(await screen.findByText(/Duplicate reference refused/)).toBeVisible();
    expect(screen.getAllByLabelText(/^Reference ID/)).toHaveLength(countAfterFirst);
  });
});
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
