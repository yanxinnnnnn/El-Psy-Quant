"""Immutable trading-calendar and trading-session definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MARKET_TIME_RECORD_SCHEMA_VERSION = 1

MAX_MARKET_TIME_ID_LENGTH = 512
MAX_MARKET_LENGTH = 64
MAX_TIMEZONE_LENGTH = 128
MAX_SESSION_TYPE_LENGTH = 64

_MARKET_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._:-]{0,63}")
_SESSION_TYPE_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}")


def _bounded_string(
    value: object,
    *,
    field_name: str,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(normalized) > maximum_length:
        raise ValueError(
            f"{field_name} must be at most {maximum_length} characters"
        )
    return normalized


def _market(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="market",
        maximum_length=MAX_MARKET_LENGTH,
    ).upper()
    if _MARKET_PATTERN.fullmatch(normalized) is None:
        raise ValueError("market must be a normalized market identifier")
    return normalized


def _timezone_name(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="timezone",
        maximum_length=MAX_TIMEZONE_LENGTH,
    )
    try:
        ZoneInfo(normalized)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone must be a valid IANA timezone") from exc
    return normalized


def _positive_version(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("calendar_version must be a positive integer")
    return value


def _aware_utc_datetime(value: object, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime"
        ) from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime"
        ) from exc


def _trading_date(value: object) -> date:
    if type(value) is not date:
        raise ValueError("trading_date must be a date")
    return value


def _session_type(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="session_type",
        maximum_length=MAX_SESSION_TYPE_LENGTH,
    ).lower()
    if _SESSION_TYPE_PATTERN.fullmatch(normalized) is None:
        raise ValueError("session_type must be a normalized identifier")
    return normalized


@dataclass(frozen=True)
class TradingCalendar:
    """One immutable versioned market-calendar definition."""

    id: str
    market: str
    timezone: str
    calendar_version: int
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "id",
            _bounded_string(
                self.id,
                field_name="id",
                maximum_length=MAX_MARKET_TIME_ID_LENGTH,
            ),
        )
        object.__setattr__(self, "market", _market(self.market))
        object.__setattr__(self, "timezone", _timezone_name(self.timezone))
        object.__setattr__(
            self,
            "calendar_version",
            _positive_version(self.calendar_version),
        )
        object.__setattr__(
            self,
            "created_at",
            _aware_utc_datetime(self.created_at, field_name="created_at"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible calendar definition."""
        return {
            "schema_version": MARKET_TIME_RECORD_SCHEMA_VERSION,
            "id": self.id,
            "market": self.market,
            "timezone": self.timezone,
            "calendar_version": self.calendar_version,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class TradingSession:
    """One immutable market session with absolute time boundaries."""

    id: str
    calendar_id: str
    trading_date: date
    open_time: datetime
    close_time: datetime
    session_type: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "id",
            _bounded_string(
                self.id,
                field_name="id",
                maximum_length=MAX_MARKET_TIME_ID_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "calendar_id",
            _bounded_string(
                self.calendar_id,
                field_name="calendar_id",
                maximum_length=MAX_MARKET_TIME_ID_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "trading_date",
            _trading_date(self.trading_date),
        )
        normalized_open = _aware_utc_datetime(
            self.open_time,
            field_name="open_time",
        )
        normalized_close = _aware_utc_datetime(
            self.close_time,
            field_name="close_time",
        )
        if normalized_open >= normalized_close:
            raise ValueError("open_time must be earlier than close_time")
        object.__setattr__(self, "open_time", normalized_open)
        object.__setattr__(self, "close_time", normalized_close)
        object.__setattr__(
            self,
            "session_type",
            _session_type(self.session_type),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible session definition."""
        return {
            "schema_version": MARKET_TIME_RECORD_SCHEMA_VERSION,
            "id": self.id,
            "calendar_id": self.calendar_id,
            "trading_date": self.trading_date.isoformat(),
            "open_time": self.open_time.isoformat(),
            "close_time": self.close_time.isoformat(),
            "session_type": self.session_type,
        }


def validate_trading_session_for_calendar(
    *,
    calendar: TradingCalendar,
    session: TradingSession,
) -> TradingSession:
    """Validate one session against its calendar's identity and local date."""
    if type(calendar) is not TradingCalendar:
        raise ValueError("calendar must be a TradingCalendar")
    if type(session) is not TradingSession:
        raise ValueError("session must be a TradingSession")
    if session.calendar_id != calendar.id:
        raise ValueError("session must reference the exact calendar")

    market_timezone = ZoneInfo(calendar.timezone)
    local_open_date = session.open_time.astimezone(market_timezone).date()
    local_close_date = session.close_time.astimezone(market_timezone).date()
    if local_open_date != session.trading_date:
        raise ValueError("open_time must fall on trading_date in market timezone")
    if local_close_date not in (
        session.trading_date,
        session.trading_date + timedelta(days=1),
    ):
        raise ValueError(
            "close_time must fall on trading_date or the following local date"
        )
    return session


def sort_and_validate_trading_sessions(
    *,
    calendar: TradingCalendar,
    sessions: tuple[TradingSession, ...] | list[TradingSession],
) -> tuple[TradingSession, ...]:
    """Validate and deterministically order non-overlapping sessions."""
    if type(calendar) is not TradingCalendar:
        raise ValueError("calendar must be a TradingCalendar")
    if not isinstance(sessions, (tuple, list)):
        raise ValueError("sessions must be a tuple or list")

    validated: list[TradingSession] = []
    identities: set[str] = set()
    for session in sessions:
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=session,
        )
        if session.id in identities:
            raise ValueError("session identities must be unique")
        identities.add(session.id)
        validated.append(session)

    ordered = tuple(
        sorted(
            validated,
            key=lambda item: (
                item.open_time,
                item.close_time,
                item.session_type,
                item.id,
            ),
        )
    )
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.open_time < previous.close_time:
            raise ValueError("trading sessions must not overlap")
    return ordered


def create_trading_calendar(
    *,
    id: str,
    market: str,
    timezone: str,
    calendar_version: int,
    created_at: datetime,
) -> TradingCalendar:
    """Create one validated immutable calendar definition."""
    return TradingCalendar(
        id=id,
        market=market,
        timezone=timezone,
        calendar_version=calendar_version,
        created_at=created_at,
    )


def create_trading_session(
    *,
    id: str,
    calendar_id: str,
    trading_date: date,
    open_time: datetime,
    close_time: datetime,
    session_type: str,
) -> TradingSession:
    """Create one validated immutable session definition."""
    return TradingSession(
        id=id,
        calendar_id=calendar_id,
        trading_date=trading_date,
        open_time=open_time,
        close_time=close_time,
        session_type=session_type,
    )
