import { afterEach, describe, expect, it, vi } from "vitest";

import { ErrorState } from "@/components/data-states";
import { LocalizedNumber, LocalizedTimestamp } from "@/components/localized-values";
import { PaperJobListView } from "@/components/paper-job-list-view";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { render, screen, within } from "@/test/render";

vi.mock("next/navigation", () => ({ usePathname: () => "/paper-jobs" }));

afterEach(() => vi.unstubAllGlobals());

const job = {
  job_id: "11111111-1111-4111-8111-111111111111",
  run_id: "run-bilingual-raw",
  status: "failed",
  submitted_timestamp: "2026-07-15T10:00:00Z",
  updated_timestamp: "2026-07-15T11:00:00Z",
  attempt_count: 1,
  latest_attempt: {
    attempt_id: "22222222-2222-4222-8222-222222222222",
    attempt_number: 1,
    status: "failed",
    started_timestamp: "2026-07-15T10:30:00Z",
    completed_timestamp: "2026-07-15T11:00:00Z",
    error_code: "output_conflict",
  },
  result_available: false,
  result_url: null,
};

function response(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

describe("bilingual workspace presentation", () => {
  it("renders Simplified Chinese navigation and paper-job copy while preserving raw transport values", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(response([job])));
    render(<><WorkspaceNavigation /><PaperJobListView /></>, { locale: "zh-CN" });

    expect(screen.getByRole("navigation", { name: "创始人工作台" })).toBeVisible();
    expect(screen.getByRole("link", { name: /模拟任务/ })).toHaveAttribute("href", "/paper-jobs");
    expect(await screen.findByRole("heading", { name: "模拟任务状态" })).toBeVisible();
    const card = screen.getByRole("heading", { name: "run-bilingual-raw" }).closest("li");
    expect(card).not.toBeNull();
    expect(within(card as HTMLElement).getAllByText("failed").length).toBeGreaterThan(0);
    expect(within(card as HTMLElement).getByText("输出冲突 (output_conflict)")).toBeVisible();
    expect(within(card as HTMLElement).getByText("2026-07-15T10:00:00Z")).toBeVisible();
  });

  it("localizes number and UTC presentation without replacing stable raw values", () => {
    const english = render(
      <><LocalizedNumber value={1234.5} /><LocalizedTimestamp value="2026-07-15T10:00:00Z" /></>,
      { locale: "en" },
    );
    expect(screen.getByText("1,234.5")).toBeVisible();
    expect(screen.getByText("Raw value: 1234.5")).toBeVisible();
    expect(screen.getByText("2026-07-15T10:00:00Z")).toBeVisible();

    english.unmount();
    render(
      <><LocalizedNumber value={1234.5} /><LocalizedTimestamp value="2026-07-15T10:00:00Z" /></>,
      { locale: "zh-CN" },
    );
    expect(screen.getByText("1,234.5")).toBeVisible();
    expect(screen.getByText("原始值：1234.5")).toBeVisible();
    expect(screen.getByText("2026-07-15T10:00:00Z")).toBeVisible();
  });

  it("keeps a known raw error code and safe backend message beside localized guidance", () => {
    render(
      <ErrorState
        code="product_database_unavailable"
        title="产品数据库不可用"
        message="Safe backend detail"
        requestId="raw-request-id"
      />,
      { locale: "zh-CN" },
    );
    expect(screen.getByRole("heading", { name: "产品数据库不可用" })).toBeVisible();
    expect(screen.getByText("错误码：product_database_unavailable")).toBeVisible();
    expect(screen.getByText("Safe backend detail")).toBeVisible();
    expect(screen.getByText("请求 raw-request-id")).toBeVisible();
  });
});
