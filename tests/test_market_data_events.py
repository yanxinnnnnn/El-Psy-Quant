"""Domain coverage for the canonical market-data event contract."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from el_psy_quant.market_time import (
    MARKET_DATA_EVENT_SCHEMA_VERSION,
    MarketDataEvent,
    create_market_data_event,
    market_data_event_from_dict,
    market_data_event_from_json,
    normalize_market_instrument_id,
    sort_and_validate_market_data_events,
)

_DEFAULT_PAYLOAD = object()


def _event(
    *,
    event_id: str = "event-002",
    instrument_id: str = "xnys:aapl",
    event_time: datetime | None = None,
    event_type: str = "quote",
    payload: object = _DEFAULT_PAYLOAD,
    schema_version: int = MARKET_DATA_EVENT_SCHEMA_VERSION,
    source: str = "fixture:primary",
) -> MarketDataEvent:
    return create_market_data_event(
        event_id=event_id,
        instrument_id=instrument_id,
        event_time=event_time
        or datetime(
            2026,
            7,
            28,
            17,
            30,
            tzinfo=timezone(timedelta(hours=8)),
        ),
        event_type=event_type,
        payload=payload
        if payload is not _DEFAULT_PAYLOAD
        else {
            "ask": "150.02",
            "bid": "150.01",
            "flags": ["firm", "regular"],
            "sequence": 7,
        },
        schema_version=schema_version,
        source=source,
    )


def test_market_data_event_creation_normalizes_authority_fields() -> None:
    event = _event(event_type="QUOTE", source="FIXTURE:PRIMARY")

    assert event.event_id == "event-002"
    assert event.instrument_id == "XNYS:AAPL"
    assert event.event_time == datetime(
        2026,
        7,
        28,
        9,
        30,
        tzinfo=timezone.utc,
    )
    assert event.event_type == "quote"
    assert event.schema_version == 1
    assert event.source == "fixture:primary"
    assert event.payload["sequence"] == 7
    with pytest.raises(FrozenInstanceError):
        event.event_type = "trade"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", "not an id"),
        ("event_type", "not an event"),
        ("source", "not a source"),
    ],
)
def test_event_identifiers_reject_invalid_values(
    field: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "event_id": "event-002",
        "event_type": "quote",
        "source": "fixture:primary",
    }
    values[field] = value
    with pytest.raises(ValueError, match=field):
        _event(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    ["", " ", "XNYS AAPL", "XNYS:AAPL!", 123, None],
)
def test_instrument_identity_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError, match="instrument_id"):
        normalize_market_instrument_id(value)


def test_instrument_identity_is_explicit_and_canonical() -> None:
    assert normalize_market_instrument_id(" xnas:brk.b ") == "XNAS:BRK.B"
    assert normalize_market_instrument_id("crypto:btc/usd") == "CRYPTO:BTC/USD"


@pytest.mark.parametrize("value", [0, 2, -1, True, "1"])
def test_schema_version_rejects_unknown_or_non_integer_values(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _event(schema_version=value)  # type: ignore[arg-type]


def test_event_time_requires_timezone_and_normalizes_to_utc() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _event(event_time=datetime(2026, 7, 28, 9, 30))

    event = _event(
        event_time=datetime(
            2026,
            7,
            28,
            9,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        )
    )
    assert event.event_time.isoformat() == "2026-07-28T13:30:00+00:00"


def test_payload_is_isolated_and_canonical_serialization_is_stable() -> None:
    original = {
        "z": [{"price": "150.01"}],
        "a": {"size": 100, "indicative": False},
    }
    event = _event(payload=original)
    original["z"][0]["price"] = "999"  # type: ignore[index]
    returned = event.payload
    returned["a"] = None

    assert event.payload == {
        "a": {"indicative": False, "size": 100},
        "z": [{"price": "150.01"}],
    }
    assert event.to_json() == (
        '{"event_id":"event-002","event_time":"2026-07-28T09:30:00+00:00",'
        '"event_type":"quote","instrument_id":"XNYS:AAPL",'
        '"payload":{"a":{"indicative":false,"size":100},'
        '"z":[{"price":"150.01"}]},"schema_version":1,'
        '"source":"fixture:primary"}'
    )
    assert market_data_event_from_json(event.to_json()) == event
    assert market_data_event_from_dict(event.to_dict()) == event


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        "not-an-object",
        {"price": float("nan")},
        {"price": float("inf")},
        {"items": ("not", "json")},
        {1: "non-string-key"},
        {"unsupported": object()},
        {"invalid_unicode": "\ud800"},
    ],
)
def test_invalid_payloads_are_rejected(payload: object) -> None:
    with pytest.raises(ValueError, match="payload"):
        _event(payload=payload)


def test_serialized_contract_rejects_invalid_shape_timestamp_and_json() -> None:
    payload = _event().to_dict()
    payload["unknown"] = "field"
    with pytest.raises(ValueError, match="unknown fields"):
        market_data_event_from_dict(payload)
    with pytest.raises(ValueError, match="field names"):
        market_data_event_from_dict({1: "not-a-field-name"})

    noncanonical_time = _event().to_dict()
    noncanonical_time["event_time"] = "2026-07-28T17:30:00+08:00"
    with pytest.raises(ValueError, match="canonical UTC"):
        market_data_event_from_dict(noncanonical_time)

    duplicate_key = _event().to_json().replace(
        '{"event_id":',
        '{"event_id":"duplicate","event_id":',
        1,
    )
    with pytest.raises(ValueError, match="valid strict JSON"):
        market_data_event_from_json(duplicate_key)
    with pytest.raises(ValueError, match="valid strict JSON"):
        market_data_event_from_json('{"payload":{"price":NaN}}')


def test_schema_v1_round_trip_is_supported_and_unknown_versions_fail_closed() -> None:
    serialized = _event().to_dict()

    assert market_data_event_from_dict(serialized).schema_version == 1
    serialized["schema_version"] = 2
    with pytest.raises(ValueError, match="unsupported"):
        market_data_event_from_dict(serialized)


def test_deterministic_order_uses_utc_event_time_then_event_id() -> None:
    first = _event(
        event_id="event-001",
        event_time=datetime(2026, 7, 28, 9, 30, tzinfo=timezone.utc),
        instrument_id="XNAS:MSFT",
    )
    same_time_later_id = _event(
        event_id="event-003",
        event_time=datetime(2026, 7, 28, 9, 30, tzinfo=timezone.utc),
        instrument_id="XNYS:AAPL",
    )
    later = _event(
        event_id="event-000",
        event_time=datetime(2026, 7, 28, 9, 31, tzinfo=timezone.utc),
    )

    assert sort_and_validate_market_data_events(
        [later, same_time_later_id, first]
    ) == (first, same_time_later_id, later)
    with pytest.raises(ValueError, match="identities"):
        sort_and_validate_market_data_events([first, first])
    with pytest.raises(ValueError, match="MarketDataEvent"):
        sort_and_validate_market_data_events([first, object()])  # type: ignore[list-item]
