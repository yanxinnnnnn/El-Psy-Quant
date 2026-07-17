import { describe, expect, it } from "vitest";

import {
  isExplicitUtcTimestamp,
  isExplicitUtcTimestampAtOrAfter,
  paperJobActionsForStatus,
  reconcilePaperJobAttempts,
} from "@/lib/paper-jobs";

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

describe("paperJobActionsForStatus", () => {
  it.each([
    ["queued", ["run", "cancel"]],
    ["running", ["recover"]],
    ["failed", ["retry"]],
    ["succeeded", []],
    ["canceled", []],
    ["future-status", []],
  ])("uses one bounded action matrix for %s", (status, expected) => {
    expect(paperJobActionsForStatus(status)).toEqual(expected);
  });
});

describe("reconcilePaperJobAttempts", () => {
  it("replaces by attempt ID, appends new attempts, and never duplicates", () => {
    const first = {
      attempt_id: "attempt-1",
      attempt_number: 1,
      status: "running" as const,
      started_timestamp: "2026-07-15T10:00:00Z",
      completed_timestamp: null,
      error_code: null,
    };
    const second = {
      attempt_id: "attempt-2",
      attempt_number: 2,
      status: "failed" as const,
      started_timestamp: "2026-07-15T11:00:00Z",
      completed_timestamp: "2026-07-15T11:01:00Z",
      error_code: "workflow_validation_failed" as const,
    };
    const interrupted = {
      ...first,
      status: "interrupted" as const,
      completed_timestamp: "2026-07-15T10:02:00Z",
      error_code: "interrupted_without_output" as const,
    };
    const replaced = reconcilePaperJobAttempts(
      [first, second],
      [interrupted],
    );

    expect(replaced.map((attempt) => attempt.attempt_id)).toEqual([
      "attempt-1",
      "attempt-2",
    ]);
    expect(replaced[0]).toEqual(interrupted);
    expect(reconcilePaperJobAttempts(replaced, [interrupted])).toEqual(replaced);

    const appended = reconcilePaperJobAttempts([], [first, first]);
    expect(appended).toEqual([first]);
  });
});

describe("isExplicitUtcTimestampAtOrAfter", () => {
  it("compares exact UTC instants without generating a threshold", () => {
    expect(
      isExplicitUtcTimestampAtOrAfter(
        "2026-07-15T10:00:00.001+00:00",
        "2026-07-15T10:00:00Z",
      ),
    ).toBe(true);
    expect(
      isExplicitUtcTimestampAtOrAfter(
        "2026-07-15T09:59:59.999Z",
        "2026-07-15T10:00:00Z",
      ),
    ).toBe(false);
    expect(
      isExplicitUtcTimestampAtOrAfter(
        "2026-07-15T10:00:00+08:00",
        "2026-07-15T10:00:00Z",
      ),
    ).toBe(false);
  });
});
