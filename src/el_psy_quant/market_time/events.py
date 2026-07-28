"""Canonical immutable market-data event definitions."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import cast

MARKET_DATA_EVENT_SCHEMA_VERSION = 1
SUPPORTED_MARKET_DATA_EVENT_SCHEMA_VERSIONS = frozenset(
    {MARKET_DATA_EVENT_SCHEMA_VERSION}
)

MAX_MARKET_DATA_EVENT_ID_LENGTH = 512
MAX_MARKET_INSTRUMENT_ID_LENGTH = 512
MAX_MARKET_EVENT_TYPE_LENGTH = 64
MAX_MARKET_EVENT_SOURCE_LENGTH = 256

_EVENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,511}")
_INSTRUMENT_ID_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._:/-]{0,511}")
_EVENT_TYPE_PATTERN = re.compile(r"[a-z][a-z0-9._-]{0,63}")
_SOURCE_PATTERN = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,255}")

_SERIALIZED_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "instrument_id",
        "event_time",
        "event_type",
        "payload",
        "source",
    }
)


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


def _event_id(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="event_id",
        maximum_length=MAX_MARKET_DATA_EVENT_ID_LENGTH,
    )
    if _EVENT_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError("event_id must be a normalized event identifier")
    return normalized


def normalize_market_instrument_id(value: object) -> str:
    """Return one canonical opaque instrument identifier."""
    normalized = _bounded_string(
        value,
        field_name="instrument_id",
        maximum_length=MAX_MARKET_INSTRUMENT_ID_LENGTH,
    ).upper()
    if _INSTRUMENT_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            "instrument_id must be a normalized instrument identifier"
        )
    return normalized


def _event_type(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="event_type",
        maximum_length=MAX_MARKET_EVENT_TYPE_LENGTH,
    ).lower()
    if _EVENT_TYPE_PATTERN.fullmatch(normalized) is None:
        raise ValueError("event_type must be a normalized event identifier")
    return normalized


def _source(value: object) -> str:
    normalized = _bounded_string(
        value,
        field_name="source",
        maximum_length=MAX_MARKET_EVENT_SOURCE_LENGTH,
    ).lower()
    if _SOURCE_PATTERN.fullmatch(normalized) is None:
        raise ValueError("source must be a normalized source identifier")
    return normalized


def _schema_version(value: object) -> int:
    if type(value) is not int:
        raise ValueError("schema_version must be an integer")
    if value not in SUPPORTED_MARKET_DATA_EVENT_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported market-data event schema_version: {value}"
        )
    return value


def _event_time(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("event_time must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            "event_time must be a timezone-aware datetime"
        ) from exc
    if value.tzinfo is None or offset is None:
        raise ValueError("event_time must be a timezone-aware datetime")
    try:
        return value.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise ValueError(
            "event_time must be a timezone-aware datetime"
        ) from exc


def _validated_json_value(value: object, *, path: str) -> object:
    if value is None or type(value) in (bool, int, str):
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    f"{path} must contain valid Unicode"
                ) from exc
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain only finite JSON numbers")
        return value
    if type(value) is list:
        return [
            _validated_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        validated: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings")
            try:
                key.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    f"{path} keys must contain valid Unicode"
                ) from exc
            validated[key] = _validated_json_value(
                item,
                path=f"{path}.{key}",
            )
        return validated
    raise ValueError(f"{path} must contain only JSON-compatible values")


def _canonical_payload_json(value: object) -> str:
    if type(value) is not dict:
        raise ValueError("payload must be a JSON object")
    validated = _validated_json_value(value, path="payload")
    return json.dumps(
        validated,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _parse_serialized_event_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("event_time must be a canonical UTC timestamp string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "event_time must be a canonical UTC timestamp string"
        ) from exc
    normalized = _event_time(parsed)
    if value != normalized.isoformat():
        raise ValueError(
            "event_time must be a canonical UTC timestamp string"
        )
    return normalized


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True, init=False)
class MarketDataEvent:
    """One immutable versioned market-state event."""

    event_id: str
    instrument_id: str
    event_time: datetime
    event_type: str
    schema_version: int
    source: str
    _payload_json: str = field(repr=False)

    def __init__(
        self,
        *,
        event_id: str,
        instrument_id: str,
        event_time: datetime,
        event_type: str,
        payload: object,
        schema_version: int = MARKET_DATA_EVENT_SCHEMA_VERSION,
        source: str,
    ) -> None:
        object.__setattr__(self, "event_id", _event_id(event_id))
        object.__setattr__(
            self,
            "instrument_id",
            normalize_market_instrument_id(instrument_id),
        )
        object.__setattr__(self, "event_time", _event_time(event_time))
        object.__setattr__(self, "event_type", _event_type(event_type))
        object.__setattr__(
            self,
            "schema_version",
            _schema_version(schema_version),
        )
        object.__setattr__(self, "source", _source(source))
        object.__setattr__(
            self,
            "_payload_json",
            _canonical_payload_json(payload),
        )

    @property
    def payload(self) -> dict[str, object]:
        """Return an isolated JSON-compatible copy of the event payload."""
        return cast(dict[str, object], json.loads(self._payload_json))

    @property
    def ordering_key(self) -> tuple[datetime, str]:
        """Return the total replay order key for this event."""
        return (self.event_time, self.event_id)

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-compatible event representation."""
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "instrument_id": self.instrument_id,
            "event_time": self.event_time.isoformat(),
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
        }

    def to_json(self) -> str:
        """Return canonical UTF-8-compatible JSON text."""
        return json.dumps(
            self.to_dict(),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def create_market_data_event(
    *,
    event_id: str,
    instrument_id: str,
    event_time: datetime,
    event_type: str,
    payload: object,
    schema_version: int = MARKET_DATA_EVENT_SCHEMA_VERSION,
    source: str,
) -> MarketDataEvent:
    """Create one validated canonical market-data event."""
    return MarketDataEvent(
        event_id=event_id,
        instrument_id=instrument_id,
        event_time=event_time,
        event_type=event_type,
        payload=payload,
        schema_version=schema_version,
        source=source,
    )


def market_data_event_from_dict(value: object) -> MarketDataEvent:
    """Parse one exact versioned serialized event mapping."""
    if type(value) is not dict:
        raise ValueError("market-data event must be a JSON object")
    if any(not isinstance(key, str) for key in value):
        raise ValueError("market-data event field names must be strings")
    fields = set(value)
    if fields != _SERIALIZED_EVENT_FIELDS:
        missing = sorted(_SERIALIZED_EVENT_FIELDS - fields)
        unknown = sorted(fields - _SERIALIZED_EVENT_FIELDS)
        details: list[str] = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown fields: {', '.join(unknown)}")
        raise ValueError(
            "invalid market-data event fields"
            + (f" ({'; '.join(details)})" if details else "")
        )
    schema_version = _schema_version(value["schema_version"])
    return create_market_data_event(
        event_id=cast(str, value["event_id"]),
        instrument_id=cast(str, value["instrument_id"]),
        event_time=_parse_serialized_event_time(value["event_time"]),
        event_type=cast(str, value["event_type"]),
        payload=value["payload"],
        schema_version=schema_version,
        source=cast(str, value["source"]),
    )


def market_data_event_from_json(value: object) -> MarketDataEvent:
    """Parse one strict JSON market-data event representation."""
    if not isinstance(value, str):
        raise ValueError("serialized market-data event must be a JSON string")
    try:
        parsed = json.loads(
            value,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(
            "serialized market-data event must be valid strict JSON"
        ) from exc
    return market_data_event_from_dict(parsed)


def sort_and_validate_market_data_events(
    events: tuple[MarketDataEvent, ...] | list[MarketDataEvent],
) -> tuple[MarketDataEvent, ...]:
    """Validate unique identities and return deterministic replay order."""
    if not isinstance(events, (tuple, list)):
        raise ValueError("events must be a tuple or list")

    validated: list[MarketDataEvent] = []
    identities: set[str] = set()
    for event in events:
        if type(event) is not MarketDataEvent:
            raise ValueError("events must contain only MarketDataEvent values")
        if event.event_id in identities:
            raise ValueError("market-data event identities must be unique")
        identities.add(event.event_id)
        validated.append(event)
    return tuple(sorted(validated, key=lambda event: event.ordering_key))
