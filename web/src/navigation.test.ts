import { describe, expect, it } from "vitest";

import { isDestinationActive, workspaceDestinations } from "./navigation";

describe("workspace navigation", () => {
  it("enables the twelve delivered destinations", () => {
    expect(workspaceDestinations.filter((item) => item.available)).toEqual([
      { labelKey: "overview", sprint: "S152", href: "/", available: true },
      {
        labelKey: "strategiesResearch",
        sprint: "S153",
        href: "/strategies",
        available: true,
      },
      {
        labelKey: "governanceReports",
        sprint: "S154",
        href: "/evidence-manifests",
        available: true,
      },
      {
        labelKey: "paperJobs",
        sprint: "S155",
        href: "/paper-jobs",
        available: true,
      },
      {
        labelKey: "portfolioRecords",
        sprint: "S156",
        href: "/portfolio-records",
        available: true,
      },
      {
        labelKey: "comparisons",
        sprint: "S157",
        href: "/comparisons",
        available: true,
      },
      {
        labelKey: "portfolioReviews",
        sprint: "S175",
        href: "/portfolio-reviews",
        available: true,
      },
      {
        labelKey: "paperAccounts",
        sprint: "S186",
        href: "/paper-accounts",
        available: true,
      },
      {
        labelKey: "marketTime",
        sprint: "S194",
        href: "/market-time",
        available: true,
      },
      {
        labelKey: "strategyToRisk",
        sprint: "S204",
        href: "/strategy-to-risk",
        available: true,
      },
      {
        labelKey: "paperExecution",
        sprint: "S213",
        href: "/paper-execution",
        available: true,
      },
      {
        labelKey: "lifecycleReview",
        sprint: "S158",
        href: "/lifecycle-review",
        available: true,
      },
    ]);
    expect(workspaceDestinations.every((item) => item.href !== undefined)).toBe(true);
  });

  it.each([
    ["/", "overview"],
    ["/strategies", "strategiesResearch"],
    ["/strategies/moving_average_crossover", "strategiesResearch"],
    ["/research-runs", "strategiesResearch"],
    ["/research-runs/my-experiment/run_1", "strategiesResearch"],
    ["/evidence-manifests", "governanceReports"],
    [
      "/evidence-manifests/report_artifact_manifest/founder-report",
      "governanceReports",
    ],
    ["/paper-jobs", "paperJobs"],
    ["/paper-jobs/new", "paperJobs"],
    ["/paper-jobs/123", "paperJobs"],
    ["/portfolio-records", "portfolioRecords"],
    ["/portfolio-records/123", "portfolioRecords"],
    ["/comparisons", "comparisons"],
    ["/portfolio-reviews", "portfolioReviews"],
    ["/portfolio-reviews/new", "portfolioReviews"],
    ["/portfolio-reviews/review-175", "portfolioReviews"],
    ["/paper-accounts", "paperAccounts"],
    ["/paper-accounts/new", "paperAccounts"],
    ["/paper-accounts/account-186", "paperAccounts"],
    ["/market-time", "marketTime"],
    ["/market-time/replays/replay-194", "marketTime"],
    ["/market-time/calendars/xnys-2026-v1", "marketTime"],
    ["/strategy-to-risk", "strategyToRisk"],
    ["/paper-execution", "paperExecution"],
    ["/lifecycle-review", "lifecycleReview"],
  ])("marks only the matching route family active for %s", (pathname, labelKey) => {
    expect(
      workspaceDestinations
        .filter((destination) => isDestinationActive(destination, pathname))
        .map((destination) => destination.labelKey),
    ).toEqual([labelKey]);
  });

  it("does not extend the comparisons active state beyond its exact route", () => {
    expect(
      workspaceDestinations.filter((destination) =>
        isDestinationActive(destination, "/comparisons/saved"),
      ),
    ).toEqual([]);
  });

  it("does not extend the lifecycle review active state beyond its exact route", () => {
    expect(
      workspaceDestinations.filter((destination) =>
        isDestinationActive(destination, "/lifecycle-review/history"),
      ),
    ).toEqual([]);
  });

  it("does not invent nested Paper Execution routes", () => {
    expect(
      workspaceDestinations.filter((destination) =>
        isDestinationActive(destination, "/paper-execution/orders/order-1"),
      ),
    ).toEqual([]);
  });
});
