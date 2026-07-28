"""Read-only response contracts for durable market-time inspection."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ReplayStatus = Literal["ready", "running", "paused", "completed"]


class _StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TradingCalendarResponse(_StrictResponse):
    schema_version: Literal[1]
    id: str
    market: str
    timezone: str
    calendar_version: int
    created_at: str


class TradingSessionResponse(_StrictResponse):
    schema_version: Literal[1]
    id: str
    calendar_id: str
    trading_date: str
    open_time: str
    close_time: str
    session_type: str


class TradingCalendarDetailResponse(_StrictResponse):
    calendar: TradingCalendarResponse
    sessions: list[TradingSessionResponse]


class ReplayCursorResponse(_StrictResponse):
    schema_version: Literal[1]
    replay_id: str
    event_stream_digest: str
    position: int
    last_event_id: str | None
    current_event_time: str | None
    status: ReplayStatus


class ReplaySessionResponse(_StrictResponse):
    schema_version: Literal[1]
    replay_id: str
    status: ReplayStatus
    start_time: str | None
    current_time: str | None
    cursor: ReplayCursorResponse


class MarketDataEventResponse(_StrictResponse):
    schema_version: Literal[1]
    event_id: str
    instrument_id: str
    event_time: str
    event_type: str
    payload: dict[str, object]
    source: str


class MarketDataReplayDetailResponse(_StrictResponse):
    record_schema_version: Literal[1]
    session: ReplaySessionResponse
    event_count: int
    events: list[MarketDataEventResponse]


__all__ = [
    "MarketDataEventResponse",
    "MarketDataReplayDetailResponse",
    "ReplayCursorResponse",
    "ReplaySessionResponse",
    "ReplayStatus",
    "TradingCalendarDetailResponse",
    "TradingCalendarResponse",
    "TradingSessionResponse",
]
