import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthPanel } from "./health-panel";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HealthPanel", () => {
  it("moves from loading to available without leaving the workspace", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({ status: "ok", service: "el-psy-quant", api_version: "v1" }),
        { status: 200, headers: { "X-Request-ID": "request-123" } },
      ),
    );
    vi.stubGlobal("fetch", fetcher);

    render(<HealthPanel />);

    expect(screen.getByRole("status")).toHaveTextContent("Checking");
    await waitFor(() => expect(screen.getByText("Available")).toBeInTheDocument());
    expect(screen.getByText("Request request-123")).toBeInTheDocument();
  });

  it("shows a safe unavailable state and supports manual retry", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("private network detail"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ status: "ok", service: "el-psy-quant", api_version: "v1" }),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<HealthPanel />);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.queryByText(/private network detail/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry connection" }));
    await waitFor(() => expect(screen.getByText("Available")).toBeInTheDocument());
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
