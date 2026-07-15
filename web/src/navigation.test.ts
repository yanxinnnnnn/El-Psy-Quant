import { describe, expect, it } from "vitest";

import { isDestinationActive, workspaceDestinations } from "./navigation";

describe("workspace navigation", () => {
  it("enables the four delivered destinations", () => {
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
    ]);
    expect(workspaceDestinations.slice(4).every((item) => item.href === undefined)).toBe(
      true,
    );
  });

  it("keeps S156 through S158 explicit and unavailable", () => {
    expect(workspaceDestinations.slice(4).map(({ label, sprint, available }) => ({
      label,
      sprint,
      available,
    }))).toEqual([
      { label: "Portfolio Records", sprint: "S156", available: false },
      { label: "Comparisons", sprint: "S157", available: false },
      { label: "Lifecycle Review", sprint: "S158", available: false },
    ]);
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
  ])("marks only the matching route family active for %s", (pathname, label) => {
    expect(
      workspaceDestinations
        .filter((destination) => isDestinationActive(destination, pathname))
        .map((destination) => destination.label),
    ).toEqual([label]);
  });
});
