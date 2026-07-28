import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { fireEvent, render, screen, waitFor, within } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LifecycleReviewWorkspace } from "@/components/lifecycle-review-workspace";
import type {
  DemoWorkspaceDescriptorResponse,
  LifecycleTransitionProposalResponse,
  LifecycleTransitionReviewResponse,
} from "@/lib/api-client";

function demoSourceJson(relativePath: string): Record<string, unknown> {
  return JSON.parse(
    readFileSync(resolve(process.cwd(), "..", "examples", "demo_workspace", relativePath), "utf8"),
  ) as Record<string, unknown>;
}

function demoDescriptorFromVersionedSource(): DemoWorkspaceDescriptorResponse {
  const manifest = demoSourceJson("workspace-manifest.json");
  const jobs = manifest.paper_jobs as Array<{ job_id: string; run_id: string }>;
  const submission = manifest.paper_submission_example as { idempotency_key: string };
  const portfolioReview = manifest.portfolio_review_example as {
    create_idempotency_key: string;
  };
  const paperAccount = demoSourceJson("paper_accounts/account-journey.json");
  const paperAccountExpected = paperAccount.expected as Record<string, unknown>;
  const marketTime = demoSourceJson("market_time/replay-journey.json");
  const marketTimeCalendar = marketTime.calendar as Record<string, unknown>;
  const marketTimeSessions = marketTime.sessions as Array<Record<string, unknown>>;
  const marketTimeExpected = marketTime.expected as Record<string, unknown>;
  return {
    schema_version: manifest.schema_version as 4,
    dataset_id: manifest.dataset_id as string,
    dataset_version: manifest.dataset_version as number,
    display_name: manifest.display_name as string,
    warning: manifest.warning as string,
    canonical_strategy_name: manifest.canonical_strategy_name as string,
    research_run: manifest.research_run as DemoWorkspaceDescriptorResponse["research_run"],
    evidence_manifests: manifest.evidence_manifests as DemoWorkspaceDescriptorResponse["evidence_manifests"],
    paper_jobs: jobs.map(({ job_id, run_id }) => ({ job_id, run_id })),
    comparison_candidate_job_ids: manifest.comparison_candidate_job_ids as string[],
    lifecycle_proposal_example: demoSourceJson("lifecycle_records/proposal-request.json") as DemoWorkspaceDescriptorResponse["lifecycle_proposal_example"],
    lifecycle_review_example: demoSourceJson("lifecycle_records/human-review-request.json") as DemoWorkspaceDescriptorResponse["lifecycle_review_example"],
    paper_job_submission_example: {
      idempotency_key: submission.idempotency_key,
      request: demoSourceJson("paper_artifacts/submission-example.json") as DemoWorkspaceDescriptorResponse["paper_job_submission_example"]["request"],
    },
    portfolio_review_example: {
      create_idempotency_key: portfolioReview.create_idempotency_key,
      request: demoSourceJson("portfolio_reviews/create-request.json") as DemoWorkspaceDescriptorResponse["portfolio_review_example"]["request"],
    },
    paper_account: {
      account_id: paperAccount.account_id as string,
      head_version: paperAccountExpected.head_version as number,
      event_types: paperAccountExpected.event_types as DemoWorkspaceDescriptorResponse["paper_account"]["event_types"],
      snapshot_id: paperAccountExpected.snapshot_id as string,
      reconciliation_id: paperAccountExpected.reconciliation_id as string,
    },
    market_time: {
      calendar_id: marketTimeCalendar.id as string,
      session_ids: marketTimeSessions.map(({ id }) => id as string),
      replay_id: marketTime.replay_id as string,
      event_count: (marketTime.events as unknown[]).length,
      event_stream_digest: marketTimeExpected.event_stream_digest as string,
      checkpoint: {
        status: marketTimeExpected.checkpoint_status as "paused",
        position: marketTimeExpected.checkpoint_position as number,
        last_event_id: marketTimeExpected.checkpoint_last_event_id as string,
        current_time: marketTimeExpected.checkpoint_current_time as string,
      },
      recovery: {
        remaining_event_ids: marketTimeExpected.recovery_remaining_event_ids as string[],
        final_status: marketTimeExpected.recovery_final_status as "completed",
        final_position: marketTimeExpected.recovery_final_position as number,
        last_event_id: marketTimeExpected.recovery_last_event_id as string,
        current_time: marketTimeExpected.recovery_current_time as string,
      },
    },
  };
}

