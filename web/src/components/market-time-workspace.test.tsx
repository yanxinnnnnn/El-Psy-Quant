import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MarketDataReplayDetailView } from "@/components/market-data-replay-detail-view";
import { MarketTimeWorkspace } from "@/components/market-time-workspace";
import { TradingCalendarDetailView } from "@/components/trading-calendar-detail-view";
import { render, screen, within } from "@/test/render";
import {
  replayDetail,
  replaySessions,
  tradingCalendarDetail,
  tradingCalendars,
} from "@/test/market-time-fixtures";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "market-time-workspace-request",
    },
  });
}

function routeFetcher() {
  return vi.fn<typeof fetch>(async (input) => {
    const url = String(input);
    if (url.includes("/market-time/replays/")) return response(replayDetail);
    if (url.includes("/market-time/calendars/")) {
      return response(tradingCalendarDetail);
    }
    if (url.includes("/market-time/replays")) return response(replaySessions);
    return response(tradingCalendars);
  });
}

describe("Founder Replay Workspace", () => {
  it("shows ordered replay and calendar inspection cards without mutation controls", async () => {
    const fetcher = routeFetcher();
    vi.stubGlobal("fetch", fetcher);

    render(<MarketTimeWorkspace />);

    expect(await screen.findByRole("heading", {
      name: "Founder Replay Workspace",
    })).toBeVisible();
    expect(screen.getByRole("link", { name: "Inspect replay" }))
      .toHaveAttribute("href", "/market-time/replays/replay-194");
    expect(screen.getByRole("link", { name: "Inspect sessions" }))
      .toHaveAttribute("href", "/market-time/calendars/xnys-2026-v1");
    expect(screen.getByText("paused")).toBeVisible();
    expect(screen.queryByRole("button", { name: /pause|resume|advance|buy|sell/i }))
      .not.toBeInTheDocument();
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET"))
      .toBe(true);
  });

  it("applies replay status as a read-only GET inspection filter", async () => {
    const fetcher = routeFetcher();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<MarketTimeWorkspace />);
    await screen.findByText("replay-194");

    await user.selectOptions(
      screen.getByLabelText("Replay status"),
      "paused",
    );
    await user.click(within(screen.getByRole("form", {
      name: "Replay inspection filters",
    })).getByRole("button", { name: "Apply filter" }));

    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/market-time/replays?status=paused",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("visualizes returned lifecycle, cursor, and exact event order", async () => {
    vi.stubGlobal("fetch", routeFetcher());
    render(<MarketDataReplayDetailView replayId="replay-194" />);

    expect(await screen.findByRole("heading", { name: "Replay checkpoint" }))
      .toBeVisible();
    expect(screen.getByRole("progressbar")).toHaveAttribute("value", "1");
    expect(screen.getByRole("progressbar")).toHaveAttribute("max", "2");
    expect(screen.getByRole("list", {
      name: "Replay lifecycle states with the current returned state marked",
    })).toHaveTextContent("paused");
    const timeline = screen.getByRole("list", {
      name: "Market data events in exact API order",
    });
    const eventIds = within(timeline).getAllByText(/^event-00[12]$/);
    expect(eventIds.map((node) => node.textContent)).toEqual([
      "event-001",
      "event-002",
    ]);
    expect(within(timeline).getByText(/"ask": 101/)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("inspects calendar sessions with validated read-only query filters", async () => {
    const fetcher = routeFetcher();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<TradingCalendarDetailView calendarId="xnys-2026-v1" />);

    expect(await screen.findByRole("heading", { name: "XNYS" })).toBeVisible();
    expect(screen.getByRole("table", {
      name: "Trading sessions in exact API order",
    })).toHaveTextContent("xnys-2026-07-28-regular");
    await user.type(screen.getByLabelText("Start date"), "2026-07-28");
    await user.type(screen.getByLabelText("End date"), "2026-07-28");
    await user.type(screen.getByLabelText("Session type"), "regular");
    await user.click(screen.getByRole("button", {
      name: "Apply inspection filters",
    }));

    expect(fetcher).toHaveBeenCalledWith(
      "/api/backend/api/v1/market-time/calendars/xnys-2026-v1?start_date=2026-07-28&end_date=2026-07-28&session_type=regular",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("renders Simplified Chinese presentation while preserving raw authority values", async () => {
    vi.stubGlobal("fetch", routeFetcher());
    render(<MarketTimeWorkspace />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", { name: "创始人重放工作台" }))
      .toBeVisible();
    expect(screen.getByText("paused")).toBeVisible();
    expect(screen.getByText("replay-194")).toBeVisible();
    expect(screen.getByText("America/New_York")).toBeVisible();
  });
});
