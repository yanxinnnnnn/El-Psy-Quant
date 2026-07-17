import { describe, expect, it } from "vitest";

import { ScrollableTable } from "@/components/ui/scrollable-table";
import { render, screen, within } from "@/test/render";

describe("ScrollableTable", () => {
  it.each([
    ["English", "Research metrics"],
    ["Simplified Chinese", "研究指标"],
  ])("uses the localized caption as its %s accessible name", (_language, caption) => {
    render(
      <ScrollableTable caption={caption}>
        <thead><tr><th scope="col">ID</th><th scope="col">Status</th></tr></thead>
        <tbody>
          <tr><th scope="row">duplicate-id</th><td>interrupted</td></tr>
          <tr><th scope="row">duplicate-id</th><td>interrupted</td></tr>
        </tbody>
      </ScrollableTable>,
    );

    const region = screen.getByRole("region", { name: caption });
    expect(region).toHaveAttribute("tabindex", "0");
    const table = within(region).getByRole("table", { name: caption });
    expect(table.querySelector("caption")).toHaveTextContent(caption);
    expect(within(table).getAllByRole("columnheader").map((cell) => cell.textContent))
      .toEqual(["ID", "Status"]);
    expect(within(table).getAllByRole("rowheader").map((cell) => cell.textContent))
      .toEqual(["duplicate-id", "duplicate-id"]);
    expect(within(table).getAllByRole("cell").map((cell) => cell.textContent))
      .toEqual(["interrupted", "interrupted"]);
  });
});
