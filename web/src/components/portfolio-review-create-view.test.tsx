import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PortfolioReviewCreateView } from "@/components/portfolio-review-create-view";
import { render, screen, waitFor } from "@/test/render";
import { portfolioReviewDetail } from "@/test/portfolio-review-fixtures";

afterEach(() => vi.unstubAllGlobals());

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
    render(<PortfolioReviewCreateView />);
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
    render(<PortfolioReviewCreateView />);
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

  it("supports the 12-component boundary with stable dependent observation cells", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>());
    const user = userEvent.setup();
    render(<PortfolioReviewCreateView />);
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
});
