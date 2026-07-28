"""Domain coverage for trading-calendar and session authority."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from el_psy_quant.market_time import (
    TradingCalendar,
    TradingSession,
    create_trading_calendar,
    create_trading_session,
    sort_and_validate_trading_sessions,
    validate_trading_session_for_calendar,
)


def _calendar() -> TradingCalendar:
    return create_trading_calendar(
        id="xnys-2026-v1",
        market="xnys",
        timezone="America/New_York",
        calendar_version=1,
        created_at=datetime(
            2026,
            7,
            27,
            17,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )


def _session(
    *,
    identity: str = "xnys-2026-07-27-regular",
    hour_open: int = 9,
    minute_open: int = 30,
    hour_close: int = 16,
    minute_close: int = 0,
    session_type: str = "regular",
) -> TradingSession:
    market_timezone = ZoneInfo("America/New_York")
    return create_trading_session(
        id=identity,
        calendar_id="xnys-2026-v1",
        trading_date=date(2026, 7, 27),
        open_time=datetime(
            2026,
            7,
            27,
            hour_open,
            minute_open,
            tzinfo=market_timezone,
        ),
        close_time=datetime(
            2026,
            7,
            27,
            hour_close,
            minute_close,
            tzinfo=market_timezone,
        ),
        session_type=session_type,
    )


def test_calendar_and_session_are_normalized_immutable_definitions() -> None:
    calendar = _calendar()
    session = _session(session_type="REGULAR")

    assert calendar.market == "XNYS"
    assert calendar.created_at == datetime(2026, 7, 27, 9, tzinfo=timezone.utc)
    assert calendar.to_dict() == {
        "schema_version": 1,
        "id": "xnys-2026-v1",
        "market": "XNYS",
        "timezone": "America/New_York",
        "calendar_version": 1,
        "created_at": "2026-07-27T09:00:00+00:00",
    }
    assert session.open_time == datetime(
        2026,
        7,
        27,
        13,
        30,
        tzinfo=timezone.utc,
    )
    assert session.close_time == datetime(
        2026,
        7,
        27,
        20,
        tzinfo=timezone.utc,
    )
    assert session.session_type == "regular"
    assert session.to_dict()["trading_date"] == "2026-07-27"
    with pytest.raises(FrozenInstanceError):
        calendar.market = "XNAS"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        session.session_type = "post_market"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", " ", "id"),
        ("market", "NYSE ARCA", "market"),
        ("timezone", "Not/A_Timezone", "timezone"),
        ("calendar_version", 0, "calendar_version"),
        ("calendar_version", True, "calendar_version"),
        ("created_at", datetime(2026, 7, 27), "created_at"),
    ],
)
def test_calendar_rejects_invalid_authority_fields(
    field: str,
    value: object,
    message: str,
) -> None:
    values: dict[str, object] = {
        "id": "calendar-1",
        "market": "XNYS",
        "timezone": "America/New_York",
        "calendar_version": 1,
        "created_at": datetime(2026, 7, 27, tzinfo=timezone.utc),
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        create_trading_calendar(**values)  # type: ignore[arg-type]


def test_session_rejects_invalid_boundaries_types_and_dates() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        create_trading_session(
            id="session-1",
            calendar_id="calendar-1",
            trading_date=date(2026, 7, 27),
            open_time=datetime(2026, 7, 27, 9),
            close_time=datetime(2026, 7, 27, 10, tzinfo=timezone.utc),
            session_type="regular",
        )
    with pytest.raises(ValueError, match="earlier"):
        create_trading_session(
            id="session-1",
            calendar_id="calendar-1",
            trading_date=date(2026, 7, 27),
            open_time=datetime(2026, 7, 27, 10, tzinfo=timezone.utc),
            close_time=datetime(2026, 7, 27, 10, tzinfo=timezone.utc),
            session_type="regular",
        )
    with pytest.raises(ValueError, match="trading_date"):
        create_trading_session(
            id="session-1",
            calendar_id="calendar-1",
            trading_date=datetime(2026, 7, 27),  # type: ignore[arg-type]
            open_time=datetime(2026, 7, 27, 9, tzinfo=timezone.utc),
            close_time=datetime(2026, 7, 27, 10, tzinfo=timezone.utc),
            session_type="regular",
        )
    with pytest.raises(ValueError, match="session_type"):
        _session(session_type="closing auction")


def test_calendar_validation_uses_the_market_local_trading_date() -> None:
    calendar = _calendar()
    valid = _session()

    assert (
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=valid,
        )
        is valid
    )
    mismatched = create_trading_session(
        id="wrong-date",
        calendar_id=calendar.id,
        trading_date=date(2026, 7, 28),
        open_time=valid.open_time,
        close_time=valid.close_time,
        session_type="regular",
    )
    with pytest.raises(ValueError, match="trading_date"):
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=mismatched,
        )
    wrong_calendar = create_trading_session(
        id="wrong-calendar",
        calendar_id="other-calendar",
        trading_date=valid.trading_date,
        open_time=valid.open_time,
        close_time=valid.close_time,
        session_type="regular",
    )
    with pytest.raises(ValueError, match="exact calendar"):
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=wrong_calendar,
        )


def test_batch_validation_is_deterministic_and_rejects_overlaps() -> None:
    calendar = _calendar()
    pre_market = _session(
        identity="pre-market",
        hour_open=8,
        minute_open=0,
        hour_close=9,
        minute_close=30,
        session_type="pre_market",
    )
    regular = _session()
    post_market = _session(
        identity="post-market",
        hour_open=16,
        minute_open=0,
        hour_close=17,
        minute_close=0,
        session_type="post_market",
    )

    assert sort_and_validate_trading_sessions(
        calendar=calendar,
        sessions=[post_market, regular, pre_market],
    ) == (pre_market, regular, post_market)

    overlapping = _session(
        identity="overlap",
        hour_open=15,
        minute_open=59,
        hour_close=17,
        minute_close=0,
        session_type="post_market",
    )
    with pytest.raises(ValueError, match="overlap"):
        sort_and_validate_trading_sessions(
            calendar=calendar,
            sessions=[regular, overlapping],
        )
    with pytest.raises(ValueError, match="identities"):
        sort_and_validate_trading_sessions(
            calendar=calendar,
            sessions=[regular, regular],
        )
