import { describe, expect, it } from "vitest";

import {
  LifecycleStateValue,
  PaperJobStatusValue,
  ReviewOutcomeValue,
} from "@/components/domain-values";
import { render, screen, within } from "@/test/render";

describe("operational status presentation", () => {
  it("pairs a localized failed label with the unchanged raw transport value", () => {
    render(<PaperJobStatusValue value="failed" />, { locale: "zh-CN" });

    const badge = screen.getByText("失败").closest(".status-badge");
    expect(badge).toHaveClass("status-badge--danger");
    expect(within(badge as HTMLElement).getByText("failed", { selector: "code" })).toBeVisible();
  });

  it("uses bounded neutral presentation for an unknown lifecycle state", () => {
    render(<LifecycleStateValue value="future_state" />);

    const raw = screen.getByText("future_state", { selector: "code" });
    expect(raw.closest(".status-badge")).toHaveClass("status-badge--neutral");
  });

  it("presents human approval as informational evidence rather than execution", () => {
    render(<ReviewOutcomeValue value="approved" />);

    const badge = screen.getByText("Approved").closest(".status-badge");
    expect(badge).toHaveClass("status-badge--info");
    expect(within(badge as HTMLElement).getByText("approved", { selector: "code" })).toBeVisible();
  });
});
