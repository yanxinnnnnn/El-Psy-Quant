import { render, screen, waitFor } from "@/test/render";
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

  it("uses the localized stable-error presentation when the local API is unavailable", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new Error("C:\\private\\network detail"));
    vi.stubGlobal("fetch", fetcher);

    render(<HealthPanel />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "本地 API 不可用" })).toBeVisible();
    expect(screen.getByText("工作台无法通过同源网关连接本地 API。")).toBeVisible();
    expect(screen.getByText("请确认 FastAPI 已在回环地址运行，然后重试。")).toBeVisible();
    expect(screen.getByText("错误码：api_unavailable")).toBeVisible();
    expect(screen.getByText("The local API is unavailable.").closest("details")).not.toBeNull();
    expect(screen.getByRole("button", { name: "重试连接" })).toBeVisible();
    expect(screen.queryByText(/private/i)).not.toBeInTheDocument();
  });
});
