import { describe, expect, it } from "vitest";

import {
  comparisonHref,
  comparisonResultErrorTitle,
  comparisonSelectionError,
} from "./comparisons";

describe("comparison URL selection", () => {
  it.each([
    [[], null],
    [["one"], "Select at least two backend-available results before comparing."],
    [["one", ""], "Comparison job IDs must be nonblank."],
    [["one", "one"], "Comparison job IDs must be distinct. Duplicate IDs are not allowed."],
    [["1", "2", "3", "4", "5"], "Select no more than four backend-available results before comparing."],
  ])("validates %j before result requests", (jobIds, expected) => {
    expect(comparisonSelectionError(jobIds)).toBe(expected);
  });

  it("preserves order and independently encodes repeated job_id parameters", () => {
    expect(comparisonHref(["second / job", "first?job"])).toBe(
      "/comparisons?job_id=second%20%2F%20job&job_id=first%3Fjob",
    );
  });

  it("keeps every required result error distinct and all other errors neutral", () => {
    expect(comparisonResultErrorTitle("product_database_unavailable")).toBe("Product database unavailable");
    expect(comparisonResultErrorTitle("paper_artifact_root_unavailable")).toBe("Paper artifact root unavailable");
    expect(comparisonResultErrorTitle("paper_job_not_found")).toBe("Paper job not found");
    expect(comparisonResultErrorTitle("paper_job_result_unavailable")).toBe("Paper job result unavailable");
    expect(comparisonResultErrorTitle("paper_job_result_invalid")).toBe("Paper job result is invalid");
    expect(comparisonResultErrorTitle("private_exception")).toBe("Comparison result unavailable");
  });
});
