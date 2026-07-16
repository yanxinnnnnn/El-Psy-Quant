import { render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EvidenceManifestDetailView } from "./evidence-manifest-detail-view";
import { EvidenceManifestListView } from "./evidence-manifest-list-view";

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

const reference = {
  schema_version: 1 as const,
  reference_type: "research_summary",
  reference_id: "duplicate-ref",
  label: null,
  description: null,
};

const commonDetail = {
  artifact_key: "artifact-1",
  schema_version: 1 as const,
  manifest_id: "manifest-1",
  created_by: null,
  created_timestamp: null,
  description: null,
};

describe("EvidenceManifestListView", () => {
  it("uses one loading status region then preserves backend order and nullable fields", async () => {
    let resolveFetch: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
      () => new Promise<Response>((resolve) => { resolveFetch = resolve; }),
    );
    vi.stubGlobal("fetch", fetcher);

    render(<EvidenceManifestListView />);
    const statuses = screen.getAllByRole("status");
    expect(statuses).toHaveLength(1);
    expect(statuses[0]).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Loading configured evidence manifests…")).not.toHaveAttribute(
      "role",
    );

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    resolveFetch?.(apiResponse({
      manifests: [
        {
          manifest_type: "strategy_decision_manifest",
          artifact_key: "decision-1",
          manifest_id: "manifest-decision",
          reference_count: 2,
          created_by: "founder",
          created_timestamp: "2026-07-15T10:00:00Z",
          label: null,
          description: "Decision evidence",
        },
        {
          manifest_type: "report_artifact_manifest",
          artifact_key: "report-1",
          manifest_id: "manifest-report",
          reference_count: 1,
          created_by: null,
          created_timestamp: null,
          label: "Daily report",
          description: null,
        },
      ],
    }));

    await screen.findByRole("heading", { name: "Strategy decision" });
    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings.map((heading) => heading.textContent)).toEqual([
      "Strategy decision",
      "Report artifact",
    ]);
    expect(screen.getByText("manifest-decision")).toBeVisible();
    expect(screen.getAllByText("Not available").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "Inspect manifest" })[0]).toHaveAttribute(
      "href",
      "/evidence-manifests/strategy_decision_manifest/decision-1",
    );
  });

  it("distinguishes a successful empty configured root", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(apiResponse({ manifests: [] })),
    );
    render(<EvidenceManifestListView />);
    expect(
      await screen.findByRole("heading", { name: "The configured evidence root is empty" }),
    ).toBeVisible();
  });

  it.each([
    ["evidence_artifact_root_unavailable", "Evidence root unavailable", 503],
    ["evidence_artifact_invalid", "Evidence artifacts are invalid", 422],
  ])("maps and retries bounded %s failures", async (code, heading, status) => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(apiResponse(
        { error: { code, message: "Safe evidence error" }, request_id: "body-id" },
        { status, requestId: "header-id" },
      ))
      .mockResolvedValueOnce(apiResponse({ manifests: [] }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<EvidenceManifestListView />);
    const alert = await screen.findByRole("alert");
    expect(screen.getByRole("heading", { name: heading })).toBeVisible();
    expect(alert).toHaveTextContent("Safe evidence error");
    expect(screen.getByText("Request header-id")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(
      await screen.findByRole("heading", { name: "The configured evidence root is empty" }),
    ).toBeVisible();
  });

  it("uses a neutral bounded failure for transport errors and retries", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("C:\\private\\evidence"))
      .mockResolvedValueOnce(apiResponse({ manifests: [] }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<EvidenceManifestListView />);
    const alert = await screen.findByRole("alert");
    expect(screen.getByRole("heading", { name: "Evidence manifests unavailable" })).toBeVisible();
    expect(alert).toHaveTextContent("The local API is unavailable.");
    expect(alert).not.toHaveTextContent("private");
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(
      await screen.findByRole("heading", { name: "The configured evidence root is empty" }),
    ).toBeVisible();
  });
});

describe("EvidenceManifestDetailView", () => {
  it("renders decision groups in order and preserves duplicate unresolved pointers", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(apiResponse({
      ...commonDetail,
      manifest_type: "strategy_decision_manifest",
      summary_references: [reference, reference],
      record_references: [{ ...reference, reference_id: "record-ref" }],
    })));

    render(<EvidenceManifestDetailView manifestType="strategy_decision_manifest" artifactKey="artifact-1" />);
    expect(await screen.findByRole("heading", { name: "Strategy decision", level: 1 })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Summary references" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Record references" })).toBeVisible();
    const duplicateReferences = screen.getAllByText("duplicate-ref");
    expect(duplicateReferences).toHaveLength(2);
    expect(duplicateReferences.every((item) => item.closest("a") === null)).toBe(true);
    expect(screen.getAllByText("Not available").length).toBeGreaterThanOrEqual(7);
  });

  it("renders report label, notes, and references with null-safe values", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(apiResponse({
      ...commonDetail,
      manifest_type: "report_artifact_manifest",
      references: [reference],
      label: null,
      notes: null,
    })));

    render(<EvidenceManifestDetailView manifestType="report_artifact_manifest" artifactKey="artifact-1" />);
    expect(await screen.findByRole("heading", { name: "Report artifact", level: 1 })).toBeVisible();
    const reportDetails = screen.getByRole("heading", { name: "Report details" }).closest("section");
    expect(reportDetails).not.toBeNull();
    expect(within(reportDetails as HTMLElement).getAllByText("Not available")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "References" })).toBeVisible();
  });

  it("renders all workflow reference groups", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(apiResponse({
      ...commonDetail,
      manifest_type: "strategy_review_workflow_manifest",
      state_snapshot_references: [reference],
      transition_proposal_references: [],
      transition_record_references: [reference],
    })));

    render(<EvidenceManifestDetailView manifestType="strategy_review_workflow_manifest" artifactKey="artifact-1" />);
    expect(await screen.findByRole("heading", { name: "Strategy review workflow", level: 1 })).toBeVisible();
    for (const heading of [
      "State snapshot references",
      "Transition proposal references",
      "Transition record references",
    ]) {
      expect(screen.getByRole("heading", { name: heading })).toBeVisible();
    }
    expect(screen.getByText("No references in this group.")).toBeVisible();
  });

  it("renders bounded not-found state with request ID and back link", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(apiResponse(
      {
        error: { code: "evidence_manifest_not_found", message: "Evidence manifest not found" },
        request_id: "body-id",
      },
      { status: 404, requestId: "header-id" },
    )));

    render(<EvidenceManifestDetailView manifestType="report_artifact_manifest" artifactKey="missing" />);
    expect(await screen.findByRole("heading", { name: "Evidence manifest not found" })).toBeVisible();
    expect(screen.getByText("Request header-id")).toBeVisible();
    expect(screen.getByRole("link", { name: "Return to evidence manifests" })).toHaveAttribute(
      "href",
      "/evidence-manifests",
    );
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });
});
