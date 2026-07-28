"""Deterministic in-memory replay over canonical market-data events."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from el_psy_quant.market_time.events import (
    MAX_MARKET_DATA_EVENT_ID_LENGTH,
    MarketDataEvent,
    sort_and_validate_market_data_events,
)

MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION = 1
SUPPORTED_MARKET_DATA_REPLAY_STATUSES = (
    "ready",
    "running",
    "paused",
    "completed",
)

MarketDataReplayStatus = Literal[
    "ready",
    "running",
    "paused",
    "completed",
]

MAX_MARKET_DATA_REPLAY_ID_LENGTH = 512
_REPLAY_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,511}")
_EVENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,511}")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _replay_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("replay_id must be a normalized replay identifier")
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > MAX_MARKET_DATA_REPLAY_ID_LENGTH
        or _REPLAY_ID_PATTERN.fullmatch(normalized) is None
    ):
        raise ValueError("replay_id must be a normalized replay identifier")
    return normalized


def _status(value: object) -> MarketDataReplayStatus:
    if not isinstance(value, str) or value not in (
        SUPPORTED_MARKET_DATA_REPLAY_STATUSES
    ):
        supported = ", ".join(SUPPORTED_MARKET_DATA_REPLAY_STATUSES)
        raise ValueError(f"status must be one of: {supported}")
    return value  # type: ignore[return-value]


def _stream_digest(value: object) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(
            "event_stream_digest must be a lowercase SHA-256 digest"
        )
    return value


def _position(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("position must be a non-negative integer")
    return value


def _last_event_id(value: object) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) > MAX_MARKET_DATA_EVENT_ID_LENGTH
        or _EVENT_ID_PATTERN.fullmatch(value) is None
    ):
        raise ValueError("last_event_id must be a normalized event identifier")
    return value


def _utc_time(value: object, *, field_name: str) -> datetime | None:
    if value is None:
        return None
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


def _event_stream_digest(events: tuple[MarketDataEvent, ...]) -> str:
    serialized = f"[{','.join(event.to_json() for event in events)}]"
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReplayCursor:
    """Immutable replay checkpoint bound to one exact canonical event stream."""

    replay_id: str
    event_stream_digest: str
    position: int
    last_event_id: str | None
    current_event_time: datetime | None
    status: MarketDataReplayStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "replay_id", _replay_id(self.replay_id))
        object.__setattr__(
            self,
            "event_stream_digest",
            _stream_digest(self.event_stream_digest),
        )
        object.__setattr__(self, "position", _position(self.position))
        object.__setattr__(
            self,
            "last_event_id",
            _last_event_id(self.last_event_id),
        )
        object.__setattr__(
            self,
            "current_event_time",
            _utc_time(
                self.current_event_time,
                field_name="current_event_time",
            ),
        )
        object.__setattr__(self, "status", _status(self.status))

        has_last_event = self.last_event_id is not None
        has_current_time = self.current_event_time is not None
        if has_last_event != has_current_time:
            raise ValueError(
                "last_event_id and current_event_time must be paired"
            )
        if self.position == 0 and has_last_event:
            raise ValueError("position zero cannot reference a consumed event")
        if self.position > 0 and not has_last_event:
            raise ValueError(
                "positive position requires the last consumed event"
            )
        if self.status == "ready" and self.position != 0:
            raise ValueError("ready replay cursor must be at position zero")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible cursor representation."""
        return {
            "schema_version": MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION,
            "replay_id": self.replay_id,
            "event_stream_digest": self.event_stream_digest,
            "position": self.position,
            "last_event_id": self.last_event_id,
            "current_event_time": (
                None
                if self.current_event_time is None
                else self.current_event_time.isoformat()
            ),
            "status": self.status,
        }


