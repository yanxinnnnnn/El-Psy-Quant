import { describe, expect, it } from "vitest";

import { workspaceDestinations } from "./navigation";

describe("workspace navigation", () => {
  it("enables only the implemented Overview destination", () => {
    expect(workspaceDestinations.filter((item) => item.available)).toEqual([
      { label: "Overview", sprint: "S152", href: "/", available: true },
    ]);
    expect(workspaceDestinations.slice(1).every((item) => item.href === undefined)).toBe(
      true,
    );
  });

  it("keeps each future Milestone 28 area explicit and unavailable", () => {
    expect(workspaceDestinations.slice(1).map(({ label, sprint, available }) => ({
      label,
      sprint,
      available,
    }))).toEqual([
      { label: "Strategies and Research", sprint: "S153", available: false },
      { label: "Governance and Reports", sprint: "S154", available: false },
      { label: "Paper Runs", sprint: "S155", available: false },
      { label: "Portfolio Records", sprint: "S156", available: false },
      { label: "Comparisons", sprint: "S157", available: false },
      { label: "Lifecycle Review", sprint: "S158", available: false },
    ]);
  });
});
