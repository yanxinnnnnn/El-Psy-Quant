import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  createPortfolioReview,
  fetchPortfolioReviewDetail,
  fetchPortfolioReviews,
  submitPortfolioReviewDecision,
  type PortfolioReviewCreateRequest,
  type PortfolioReviewDecisionRequest,
} from "@/lib/api-client";
import {
  portfolioReviewDetail,
  portfolioReviewRecord,
  settledPortfolioReviewDetail,
} from "@/test/portfolio-review-fixtures";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "portfolio-request-175",
    },
  });
}

const createRequest: PortfolioReviewCreateRequest = {
  review_id: "synthetic-review-175",
  source: {
    source_id: "synthetic-source-175",
    components: [
      {
        component_id: "component-a",
        strategy_id: "synthetic-strategy-a",
        evidence_references: [{
          reference_type: "research_run",
          reference_id: "synthetic-run-a",
        }],
        symbols: ["SYN-A"],
      },
      {
        component_id: "component-b",
        strategy_id: "synthetic-strategy-b",
        evidence_references: [{
          reference_type: "configured_run",
          reference_id: "synthetic-run-b",
        }],
        symbols: null,
      },
    ],
    return_observations: [
      { timestamp: "2026-01-01T00:00:00Z", component_returns: [0.1, -0.1] },
      { timestamp: "2026-01-02T00:00:00Z", component_returns: [0.2, -0.2] },
      { timestamp: "2026-01-03T00:00:00Z", component_returns: [0.3, -0.3] },
    ],
    evaluation_frequency: "synthetic-daily",
    periods_per_year: null,
    created_by: "synthetic-founder",
    created_timestamp: "2026-07-20T00:30:00Z",
    assumptions: [],
    warnings: [],
    missing_evidence: [],
  },
  baseline_scenario: {
    scenario_id: "synthetic-baseline",
    weights: { "component-a": 0.8, "component-b": 0.2 },
    rationale: "Synthetic baseline",
    assumptions: [],
    warnings: [],
  },
  proposed_scenario: {
    scenario_id: "synthetic-proposed",
    weights: { "component-a": 0.4, "component-b": 0.6 },
    rationale: "Synthetic proposal",
    proposed_component_id: "component-b",
    assumptions: [],
    warnings: [],
  },
  analysis: {
    created_by: "synthetic-analyst",
    created_timestamp: "2026-07-20T01:00:00Z",
    assumptions: [],
    warnings: [],
    missing_evidence: [],
  },
};

const decisionRequest: PortfolioReviewDecisionRequest = {
  decision_id: "synthetic-decision-175",
  outcome: "approved",
  rationale: "Synthetic governance rationale",
  reviewed_by: "synthetic-reviewer",
  reviewed_timestamp: "2026-07-20T02:00:00Z",
  notes: [],
  warnings: [],
};