@dataclass(frozen=True)
class ReplaySession:
    """Immutable inspection snapshot for one replay lifecycle state."""

    replay_id: str
    status: MarketDataReplayStatus
    start_time: datetime | None
    current_time: datetime | None
    cursor: ReplayCursor

    def __post_init__(self) -> None:
        object.__setattr__(self, "replay_id", _replay_id(self.replay_id))
        object.__setattr__(self, "status", _status(self.status))
        object.__setattr__(
            self,
            "start_time",
            _utc_time(self.start_time, field_name="start_time"),
        )
        object.__setattr__(
            self,
            "current_time",
            _utc_time(self.current_time, field_name="current_time"),
        )
        if type(self.cursor) is not ReplayCursor:
            raise ValueError("cursor must be a ReplayCursor")
        if self.cursor.replay_id != self.replay_id:
            raise ValueError("session and cursor replay_id must match")
        if self.cursor.status != self.status:
            raise ValueError("session and cursor status must match")
        if self.cursor.current_event_time != self.current_time:
            raise ValueError("session and cursor current time must match")
        if self.current_time is not None and self.start_time is None:
            raise ValueError("current_time requires start_time")
        if (
            self.start_time is not None
            and self.current_time is not None
            and self.current_time < self.start_time
        ):
            raise ValueError("current_time cannot precede start_time")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible session representation."""
        return {
            "schema_version": MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION,
            "replay_id": self.replay_id,
            "status": self.status,
            "start_time": (
                None
                if self.start_time is None
                else self.start_time.isoformat()
            ),
            "current_time": (
                None
                if self.current_time is None
                else self.current_time.isoformat()
            ),
            "cursor": self.cursor.to_dict(),
        }


class MarketDataReplayEngine:
    """Consume canonical market events with explicit replay lifecycle state."""

    def __init__(
        self,
        *,
        replay_id: str,
        events: tuple[MarketDataEvent, ...] | list[MarketDataEvent],
        cursor: ReplayCursor | None = None,
    ) -> None:
        self._replay_id = _replay_id(replay_id)
        self._events = sort_and_validate_market_data_events(events)
        self._event_stream_digest = _event_stream_digest(self._events)
        self._start_time = (
            None if not self._events else self._events[0].event_time
        )
        if cursor is None:
            self._cursor = ReplayCursor(
                replay_id=self._replay_id,
                event_stream_digest=self._event_stream_digest,
                position=0,
                last_event_id=None,
                current_event_time=None,
                status="ready",
            )
        else:
            self._validate_cursor(cursor)
            self._cursor = cursor

    @property
    def events(self) -> tuple[MarketDataEvent, ...]:
        """Return the immutable canonical replay input order."""
        return self._events

    @property
    def cursor(self) -> ReplayCursor:
        """Return the current immutable restart checkpoint."""
        return self._cursor

    @property
    def session(self) -> ReplaySession:
        """Return the current immutable replay inspection snapshot."""
        return ReplaySession(
            replay_id=self._replay_id,
            status=self._cursor.status,
            start_time=self._start_time,
            current_time=self._cursor.current_event_time,
            cursor=self._cursor,
        )

    def _validate_cursor(self, cursor: ReplayCursor) -> None:
        if type(cursor) is not ReplayCursor:
            raise ValueError("cursor must be a ReplayCursor")
        if cursor.replay_id != self._replay_id:
            raise ValueError("cursor replay_id does not match replay")
        if cursor.event_stream_digest != self._event_stream_digest:
            raise ValueError("cursor event stream does not match replay input")
        if cursor.position > len(self._events):
            raise ValueError("cursor position exceeds replay input")

        if not self._events and cursor.status == "ready":
            pass
        elif cursor.position == len(self._events):
            if cursor.status != "completed":
                raise ValueError(
                    "cursor at end of replay must be completed"
                )
        elif cursor.status == "completed":
            raise ValueError(
                "completed cursor must be at end of replay input"
            )

        if cursor.status in ("running", "paused") and not self._events:
            raise ValueError("empty replay cannot be running or paused")

        if cursor.position == 0:
            if (
                cursor.last_event_id is not None
                or cursor.current_event_time is not None
            ):
                raise ValueError(
                    "cursor at position zero cannot reference an event"
                )
            return

        last_event = self._events[cursor.position - 1]
        if cursor.last_event_id != last_event.event_id:
            raise ValueError(
                "cursor last_event_id does not match replay position"
            )
        if cursor.current_event_time != last_event.event_time:
            raise ValueError(
                "cursor current_event_time does not match replay position"
            )

    def _replace_cursor(
        self,
        *,
        status: MarketDataReplayStatus,
        position: int | None = None,
        last_event_id: str | None = None,
        current_event_time: datetime | None = None,
    ) -> None:
        if position is None:
            position = self._cursor.position
            last_event_id = self._cursor.last_event_id
            current_event_time = self._cursor.current_event_time
        cursor = ReplayCursor(
            replay_id=self._replay_id,
            event_stream_digest=self._event_stream_digest,
            position=position,
            last_event_id=last_event_id,
            current_event_time=current_event_time,
            status=status,
        )
        self._validate_cursor(cursor)
        self._cursor = cursor

    def start(self) -> ReplaySession:
        """Start one ready replay, completing an empty input immediately."""
        if self._cursor.status != "ready":
            raise ValueError("only a ready replay can be started")
        target: MarketDataReplayStatus = (
            "running" if self._events else "completed"
        )
        self._replace_cursor(status=target)
        return self.session

    def pause(self) -> ReplaySession:
        """Pause one running replay without advancing its cursor."""
        if self._cursor.status != "running":
            raise ValueError("only a running replay can be paused")
        self._replace_cursor(status="paused")
        return self.session

    def resume(self) -> ReplaySession:
        """Resume one paused replay without advancing its cursor."""
        if self._cursor.status != "paused":
            raise ValueError("only a paused replay can be resumed")
        self._replace_cursor(status="running")
        return self.session

    def next_event(self) -> MarketDataEvent:
        """Consume exactly one next event and advance the cursor atomically."""
        if self._cursor.status != "running":
            raise ValueError("next event requires a running replay")
        position = self._cursor.position
        if position >= len(self._events):
            raise ValueError("replay cursor has no next event")

        event = self._events[position]
        next_position = position + 1
        next_status: MarketDataReplayStatus = (
            "completed"
            if next_position == len(self._events)
            else "running"
        )
        self._replace_cursor(
            status=next_status,
            position=next_position,
            last_event_id=event.event_id,
            current_event_time=event.event_time,
        )
        return event

    def iter_remaining(self) -> Iterator[MarketDataEvent]:
        """Yield remaining events until this running replay completes."""
        if self._cursor.status != "running":
            raise ValueError("event iteration requires a running replay")
        while self._cursor.status == "running":
            yield self.next_event()
