import { describe, expect, it, vi } from "vitest";

import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { render, screen } from "@/test/render";

vi.mock("next/navigation", () => ({
  usePathname: () => "/strategy-to-risk",
}));

describe("Sprint 204 navigation", () => {
  it("exposes one current Strategy-to-Risk destination", () => {
    render(<WorkspaceNavigation />);
    const link = screen.getByRole("link", { name: /Strategy to Risk/ });
    expect(link).toHaveAttribute("href", "/strategy-to-risk");
    expect(link).toHaveAttribute("aria-current", "page");
  });
});