const proposalResponse: LifecycleTransitionProposalResponse = {
  proposal: {
    schema_version: 1,
    proposal_id: "proposal-158",
    source_snapshot: {
      schema_version: 1,
      snapshot_id: "snapshot-source",
      strategy_id: "moving_average_crossover",
      lifecycle_state: "research_review",
      rationale: "Source evidence",
      declared_by: null,
      declared_timestamp: null,
      notes: ["source note", "source note"],
      warnings: [],
    },
    target_state: "paper_candidate",
    rationale: "Request human review",
    evidence_references: [
      {
        schema_version: 1,
        reference_type: "strategy_decision_record",
        reference_id: "decision-158",
        label: "Decision evidence",
        description: null,
      },
      {
        schema_version: 1,
        reference_type: "strategy_decision_record",
        reference_id: "decision-158",
        label: null,
        description: "Duplicate pointer retained",
      },
    ],
    requested_by: null,
    requested_timestamp: null,
    notes: [],
    warnings: ["human review required"],
  },
};

const resultingSnapshot = {
  schema_version: 1 as const,
  snapshot_id: "snapshot-result",
  strategy_id: "moving_average_crossover",
  lifecycle_state: "paper_candidate",
  rationale: "Caller supplied after review",
  declared_by: "founder",
  declared_timestamp: "2026-07-15T11:00:00+00:00",
  notes: [],
  warnings: ["not execution evidence"],
};

const reviewResponse: LifecycleTransitionReviewResponse = {
  transition_record: {
    schema_version: 1,
    transition_record_id: "record-158",
    proposal: proposalResponse.proposal,
    review_outcome: "approved",
    rationale: "Founder recorded an explicit outcome",
    resulting_snapshot: resultingSnapshot,
    reviewed_by: "founder",
    reviewed_timestamp: "2026-07-15T11:00:00+00:00",
    notes: ["review note"],
    warnings: [],
  },
};

function response(body: unknown, status = 200, requestId = "request-158") {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    },
  });
}

function fillRequiredProposal({ withEvidence = false }: { withEvidence?: boolean } = {}) {
  const source = screen.getByRole("group", { name: "Source lifecycle snapshot" });
  fireEvent.change(within(source).getByLabelText("Snapshot ID"), { target: { value: "snapshot-source" } });
  fireEvent.change(within(source).getByLabelText("Strategy ID"), { target: { value: "moving_average_crossover" } });
  fireEvent.change(within(source).getByLabelText(/^Lifecycle state/), { target: { value: "research_review" } });
  fireEvent.change(within(source).getByLabelText("Snapshot rationale"), { target: { value: "Source evidence" } });
  const proposal = screen.getByRole("group", { name: "Transition proposal" });
  fireEvent.change(within(proposal).getByLabelText("Proposal ID"), { target: { value: "proposal-158" } });
  fireEvent.change(within(proposal).getByLabelText(/^Target state/), { target: { value: "paper_candidate" } });
  fireEvent.change(within(proposal).getByLabelText("Proposal rationale"), { target: { value: "Request human review" } });
  if (withEvidence) {
    const evidence = screen.getByRole("group", { name: "Evidence references" });
    fireEvent.click(within(evidence).getByRole("button", { name: "Add evidence reference" }));
    fireEvent.click(within(evidence).getByRole("button", { name: "Add evidence reference" }));
    const types = within(evidence).getAllByLabelText("Reference type");
    const ids = within(evidence).getAllByLabelText("Reference ID");
    const labels = within(evidence).getAllByLabelText(/^Label/);
    const descriptions = within(evidence).getAllByLabelText(/^Description/);
    for (const index of [0, 1]) {
      fireEvent.change(types[index], { target: { value: "strategy_decision_record" } });
      fireEvent.change(ids[index], { target: { value: "decision-158" } });
    }
    fireEvent.change(labels[0], { target: { value: "Decision evidence" } });
    fireEvent.change(descriptions[1], { target: { value: "Duplicate pointer retained" } });
  }
}

async function submitProposal(fetcher: ReturnType<typeof vi.fn<typeof fetch>>) {
  vi.stubGlobal("fetch", fetcher);
  fillRequiredProposal({ withEvidence: true });
  await userEvent.click(screen.getByRole("button", { name: "Create non-executing proposal" }));
  await screen.findByRole("heading", { name: "Proposal response received" });
}

