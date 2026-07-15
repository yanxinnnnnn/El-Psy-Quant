import { describe, expect, it } from "vitest";

import { isExplicitUtcTimestamp } from "@/lib/paper-jobs";

describe("isExplicitUtcTimestamp", () => {
  it.each([
    "2026-07-15T10:00:00Z",
    "2026-07-15T10:00:00.123Z",
    "2026-07-15T10:00:00+00:00",
    "2026-07-15T10:00:00.123+00:00",
    "2024-02-29T23:59:59.000001Z",
  ])("accepts a full explicit UTC datetime: %s", (value) => {
    expect(isExplicitUtcTimestamp(value)).toBe(true);
  });

  it.each([
    "",
    "2026-07-15",
    "2026-07-15Z",
    "July 15, 2026 Z",
    "2026-07-15T10:00:00",
    "2026-07-15T10:00:00+08:00",
    "2026-07-15T10:00:00-00:00",
    "2026-02-29T10:00:00Z",
    "2026-04-31T10:00:00Z",
    "2026-07-15T24:00:00Z",
    "2026-07-15T10:60:00Z",
    "2026-07-15T10:00:60Z",
    "invalid",
  ])("rejects a non-compatible UTC value: %s", (value) => {
    expect(isExplicitUtcTimestamp(value)).toBe(false);
  });
});
