"""Exact M32 provenance references for future M33 signal evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from el_psy_quant.market_time import (
    MarketDataEvent,
    ReplayCursor,
    ReplaySession,
    TradingCalendar,
    TradingSession,
    validate_trading_session_for_calendar,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    normalize_utc_datetime,
    reject_public_construction,
    validate_digest,
)

STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION = 1

_MAX_MARKET_REFERENCE_ID_LENGTH = 512


@dataclass(frozen=True, init=False)
class StrategySignalMarketReference:
    """One compact immutable anchor to an exact consumed M32 replay event."""

    schema_version: int
    calendar_id: str
    calendar_version: int
    trading_session_id: str
    replay_id: str
    event_stream_digest: str
    cursor_position: int
    last_event_id: str
    signal_event_id: str
    signal_time: datetime
    instrument_id: str
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible M32 provenance anchor."""
        return {
            "schema_version": self.schema_version,
            "calendar_id": self.calendar_id,
            "calendar_version": self.calendar_version,
            "trading_session_id": self.trading_session_id,
            "replay_id": self.replay_id,
            "event_stream_digest": self.event_stream_digest,
            "cursor_position": self.cursor_position,
            "last_event_id": self.last_event_id,
            "signal_event_id": self.signal_event_id,
            "signal_time": self.signal_time.isoformat(),
            "instrument_id": self.instrument_id,
            "reference_digest": self.reference_digest,
        }


def _reference_payload_without_digest(
    *,
    schema_version: int,
    calendar_id: str,
    calendar_version: int,
    trading_session_id: str,
    replay_id: str,
    event_stream_digest: str,
    cursor_position: int,
    last_event_id: str,
    signal_event_id: str,
    signal_time: datetime,
    instrument_id: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "calendar_id": calendar_id,
        "calendar_version": calendar_version,
        "trading_session_id": trading_session_id,
        "replay_id": replay_id,
        "event_stream_digest": event_stream_digest,
        "cursor_position": cursor_position,
        "last_event_id": last_event_id,
        "signal_event_id": signal_event_id,
        "signal_time": signal_time.isoformat(),
        "instrument_id": instrument_id,
    }