describe("LifecycleReviewWorkspace", () => {
  it("starts with explicit command inputs and no fabricated proposal, review, or current state", () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    render(<LifecycleReviewWorkspace />);

    expect(screen.getByRole("heading", { name: "Lifecycle proposal, human review, and timeline" })).toBeVisible();
    expect(screen.getByText("No command on this page applies a lifecycle transition.")).toBeVisible();
    expect(screen.getByRole("heading", { name: "No lifecycle command response yet" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Record an explicit human review" })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("loads lifecycle inputs from the backend demo descriptor without applying a transition", async () => {
    const descriptor = demoDescriptorFromVersionedSource();
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(descriptor, 200, "descriptor-request"))
      .mockResolvedValueOnce(response(proposalResponse, 200, "proposal-request"));
    vi.stubGlobal("fetch", fetcher);
    render(<LifecycleReviewWorkspace />);

    await userEvent.click(screen.getByRole("button", { name: "Load demo lifecycle example" }));

    expect(await within(screen.getByRole("group", { name: "Source lifecycle snapshot" })).findByLabelText("Snapshot ID")).toHaveValue(
      descriptor.lifecycle_proposal_example.source_snapshot.snapshot_id,
    );
    expect(screen.getByText("No command on this page applies a lifecycle transition.")).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: "Create non-executing proposal" }));
    const review = await screen.findByRole("group", { name: "Human review record" });
    expect(within(review).getByLabelText("Transition record ID")).toHaveValue(
      descriptor.lifecycle_review_example.transition_record_id,
    );
    expect(within(review).getByLabelText(/^Review outcome/)).toHaveValue(
      descriptor.lifecycle_review_example.review_outcome,
    );
    expect(fetcher.mock.calls[0][0]).toBe("/api/backend/api/v1/demo-workspace");
    expect(fetcher.mock.calls[1][0]).toBe("/api/backend/api/v1/lifecycle-transition-proposals");
  });

  it("lets the backend reject a structurally complete proposal without recreating evidence rules", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(
        {
          error: {
            code: "lifecycle_transition_proposal_invalid",
            message: "Lifecycle transition proposal is invalid",
          },
          request_id: "proposal-invalid",
        },
        422,
        "proposal-invalid",
      ),
    );
    vi.stubGlobal("fetch", fetcher);
    render(<LifecycleReviewWorkspace />);
    fillRequiredProposal();

    await userEvent.click(screen.getByRole("button", { name: "Create non-executing proposal" }));

    expect(await screen.findByRole("heading", { name: "Lifecycle proposal is invalid" })).toBeVisible();
    expect(screen.getByText("Request proposal-invalid")).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(1);
    const payload = JSON.parse(String((fetcher.mock.calls[0][1] as RequestInit).body));
    expect(payload.evidence_references).toEqual([]);
    expect(payload).toMatchObject({
      proposal_id: "proposal-158",
      source_snapshot: { lifecycle_state: "research_review" },
      target_state: "paper_candidate",
    });
  });

  it("preserves normalized evidence order and exposes an explicit human-review step", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(proposalResponse, 200, "proposal-request"),
    );
    render(<LifecycleReviewWorkspace />);
    await submitProposal(fetcher);

    expect(screen.getByText("Request proposal-request")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Lifecycle proposal" })).toBeVisible();
    expect(screen.getByText("This proposal is a request for human review. It is not approval, execution, promotion, or a current-state change.")).toBeVisible();
    const evidence = screen.getByRole("heading", { name: "Evidence references" }).parentElement;
    expect(evidence).not.toBeNull();
    expect(within(evidence as HTMLElement).getAllByRole("listitem")).toHaveLength(2);
    expect(within(evidence as HTMLElement).getAllByText("decision-158").length).toBeGreaterThanOrEqual(2);
    expect(within(evidence as HTMLElement).getByText("Duplicate pointer retained")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Record an explicit human review" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Lifecycle timeline" })).toBeVisible();
    expect(screen.getByText("Requested transition to paper_candidate. Proposal creation is non-executing.")).toBeVisible();
  });

  it("records human review from the normalized proposal and does not infer execution or current state", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(proposalResponse, 200, "proposal-request"))
      .mockResolvedValueOnce(response(reviewResponse, 200, "review-request"));
    render(<LifecycleReviewWorkspace />);
    await submitProposal(fetcher);

    const review = screen.getByRole("group", { name: "Human review record" });
    fireEvent.change(within(review).getByLabelText("Transition record ID"), { target: { value: "record-158" } });
    fireEvent.change(within(review).getByLabelText(/^Review outcome/), { target: { value: "approved" } });
    fireEvent.change(within(review).getByLabelText(/^Reviewed by/), { target: { value: "founder" } });
    fireEvent.change(within(review).getByLabelText(/^Reviewed timestamp/), { target: { value: "2026-07-15T11:00:00Z" } });
    fireEvent.change(within(review).getByLabelText("Review rationale"), { target: { value: "Founder recorded an explicit outcome" } });
    await userEvent.click(screen.getByLabelText("Include an explicit caller-supplied resulting snapshot"));
    const resulting = screen.getByRole("group", { name: "Caller-supplied resulting snapshot" });
    fireEvent.change(within(resulting).getByLabelText("Snapshot ID"), { target: { value: "snapshot-result" } });
    fireEvent.change(within(resulting).getByLabelText("Strategy ID"), { target: { value: "moving_average_crossover" } });
    fireEvent.change(within(resulting).getByLabelText(/^Lifecycle state/), { target: { value: "paper_candidate" } });
    fireEvent.change(within(resulting).getByLabelText("Snapshot rationale"), { target: { value: "Caller supplied after review" } });

    await userEvent.click(screen.getByRole("button", { name: "Record human review evidence" }));

    expect(await screen.findByRole("heading", { name: "Human review response received" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Human review record" })).toBeVisible();
    expect(screen.getByText("Recorded outcome: approved. This is governance evidence, not execution evidence.")).toBeVisible();
    expect(screen.getByText("Returned state: paper_candidate. The workspace does not mark this snapshot current.")).toBeVisible();
    expect(screen.getByText("This returned snapshot is immutable evidence. The workspace does not identify it as globally current or executed.")).toBeVisible();

    const body = JSON.parse(String((fetcher.mock.calls[1][1] as RequestInit).body));
    expect(body.proposal).toEqual({
      proposal_id: "proposal-158",
      source_snapshot: {
        snapshot_id: "snapshot-source",
        strategy_id: "moving_average_crossover",
        lifecycle_state: "research_review",
        rationale: "Source evidence",
        declared_by: null,
        declared_timestamp: null,
        notes: ["source note", "source note"],
        warnings: [],
      },
      target_state: "paper_candidate",
      rationale: "Request human review",
      evidence_references: [
        {
          reference_type: "strategy_decision_record",
          reference_id: "decision-158",
          label: "Decision evidence",
          description: null,
        },
        {
          reference_type: "strategy_decision_record",
          reference_id: "decision-158",
          label: null,
          description: "Duplicate pointer retained",
        },
      ],
      requested_by: null,
      requested_timestamp: null,
      notes: [],
      warnings: ["human review required"],
    });
    expect(body.resulting_snapshot).toMatchObject({
      snapshot_id: "snapshot-result",
      lifecycle_state: "paper_candidate",
    });
    expect(JSON.stringify(body)).not.toContain("schema_version");
  });

  it("suppresses duplicate proposal submissions while one command is pending", async () => {
    let resolveRequest: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
      () => new Promise((resolve) => { resolveRequest = resolve; }),
    );
    vi.stubGlobal("fetch", fetcher);
    render(<LifecycleReviewWorkspace />);
    fillRequiredProposal();

    await userEvent.click(screen.getByRole("button", { name: "Create non-executing proposal" }));
    const pending = await screen.findByRole("button", { name: "Creating proposal…" });
    expect(pending).toBeDisabled();
    fireEvent.click(pending);
    expect(fetcher).toHaveBeenCalledTimes(1);
    resolveRequest?.(response(proposalResponse));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Proposal response received" })).toBeVisible());
  });

  it("localizes Lifecycle Review while preserving raw descriptor IDs and lifecycle transport state", async () => {
    const descriptor = demoDescriptorFromVersionedSource();
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(descriptor, 200, "descriptor-zh-request"),
    );
    vi.stubGlobal("fetch", fetcher);

    render(<LifecycleReviewWorkspace />, { locale: "zh-CN" });

    expect(screen.getByRole("heading", { name: "生命周期提案、人工审查与时间线" })).toBeVisible();
    expect(screen.getByText("本页面上的任何命令都不会应用生命周期转换。")).toBeVisible();
    expect(screen.getByRole("button", { name: "创建非执行提案" })).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "加载演示生命周期示例" }));

    expect(await screen.findByDisplayValue(descriptor.lifecycle_proposal_example.source_snapshot.snapshot_id)).toBeVisible();
    expect(screen.getByDisplayValue(descriptor.lifecycle_proposal_example.source_snapshot.lifecycle_state)).toBeVisible();
    expect(screen.getByDisplayValue(descriptor.lifecycle_proposal_example.proposal_id)).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
