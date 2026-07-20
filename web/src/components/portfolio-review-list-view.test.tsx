import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PortfolioReviewListView } from "@/components/portfolio-review-list-view";
import { render, screen, waitFor, within } from "@/test/render";
import {
  portfolioReviewRecord,
  settledPortfolioReviewDetail,
} from "@/test/portfolio-review-fixtures";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "portfolio-list-request",
    },
  });
}

describe("PortfolioReviewListView", () => {
  it("preserves exact backend order, duplicate rows, raw status, full digest, and detail links", async () => {
    const second = {
      ...settledPortfolioReviewDetail.record,
      review_id: "synthetic-second-review",
      source_id: "synthetic-second-source",
      status: "deferred" as const,
      outcome: "deferred" as const,
    };
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(
      response([second, portfolioReviewRecord, portfolioReviewRecord]),
    ));
    render(<PortfolioReviewListView />);
    const list = await screen.findByRole("list", {
      name: "Portfolio reviews in backend order",
    });
    const cards = within(list).getAllByRole("listitem");
    expect(cards).toHaveLength(3);
    expect(cards.map((card) => within(card).getByRole("heading").textContent)).toEqual([
      "synthetic-second-source",
      "synthetic-source-175",
      "synthetic-source-175",
    ]);
    expect(within(cards[0]).getByText("deferred", { selector: "code" })).toBeVisible();
    expect(within(cards[1]).getByText(portfolioReviewRecord.analysis_digest)).toBeVisible();
    expect(within(cards[1]).getByRole("link", { name: "Inspect exact review" })).toHaveAttribute(
      "href",
      "/portfolio-reviews/synthetic-review-175",
    );
  });

  it("applies draft filters only on Apply and preserves prior evidence during refresh", async () => {
    let resolveRefresh: ((value: Response) => void) | undefined;
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response([portfolioReviewRecord]))
      .mockImplementationOnce(() => new Promise((resolve) => {
        resolveRefresh = resolve;
      }));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioReviewListView />);
    expect(await screen.findAllByText("synthetic-source-175")).not.toHaveLength(0);
    expect(fetcher.mock.calls[0][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews?limit=50",
    );
    await user.selectOptions(screen.getByLabelText("Status"), "approved");
    await user.selectOptions(screen.getByLabelText("Limit"), "200");
    expect(fetcher).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    expect(fetcher.mock.calls[1][0]).toBe(
      "/api/backend/api/v1/portfolio-reviews?status=approved&limit=200",
    );
    expect(screen.getAllByText("synthetic-source-175")[0]).toBeVisible();
    expect(screen.getByText(/previous successful evidence remains visible/i)).toBeVisible();
    resolveRefresh?.(response([]));
    expect(await screen.findByRole("heading", {
      name: "No portfolio reviews match this filter",
    })).toBeVisible();
  });

  it("renders stable audit identity and supports manual retry", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response({
        error: {
          code: "portfolio_review_artifact_root_unavailable",
          message: "Safe portfolio list failure",
        },
        request_id: "body-id",
      }, 503))
      .mockResolvedValueOnce(response([]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioReviewListView />);
    expect(await screen.findByRole("heading", {
      name: "Portfolio review artifact root unavailable",
    })).toBeVisible();
    expect(screen.getByText("portfolio_review.list")).toBeVisible();
    expect(screen.getByText("Request portfolio-list-request")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", {
      name: "No portfolio reviews match this filter",
    })).toBeVisible();
  });

  it("retains exact prior rows after refresh failure and replaces them only after a successful retry", async () => {
    const replacement = {
      ...portfolioReviewRecord,
      review_id: "synthetic-replacement-review",
      source_id: "synthetic-replacement-source",
    };
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response([
        portfolioReviewRecord,
        portfolioReviewRecord,
      ]))
      .mockResolvedValueOnce(response({
        error: {
          code: "portfolio_review_artifact_unavailable",
          message: "Retained refresh backend message",
        },
        request_id: "body-id",
      }, 503))
      .mockResolvedValueOnce(response([replacement]));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PortfolioReviewListView />);

    const initialList = await screen.findByRole("list", {
      name: "Portfolio reviews in backend order",
    });
    expect(within(initialList).getAllByRole("listitem")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByRole("heading", {
      name: "Portfolio review artifact unavailable",
    })).toBeVisible();
    const retainedList = screen.getByRole("list", {
      name: "Portfolio reviews in backend order",
    });
    expect(within(retainedList).getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText(
      "Error code: portfolio_review_artifact_unavailable",
    )).toBeVisible();
    expect(screen.getByText("Retained refresh backend message")).toBeVisible();
    expect(screen.getByText("Request portfolio-list-request")).toBeVisible();
    expect(screen.getByText("503")).toBeVisible();
    expect(screen.getByText("portfolio_review.list")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", {
      name: "synthetic-replacement-source",
    })).toBeVisible();
    const replacementList = screen.getByRole("list", {
      name: "Portfolio reviews in backend order",
    });
    expect(within(replacementList).getAllByRole("listitem")).toHaveLength(1);
    expect(screen.queryByText("synthetic-source-175")).not.toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(3);
  });
});