def _validate_exact_calendar(value: object) -> TradingCalendar:
    if type(value) is not TradingCalendar:
        raise ValueError("calendar must be a TradingCalendar")
    try:
        rebuilt = TradingCalendar(
            id=value.id,
            market=value.market,
            timezone=value.timezone,
            calendar_version=value.calendar_version,
            created_at=value.created_at,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("calendar must be a valid TradingCalendar") from exc
    if rebuilt != value:
        raise ValueError("calendar must be a valid TradingCalendar")
    return value


def _validate_exact_session(value: object) -> TradingSession:
    if type(value) is not TradingSession:
        raise ValueError("session must be a TradingSession")
    try:
        rebuilt = TradingSession(
            id=value.id,
            calendar_id=value.calendar_id,
            trading_date=value.trading_date,
            open_time=value.open_time,
            close_time=value.close_time,
            session_type=value.session_type,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("session must be a valid TradingSession") from exc
    if rebuilt != value:
        raise ValueError("session must be a valid TradingSession")
    return value


def _validate_exact_replay_session(value: object) -> ReplaySession:
    if type(value) is not ReplaySession:
        raise ValueError("replay_session must be a ReplaySession")
    try:
        cursor = value.cursor
        rebuilt_cursor = ReplayCursor(
            replay_id=cursor.replay_id,
            event_stream_digest=cursor.event_stream_digest,
            position=cursor.position,
            last_event_id=cursor.last_event_id,
            current_event_time=cursor.current_event_time,
            status=cursor.status,
        )
        rebuilt = ReplaySession(
            replay_id=value.replay_id,
            status=value.status,
            start_time=value.start_time,
            current_time=value.current_time,
            cursor=rebuilt_cursor,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(
            "replay_session must be a valid ReplaySession"
        ) from exc
    if rebuilt != value:
        raise ValueError("replay_session must be a valid ReplaySession")
    return value


def _validate_exact_event(value: object) -> MarketDataEvent:
    if type(value) is not MarketDataEvent:
        raise ValueError("current_event must be a MarketDataEvent")
    try:
        rebuilt = MarketDataEvent(
            event_id=value.event_id,
            instrument_id=value.instrument_id,
            event_time=value.event_time,
            event_type=value.event_type,
            payload=value.payload,
            schema_version=value.schema_version,
            source=value.source,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(
            "current_event must be a valid MarketDataEvent"
        ) from exc
    if rebuilt != value:
        raise ValueError("current_event must be a valid MarketDataEvent")
    return value


def _build_reference(
    *,
    schema_version: int,
    calendar_id: str,
    calendar_version: int,
    trading_session_id: str,
    replay_id: str,
    event_stream_digest: str,
    cursor_position: int,
    last_event_id: str,
    signal_event_id: str,
    signal_time: datetime,
    instrument_id: str,
) -> StrategySignalMarketReference:
    payload = _reference_payload_without_digest(
        schema_version=schema_version,
        calendar_id=calendar_id,
        calendar_version=calendar_version,
        trading_session_id=trading_session_id,
        replay_id=replay_id,
        event_stream_digest=event_stream_digest,
        cursor_position=cursor_position,
        last_event_id=last_event_id,
        signal_event_id=signal_event_id,
        signal_time=signal_time,
        instrument_id=instrument_id,
    )
    result = object.__new__(StrategySignalMarketReference)
    object.__setattr__(result, "schema_version", schema_version)
    object.__setattr__(result, "calendar_id", calendar_id)
    object.__setattr__(result, "calendar_version", calendar_version)
    object.__setattr__(result, "trading_session_id", trading_session_id)
    object.__setattr__(result, "replay_id", replay_id)
    object.__setattr__(result, "event_stream_digest", event_stream_digest)
    object.__setattr__(result, "cursor_position", cursor_position)
    object.__setattr__(result, "last_event_id", last_event_id)
    object.__setattr__(result, "signal_event_id", signal_event_id)
    object.__setattr__(result, "signal_time", signal_time)
    object.__setattr__(result, "instrument_id", instrument_id)
    object.__setattr__(
        result,
        "reference_digest",
        canonical_digest(payload),
    )
    return result


def create_strategy_signal_market_reference(
    *,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_session: ReplaySession,
    current_event: MarketDataEvent,
) -> StrategySignalMarketReference:
    """Bind one signal input to trusted, concrete M32 domain authority."""
    valid_calendar = _validate_exact_calendar(calendar)
    valid_session = _validate_exact_session(session)
    validate_trading_session_for_calendar(
        calendar=valid_calendar,
        session=valid_session,
    )
    valid_replay = _validate_exact_replay_session(replay_session)
    valid_event = _validate_exact_event(current_event)

    cursor = valid_replay.cursor
    if cursor.position <= 0:
        raise ValueError("replay cursor must have consumed at least one event")
    if cursor.last_event_id is None or cursor.current_event_time is None:
        raise ValueError("replay cursor must reference its consumed event")
    if valid_event.event_id != cursor.last_event_id:
        raise ValueError("current event ID must match cursor last_event_id")
    if valid_event.event_time != cursor.current_event_time:
        raise ValueError(
            "current event time must match cursor current_event_time"
        )
    if not (
        valid_session.open_time
        <= valid_event.event_time
        <= valid_session.close_time
    ):
        raise ValueError("current event must fall within the trading session")

    return _build_reference(
        schema_version=STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION,
        calendar_id=valid_calendar.id,
        calendar_version=valid_calendar.calendar_version,
        trading_session_id=valid_session.id,
        replay_id=valid_replay.replay_id,
        event_stream_digest=cursor.event_stream_digest,
        cursor_position=cursor.position,
        last_event_id=cursor.last_event_id,
        signal_event_id=cursor.last_event_id,
        signal_time=valid_event.event_time,
        instrument_id=valid_event.instrument_id,
    )


def validate_strategy_signal_market_reference(
    value: object,
) -> StrategySignalMarketReference:
    """Recompute and verify one complete compact market reference."""
    if type(value) is not StrategySignalMarketReference:
        raise ValueError(
            "market_reference must be a StrategySignalMarketReference"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported market reference schema_version")
        calendar_id = normalize_bounded_string(
            value.calendar_id,
            field_name="calendar_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        trading_session_id = normalize_bounded_string(
            value.trading_session_id,
            field_name="trading_session_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        replay_id = normalize_bounded_string(
            value.replay_id,
            field_name="replay_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        last_event_id = normalize_bounded_string(
            value.last_event_id,
            field_name="last_event_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        signal_event_id = normalize_bounded_string(
            value.signal_event_id,
            field_name="signal_event_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        instrument_id = normalize_bounded_string(
            value.instrument_id,
            field_name="instrument_id",
            maximum_length=_MAX_MARKET_REFERENCE_ID_LENGTH,
        )
        event_stream_digest = validate_digest(
            value.event_stream_digest,
            field_name="event_stream_digest",
        )
        if type(value.calendar_version) is not int or value.calendar_version < 1:
            raise ValueError("calendar_version must be a positive integer")
        if type(value.cursor_position) is not int or value.cursor_position < 1:
            raise ValueError("cursor_position must be a positive integer")
        if last_event_id != signal_event_id:
            raise ValueError("signal_event_id must equal last_event_id")
        signal_time = normalize_utc_datetime(
            value.signal_time,
            field_name="signal_time",
        )
        if signal_time != value.signal_time:
            raise ValueError("signal_time must be normalized to UTC")
        rebuilt = _build_reference(
            schema_version=value.schema_version,
            calendar_id=calendar_id,
            calendar_version=value.calendar_version,
            trading_session_id=trading_session_id,
            replay_id=replay_id,
            event_stream_digest=event_stream_digest,
            cursor_position=value.cursor_position,
            last_event_id=last_event_id,
            signal_event_id=signal_event_id,
            signal_time=signal_time,
            instrument_id=instrument_id,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("strategy signal market reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("strategy signal market reference is invalid")
    return value


def _clone_strategy_signal_market_reference(
    value: StrategySignalMarketReference,
) -> StrategySignalMarketReference:
    validate_strategy_signal_market_reference(value)
    return _build_reference(
        schema_version=value.schema_version,
        calendar_id=value.calendar_id,
        calendar_version=value.calendar_version,
        trading_session_id=value.trading_session_id,
        replay_id=value.replay_id,
        event_stream_digest=value.event_stream_digest,
        cursor_position=value.cursor_position,
        last_event_id=value.last_event_id,
        signal_event_id=value.signal_event_id,
        signal_time=value.signal_time,
        instrument_id=value.instrument_id,
    )