describe("portfolio review generated-contract API client", () => {
  it("constructs exact list queries, validates filters, and preserves backend order", async () => {
    const second = { ...portfolioReviewRecord, review_id: "synthetic-second" };
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response([second, portfolioReviewRecord, portfolioReviewRecord]),
    );
    const result = await fetchPortfolioReviews(
      { status: "awaiting_decision", limit: 200 },
      fetcher,
    );
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews?status=awaiting_decision&limit=200",
    );
    expect(result.data.map((item) => item.review_id)).toEqual([
      "synthetic-second",
      "synthetic-review-175",
      "synthetic-review-175",
    ]);
    expect(() =>
      fetchPortfolioReviews({ status: null, limit: 0 }, fetcher),
    ).toThrow(/between 1 and 200/);
  });

  it("encodes the exact review path segment once", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(portfolioReviewDetail),
    );
    await fetchPortfolioReviewDetail("review / % ?", fetcher);
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews/review%20%2F%20%25%20%3F",
    );
  });

  it.each([
    [201, "created"],
    [200, "replayed"],
  ] as const)("accepts create HTTP %s with %s and sends the exact key/body", async (status, outcome) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ outcome, review: portfolioReviewDetail }, status),
    );
    const result = await createPortfolioReview(
      createRequest,
      "Synthetic.Create:175",
      fetcher,
    );
    expect(result.data.outcome).toBe(outcome);
    expect(result.requestId).toBe("portfolio-request-175");
    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/portfolio-reviews",
      {
        method: "POST",
        cache: "no-store",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "Idempotency-Key": "Synthetic.Create:175",
        },
        body: JSON.stringify(createRequest),
      },
    );
  });

  it("sends an exact decision command and accepts the settled authority", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({ outcome: "created", review: settledPortfolioReviewDetail }, 201),
    );
    const result = await submitPortfolioReviewDecision(
      "synthetic review",
      decisionRequest,
      "Synthetic.Decision:175",
      fetcher,
    );
    expect(result.data.review.decision?.outcome).toBe("approved");
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews/synthetic%20review/decision",
    );
    expect(fetcher.mock.calls[0][1]).toMatchObject({
      body: JSON.stringify(decisionRequest),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "Idempotency-Key": "Synthetic.Decision:175",
      },
    });
  });

  it("rejects blank mutation keys before calling fetch", () => {
    const fetcher = vi.fn<typeof fetch>();
    expect(() => createPortfolioReview(createRequest, "  ", fetcher)).toThrow(
      /nonblank/,
    );
    expect(() =>
      submitPortfolioReviewDecision(
        "synthetic-review-175",
        decisionRequest,
        "",
        fetcher,
      ),
    ).toThrow(/nonblank/);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it.each([
    {
      name: "settled record without a decision",
      mutate: () => ({
        ...settledPortfolioReviewDetail,
        decision: null,
      }),
    },
    {
      name: "awaiting record with a populated decision",
      mutate: () => ({
        ...portfolioReviewDetail,
        decision: settledPortfolioReviewDetail.decision,
      }),
    },
    {
      name: "status version and null-field inconsistency",
      mutate: () => ({
        ...portfolioReviewDetail,
        record: {
          ...portfolioReviewDetail.record,
          status: "approved",
        },
      }),
    },
    {
      name: "mismatched source digest",
      mutate: () => ({
        ...portfolioReviewDetail,
        source: {
          ...portfolioReviewDetail.source,
          source_digest: "mixed-source-digest",
        },
      }),
    },
    {
      name: "mismatched analysis review ID",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          review_id: "mixed-review-id",
        },
      }),
    },
    {
      name: "mismatched nested scenario identity",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          baseline_scenario: {
            ...portfolioReviewDetail.analysis.baseline_scenario,
            scenario_id: "mixed-baseline-id",
          },
        },
      }),
    },
    {
      name: "mismatched decision identity",
      mutate: () => ({
        ...settledPortfolioReviewDetail,
        decision: {
          ...settledPortfolioReviewDetail.decision!,
          decision_id: "mixed-decision-id",
        },
      }),
    },
    {
      name: "mismatched decision digest",
      mutate: () => ({
        ...settledPortfolioReviewDetail,
        decision: {
          ...settledPortfolioReviewDetail.decision!,
          decision_digest: "mixed-decision-digest",
        },
      }),
    },
    {
      name: "mismatched decision outcome",
      mutate: () => ({
        ...settledPortfolioReviewDetail,
        decision: {
          ...settledPortfolioReviewDetail.decision!,
          outcome: "deferred",
        },
      }),
    },
    {
      name: "mismatched component order",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          component_ids: ["component-b", "component-a"],
        },
      }),
    },
    {
      name: "nested status",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          interaction_impact_analysis: {
            ...portfolioReviewDetail.analysis.interaction_impact_analysis,
            pairwise_correlations: [{
              ...portfolioReviewDetail.analysis.interaction_impact_analysis.pairwise_correlations[0],
              status: "unknown",
            }],
          },
        },
      }),
    },
    {
      name: "non-finite metric",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          interaction_impact_analysis: {
            ...portfolioReviewDetail.analysis.interaction_impact_analysis,
            proposed_impact: {
              ...portfolioReviewDetail.analysis.interaction_impact_analysis.proposed_impact,
              mean_return_delta: Number.POSITIVE_INFINITY,
            },
          },
        },
      }),
    },
    {
      name: "invalid unavailable null semantics",
      mutate: () => ({
        ...portfolioReviewDetail,
        analysis: {
          ...portfolioReviewDetail.analysis,
          interaction_impact_analysis: {
            ...portfolioReviewDetail.analysis.interaction_impact_analysis,
            symbol_overlaps: [{
              ...portfolioReviewDetail.analysis.interaction_impact_analysis.symbol_overlaps[0],
              shared_symbol_count: 0,
            }],
          },
        },
      }),
    },
  ])("turns malformed $name into api_response_invalid", async ({ mutate }) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(mutate()));
    await expect(
      fetchPortfolioReviewDetail("synthetic-review-175", fetcher),
    ).rejects.toMatchObject({
      code: "api_response_invalid",
      requestId: "portfolio-request-175",
    });
  });

  it("preserves stable backend errors and request IDs", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response({
        error: {
          code: "portfolio_review_settled_conflict",
          message: "Review already settled",
        },
        request_id: "body-request",
      }, 409),
    );
    await expect(
      submitPortfolioReviewDecision(
        "synthetic-review-175",
        decisionRequest,
        "Synthetic.Decision:175",
        fetcher,
      ),
    ).rejects.toEqual(expect.objectContaining({
      code: "portfolio_review_settled_conflict",
      requestId: "portfolio-request-175",
      status: 409,
    } satisfies Partial<ApiClientError>));
  });
});
