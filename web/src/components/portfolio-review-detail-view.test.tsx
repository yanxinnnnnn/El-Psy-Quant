import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PortfolioReviewDetailView } from "@/components/portfolio-review-detail-view";
import { render, screen, within } from "@/test/render";
import {
  portfolioReviewDetail,
  settledPortfolioReviewDetail,
} from "@/test/portfolio-review-fixtures";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "portfolio-detail-request",
    },
  });
}

describe("PortfolioReviewDetailView", () => {
  it("renders every evidence section, exact unusual values, duplicate prose, and unavailable reasons without recomputation", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(
      response(portfolioReviewDetail),
    ));
    render(<PortfolioReviewDetailView reviewId="synthetic-review-175" />);
    await screen.findByRole("heading", { name: "Source and components" });
    for (const heading of [
      "Return observations",
      "Scenarios and weights",
      "Concentration",
      "Review exposure and coverage",
      "Declared-symbol overlap",
      "Return correlation",
      "Historical behavior and drawdown",
      "Component contribution",
      "Exact proposed-minus-baseline impact",
      "Assumptions, warnings, and missing evidence",
      "Human decision",
      "Raw schemas, digests, and timestamps",
    ]) {
      expect(screen.getByRole("heading", { name: heading })).toBeVisible();
    }
    expect(screen.getByText("0.123456789012345")).toBeVisible();
    expect(screen.getByText("-1.11111111011111")).toBeVisible();
    expect(screen.getAllByText("Synthetic source assumption")).toHaveLength(2);
    const unavailable = screen.getAllByText("Unavailable")[0].closest(".evidence-card");
    expect(unavailable).not.toBeNull();
    expect(within(unavailable as HTMLElement).getByText("missing_symbol_evidence")).toBeVisible();
    expect(within(unavailable as HTMLElement).getByText("component-b")).toBeVisible();
    expect(within(unavailable as HTMLElement).queryByText("0")).not.toBeInTheDocument();
    expect(screen.getByText(portfolioReviewDetail.record.analysis_digest)).toBeVisible();
  });

  it("shows no default outcome and submits one exact explicit decision, then replaces detail with returned settlement", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(portfolioReviewDetail))
      .mockResolvedValueOnce(response({
        outcome: "created",
        review: settledPortfolioReviewDetail,
      }, 201));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioReviewDetailView reviewId="synthetic-review-175" />);
    const outcome = await screen.findByLabelText(/^Outcome/);
    expect(outcome).toHaveValue("");
    await user.type(screen.getByLabelText(/^Idempotency-Key/), "Synthetic.Decision:175");
    await user.type(screen.getByLabelText(/^Decision ID/), "synthetic-decision-175");
    await user.selectOptions(outcome, "approved");
    await user.type(screen.getByLabelText(/^Rationale/), "Synthetic governance rationale");
    await user.type(screen.getByLabelText(/^Reviewed by/), "synthetic-reviewer");
    await user.type(screen.getByLabelText(/^Reviewed timestamp/), "2026-07-20T02:00:00Z");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Record decision" }));
    expect(await screen.findByRole("heading", { name: "Decision recorded" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Immutable governance decision" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Record decision" })).not.toBeInTheDocument();
    expect(fetcher.mock.calls[1][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews/synthetic-review-175/decision",
    );
    expect(JSON.parse(String(fetcher.mock.calls[1][1]?.body))).toEqual({
      decision_id: "synthetic-decision-175",
      outcome: "approved",
      rationale: "Synthetic governance rationale",
      reviewed_by: "synthetic-reviewer",
      reviewed_timestamp: "2026-07-20T02:00:00Z",
      notes: [],
      warnings: [],
    });
  });

  it("preserves loaded evidence and every decision draft field after settled conflict", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(portfolioReviewDetail))
      .mockResolvedValueOnce(response({
        error: {
          code: "portfolio_review_settled_conflict",
          message: "Safe settled conflict",
        },
        request_id: "body-id",
      }, 409));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioReviewDetailView reviewId="synthetic-review-175" />);
    await user.type(await screen.findByLabelText(/^Idempotency-Key/), "Synthetic.Conflict:175");
    await user.type(screen.getByLabelText(/^Decision ID/), "synthetic-conflict-decision");
    await user.selectOptions(screen.getByLabelText(/^Outcome/), "deferred");
    await user.type(screen.getByLabelText(/^Rationale/), "Preserved synthetic rationale");
    await user.type(screen.getByLabelText(/^Reviewed by/), "synthetic-reviewer");
    await user.type(screen.getByLabelText(/^Reviewed timestamp/), "2026-07-20T03:00:00Z");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Record decision" }));
    expect(await screen.findByRole("heading", {
      name: "Portfolio review is already settled",
    })).toBeVisible();
    expect(screen.getByText("portfolio_review.decision")).toBeVisible();
    expect(screen.getByText("Request portfolio-detail-request")).toBeVisible();
    expect(screen.getByText("0.123456789012345")).toBeVisible();
    expect(screen.getByLabelText(/^Idempotency-Key/)).toHaveValue("Synthetic.Conflict:175");
    expect(screen.getByLabelText(/^Outcome/)).toHaveValue("deferred");
    expect(screen.getByLabelText(/^Rationale/)).toHaveValue("Preserved synthetic rationale");
  });

  it("settled detail renders only the immutable decision", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(
      response(settledPortfolioReviewDetail),
    ));
    render(<PortfolioReviewDetailView reviewId="synthetic-review-175" />);
    expect(await screen.findByRole("heading", {
      name: "Immutable governance decision",
    })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Record decision" })).not.toBeInTheDocument();
    expect(screen.getAllByText("Synthetic note")).toHaveLength(2);
  });
});
