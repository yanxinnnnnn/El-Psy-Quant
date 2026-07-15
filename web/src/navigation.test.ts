import { describe, expect, it } from "vitest";

import { isDestinationActive, workspaceDestinations } from "./navigation";

describe("workspace navigation", () => {
  it("enables the seven delivered destinations", () => {
    expect(workspaceDestinations.filter((item) => item.available)).toEqual([
      { label: "Overview", sprint: "S152", href: "/", available: true },
      {
        label: "Strategies and Research",
        sprint: "S153",
        href: "/strategies",
        available: true,
      },
      {
        label: "Governance and Reports",
        sprint: "S154",
        href: "/evidence-manifests",
        available: true,
      },
      {
        label: "Paper Runs",
        sprint: "S155",
        href: "/paper-jobs",
        available: true,
      },
      {
        label: "Portfolio Records",
        sprint: "S156",
        href: "/portfolio-records",
        available: true,
      },
      {
        label: "Comparisons",
        sprint: "S157",
        href: "/comparisons",
        available: true,
      },
      {
        label: "Lifecycle Review",
        sprint: "S158",
        href: "/lifecycle-review",
        available: true,
      },
    ]);
    expect(workspaceDestinations.every((item) => item.href !== undefined)).toBe(true);
  });

  it.each([
    ["/", "Overview"],
    ["/strategies", "Strategies and Research"],
    ["/strategies/moving_average_crossover", "Strategies and Research"],
    ["/research-runs", "Strategies and Research"],
    ["/research-runs/my-experiment/run_1", "Strategies and Research"],
    ["/evidence-manifests", "Governance and Reports"],
    [
      "/evidence-manifests/report_artifact_manifest/founder-report",
      "Governance and Reports",
    ],
    ["/paper-jobs", "Paper Runs"],
    ["/paper-jobs/new", "Paper Runs"],
    ["/paper-jobs/123", "Paper Runs"],
    ["/portfolio-records", "Portfolio Records"],
    ["/portfolio-records/123", "Portfolio Records"],
    ["/comparisons", "Comparisons"],
    ["/lifecycle-review", "Lifecycle Review"],
  ])("marks only the matching route family active for %s", (pathname, label) => {
    expect(
      workspaceDestinations
        .filter((destination) => isDestinationActive(destination, pathname))
        .map((destination) => destination.label),
    ).toEqual([label]);
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
});
