import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  submitLifecycleTransitionProposal,
  submitLifecycleTransitionReview,
  type LifecycleTransitionProposalRequest,
  type LifecycleTransitionProposalResponse,
  type LifecycleTransitionReviewRequest,
  type LifecycleTransitionReviewResponse,
} from "@/lib/api-client";

const proposalRequest: LifecycleTransitionProposalRequest = {
  proposal_id: "proposal-158",
  source_snapshot: {
    snapshot_id: "snapshot-source",
    strategy_id: "moving_average_crossover",
    lifecycle_state: "research_review",
    rationale: "Source evidence",
    declared_by: "founder",
    declared_timestamp: "2026-07-15T10:00:00Z",
    notes: [],
    warnings: [],
  },
  target_state: "paper_candidate",
  rationale: "Request a human review",
  evidence_references: [
    {
      reference_type: "strategy_decision_record",
      reference_id: "decision-158",
      label: null,
      description: null,
    },
  ],
  requested_by: "founder",
  requested_timestamp: "2026-07-15T10:05:00Z",
  notes: [],
  warnings: [],
};

const proposalResponse: LifecycleTransitionProposalResponse = {
  proposal: {
    schema_version: 1,
    ...proposalRequest,
    source_snapshot: {
      schema_version: 1,
      ...proposalRequest.source_snapshot,
      declared_by: "founder",
      declared_timestamp: "2026-07-15T10:00:00+00:00",
    },
    requested_by: "founder",
    requested_timestamp: "2026-07-15T10:05:00+00:00",
    evidence_references: proposalRequest.evidence_references.map((reference) => ({
      schema_version: 1 as const,
      ...reference,
      label: null,
      description: null,
    })),
  },
};

const reviewRequest: LifecycleTransitionReviewRequest = {
  transition_record_id: "record-158",
  proposal: proposalRequest,
  review_outcome: "deferred",
  rationale: "More evidence is required",
  resulting_snapshot: null,
  reviewed_by: "founder",
  reviewed_timestamp: "2026-07-15T10:10:00Z",
  notes: [],
  warnings: [],
};

const reviewResponse: LifecycleTransitionReviewResponse = {
  transition_record: {
    schema_version: 1,
    transition_record_id: "record-158",
    proposal: proposalResponse.proposal,
    review_outcome: "deferred",
    rationale: "More evidence is required",
    resulting_snapshot: null,
    reviewed_by: "founder",
    reviewed_timestamp: "2026-07-15T10:10:00+00:00",
    notes: [],
    warnings: [],
  },
};

function jsonResponse(body: unknown, requestId: string): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    },
  });
}

describe("lifecycle command API clients", () => {
  it("posts a generated proposal request only through the same-origin API gateway", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(proposalResponse, "request-proposal"),
    );

    await expect(submitLifecycleTransitionProposal(proposalRequest, fetcher)).resolves.toEqual({
      data: proposalResponse,
      requestId: "request-proposal",
    });
    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/lifecycle-transition-proposals",
      {
        method: "POST",
        cache: "no-store",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(proposalRequest),
      },
    );
  });

  it("posts the explicit human review and accepts an exact generated success response", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(reviewResponse, "request-review"),
    );

    await expect(submitLifecycleTransitionReview(reviewRequest, fetcher)).resolves.toEqual({
      data: reviewResponse,
      requestId: "request-review",
    });
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/lifecycle-transition-records",
    );
    expect(JSON.parse(String((fetcher.mock.calls[0][1] as RequestInit).body))).toEqual(
      reviewRequest,
    );
  });

  it("rejects a malformed lifecycle success response instead of rendering inferred state", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          proposal: {
            ...proposalResponse.proposal,
            source_snapshot: {
              ...proposalResponse.proposal.source_snapshot,
              schema_version: 2,
            },
          },
        },
        "request-invalid",
      ),
    );

    const error = await submitLifecycleTransitionProposal(
      proposalRequest,
      fetcher,
    ).catch((reason: unknown) => reason);
    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "api_response_invalid",
      requestId: "request-invalid",
    });
  });
});
