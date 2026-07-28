import { describe, expect, it, vi } from "vitest";

import {
  fetchMarketDataReplayDetail,
  fetchMarketDataReplays,
  fetchTradingCalendarDetail,
  fetchTradingCalendars,
} from "@/lib/api-client";
import {
  replayDetail,
  replaySessions,
  tradingCalendarDetail,
  tradingCalendars,
} from "@/test/market-time-fixtures";

function response(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "market-time-client-request",
    },
  });
}

describe("market-time generated-contract client", () => {
  it("uses exactly the four versioned read-only routes with encoded identities and filters", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(tradingCalendars))
      .mockResolvedValueOnce(response(tradingCalendarDetail))
      .mockResolvedValueOnce(response(replaySessions))
      .mockResolvedValueOnce(response(replayDetail));

    await fetchTradingCalendars({ market: "XNYS" }, fetcher);
    await fetchTradingCalendarDetail(
      "calendar / % ?",
      {
        startDate: "2026-07-01",
        endDate: "2026-07-31",
        sessionType: "regular",
      },
      fetcher,
    );
    await fetchMarketDataReplays({ status: "paused" }, fetcher);
    await fetchMarketDataReplayDetail("replay / % ?", fetcher);

    expect(fetcher.mock.calls.map(([url]) => url)).toEqual([
      "/api/backend/api/v1/market-time/calendars?market=XNYS",
      "/api/backend/api/v1/market-time/calendars/calendar%20%2F%20%25%20%3F?start_date=2026-07-01&end_date=2026-07-31&session_type=regular",
      "/api/backend/api/v1/market-time/replays?status=paused",
      "/api/backend/api/v1/market-time/replays/replay%20%2F%20%25%20%3F",
    ]);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET"))
      .toBe(true);
    expect(fetcher.mock.calls.every(([, init]) => init?.body === undefined))
      .toBe(true);
  });

  it("fails closed when replay cursor bindings or event counts disagree", async () => {
    const malformed = structuredClone(replayDetail);
    malformed.session.cursor.replay_id = "different-replay";
    malformed.event_count = 99;
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response(malformed));

    await expect(fetchMarketDataReplayDetail("replay-194", fetcher))
      .rejects.toMatchObject({
        code: "api_response_invalid",
        requestId: "market-time-client-request",
      });
  });

  it("rejects unsupported client-side filters without sending a request", () => {
    const fetcher = vi.fn<typeof fetch>();
    expect(() => fetchTradingCalendars({ market: " XNYS" }, fetcher))
      .toThrow(TypeError);
    expect(() => fetchMarketDataReplays(
      { status: "stopped" as never },
      fetcher,
    )).toThrow(TypeError);
    expect(fetcher).not.toHaveBeenCalled();
  });
});
