import type {
  MarketDataReplayDetailResponse,
  ReplaySessionListResponse,
  TradingCalendarDetailResponse,
  TradingCalendarListResponse,
} from "@/lib/api-client";

export const replaySessions: ReplaySessionListResponse = [
  {
    schema_version: 1,
    replay_id: "replay-194",
    status: "paused",
    start_time: "2026-07-28T13:30:00+00:00",
    current_time: "2026-07-28T13:30:00+00:00",
    cursor: {
      schema_version: 1,
      replay_id: "replay-194",
      event_stream_digest: "a".repeat(64),
      position: 1,
      last_event_id: "event-001",
      current_event_time: "2026-07-28T13:30:00+00:00",
      status: "paused",
    },
  },
];

export const replayDetail: MarketDataReplayDetailResponse = {
  record_schema_version: 1,
  session: replaySessions[0],
  event_count: 2,
  events: [
    {
      schema_version: 1,
      event_id: "event-001",
      instrument_id: "XNYS:AAPL",
      event_time: "2026-07-28T13:30:00+00:00",
      event_type: "quote",
      payload: { ask: 101, bid: 100.5 },
      source: "fixture:web",
    },
    {
      schema_version: 1,
      event_id: "event-002",
      instrument_id: "XNYS:AAPL",
      event_time: "2026-07-28T13:31:00+00:00",
      event_type: "trade",
      payload: { price: 100.75, size: 10 },
      source: "fixture:web",
    },
  ],
};

export const tradingCalendars: TradingCalendarListResponse = [
  {
    schema_version: 1,
    id: "xnys-2026-v1",
    market: "XNYS",
    timezone: "America/New_York",
    calendar_version: 1,
    created_at: "2026-07-28T08:00:00+00:00",
  },
];

export const tradingCalendarDetail: TradingCalendarDetailResponse = {
  calendar: tradingCalendars[0],
  sessions: [
    {
      schema_version: 1,
      id: "xnys-2026-07-28-regular",
      calendar_id: "xnys-2026-v1",
      trading_date: "2026-07-28",
      open_time: "2026-07-28T13:30:00+00:00",
      close_time: "2026-07-28T20:00:00+00:00",
      session_type: "regular",
    },
  ],
};
