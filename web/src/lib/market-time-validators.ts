import type { components } from "@/generated/api-types";

type Schemas = components["schemas"];
type TradingCalendar = Schemas["TradingCalendarResponse"];
type TradingCalendarDetail = Schemas["TradingCalendarDetailResponse"];
type ReplaySession = Schemas["ReplaySessionResponse"];
type ReplayDetail = Schemas["MarketDataReplayDetailResponse"];

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function nullableString(value: unknown): value is string | null {
  return value === null || string(value);
}

function nonNegativeInteger(value: unknown): value is number {
  return Number.isInteger(value) && (value as number) >= 0;
}

function one(value: unknown): value is 1 {
  return value === 1;
}

function arrayOf(
  value: unknown,
  validator: (item: unknown) => boolean,
): value is unknown[] {
  return Array.isArray(value) && value.every(validator);
}

export function isReplayStatus(
  value: unknown,
): value is ReplaySession["status"] {
  return (
    value === "ready" ||
    value === "running" ||
    value === "paused" ||
    value === "completed"
  );
}

export function isTradingCalendar(value: unknown): value is TradingCalendar {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.id) &&
    string(value.market) &&
    string(value.timezone) &&
    nonNegativeInteger(value.calendar_version) &&
    string(value.created_at)
  );
}

function isTradingSession(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.id) &&
    string(value.calendar_id) &&
    string(value.trading_date) &&
    string(value.open_time) &&
    string(value.close_time) &&
    string(value.session_type)
  );
}

export function isTradingCalendarListResponse(
  value: unknown,
): value is TradingCalendar[] {
  return arrayOf(value, isTradingCalendar);
}

export function isTradingCalendarDetailResponse(
  value: unknown,
): value is TradingCalendarDetail {
  if (
    !object(value) ||
    !isTradingCalendar(value.calendar) ||
    !arrayOf(value.sessions, isTradingSession)
  ) {
    return false;
  }
  const calendar = value.calendar as TradingCalendar;
  return value.sessions.every(
    (session) =>
      object(session) && session.calendar_id === calendar.id,
  );
}

function isReplayCursor(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.replay_id) &&
    string(value.event_stream_digest) &&
    nonNegativeInteger(value.position) &&
    nullableString(value.last_event_id) &&
    nullableString(value.current_event_time) &&
    isReplayStatus(value.status)
  );
}

export function isReplaySession(value: unknown): value is ReplaySession {
  if (
    !object(value) ||
    !one(value.schema_version) ||
    !string(value.replay_id) ||
    !isReplayStatus(value.status) ||
    !nullableString(value.start_time) ||
    !nullableString(value.current_time) ||
    !isReplayCursor(value.cursor)
  ) {
    return false;
  }
  return (
    object(value.cursor) &&
    value.cursor.replay_id === value.replay_id &&
    value.cursor.status === value.status
  );
}

export function isReplaySessionListResponse(
  value: unknown,
): value is ReplaySession[] {
  return arrayOf(value, isReplaySession);
}

function isMarketDataEvent(value: unknown): boolean {
  return (
    object(value) &&
    one(value.schema_version) &&
    string(value.event_id) &&
    string(value.instrument_id) &&
    string(value.event_time) &&
    string(value.event_type) &&
    object(value.payload) &&
    string(value.source)
  );
}

export function isMarketDataReplayDetailResponse(
  value: unknown,
): value is ReplayDetail {
  if (
    !object(value) ||
    !one(value.record_schema_version) ||
    !isReplaySession(value.session) ||
    !nonNegativeInteger(value.event_count) ||
    !arrayOf(value.events, isMarketDataEvent)
  ) {
    return false;
  }
  return (
    value.event_count === value.events.length &&
    value.session.cursor.position <= value.event_count
  );
}
