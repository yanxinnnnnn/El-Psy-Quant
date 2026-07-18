import { describe, expect, it } from "vitest";

import { ErrorState } from "@/components/data-states";
import {
  ERROR_PRESENTATION_INVENTORY,
  SUPPORTED_ERROR_CODES,
} from "@/i18n/errors";
import { loadMessages } from "@/i18n/messages";
import { render, screen } from "@/test/render";

const ATTEMPT_ERROR_CODES = [
  "workflow_validation_failed",
  "output_conflict",
  "filesystem_io_failed",
  "interrupted_without_output",
  "partial_output_detected",
  "invalid_output_detected",
  "unknown",
] as const;

describe("error surface and audit presentation", () => {
  it("keeps the static Web inventory aligned with both complete catalogs", () => {
    expect(SUPPORTED_ERROR_CODES).toEqual(
      Object.keys(ERROR_PRESENTATION_INVENTORY),
    );
    for (const locale of ["en", "zh-CN"] as const) {
      const messages = loadMessages(locale);
      for (const code of SUPPORTED_ERROR_CODES) {
        const presentation = messages.errors[code];
        expect(presentation.title).not.toHaveLength(0);
        expect(presentation.explanation).not.toHaveLength(0);
        expect(presentation.recovery).not.toHaveLength(0);
      }
      expect(Object.keys(messages.errors.categories)).toEqual([
        "authentication",
        "not_found",
        "invalid",
        "conflict",
        "unavailable",
        "protocol",
        "internal",
        "unknown",
      ]);
    }
  });

  it("renders accessible bounded audit fields without changing raw values", () => {
    render(
      <ErrorState
        code="product_database_unavailable"
        title="Context title"
        message="Safe backend detail"
        requestId="request-raw"
        operation="paper_job.detail"
        httpStatus={503}
        entityLabel="job_id"
        entityId="job-raw"
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Product database unavailable" }),
    ).toBeVisible();
    expect(screen.getByText("Unavailable")).toBeVisible();
    const audit = screen.getByRole("region", {
      name: "Technical audit details",
    });
    expect(audit).toHaveTextContent("paper_job.detail");
    expect(audit).toHaveTextContent("503");
    expect(audit).toHaveTextContent("job_id: job-raw");
    expect(audit).toHaveTextContent(
      "Error code: product_database_unavailable",
    );
    expect(audit).toHaveTextContent("Request request-raw");
    expect(screen.getByText("Safe backend detail")).toBeVisible();
    expect(
      screen.getByText("Backend detail").closest("details"),
    ).toHaveAttribute("open");
  });

  it("uses a safe unknown fallback for a prototype key and never invents a request ID", () => {
    render(
      <ErrorState
        code="toString"
        title="Context-specific failure"
        message={null}
        requestId={null}
        operation="unmatched"
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Context-specific failure" }),
    ).toBeVisible();
    expect(screen.getByText("Unknown error")).toBeVisible();
    expect(screen.getByText("Error code: toString")).toBeVisible();
    expect(screen.queryByText("Server request ID")).not.toBeInTheDocument();
  });

  it("defines bilingual label, meaning, and recovery for every attempt code", () => {
    const english = loadMessages("en").paperJobs.attemptErrors;
    const chinese = loadMessages("zh-CN").paperJobs.attemptErrors;

    for (const code of ATTEMPT_ERROR_CODES) {
      for (const catalog of [english, chinese]) {
        expect(catalog[code].label).not.toHaveLength(0);
        expect(catalog[code].meaning).not.toHaveLength(0);
        expect(catalog[code].recovery).not.toHaveLength(0);
      }
      expect(chinese[code].label).not.toBe(english[code].label);
    }
  });
});
