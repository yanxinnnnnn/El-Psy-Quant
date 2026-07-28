"""Read-only API coverage for Sprint 193 durable market-time inspection."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from el_psy_quant.api.app import create_app
from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
    create_market_data_replay_record,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


@pytest.fixture
def configured_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )
    session_factory = create_product_session_factory(engine=engine)
    calendar = create_trading_calendar(
        id="xnys-2026-v1",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=1,
        created_at=datetime(2026, 7, 28, 8, tzinfo=timezone.utc),
    )
    regular = create_trading_session(
        id="xnys-2026-07-28-regular",
        calendar_id=calendar.id,
        trading_date=date(2026, 7, 28),
        open_time=datetime(2026, 7, 28, 13, 30, tzinfo=timezone.utc),
        close_time=datetime(2026, 7, 28, 20, 0, tzinfo=timezone.utc),
        session_type="regular",
    )
    events = [
        create_market_data_event(
            event_id="event-002",
            instrument_id="XNYS:AAPL",
            event_time=datetime(2026, 7, 28, 13, 31, tzinfo=timezone.utc),
            event_type="quote",
            payload={"ask": 102.0, "bid": 101.5},
            source="fixture:api",
        ),
        create_market_data_event(
            event_id="event-001",
            instrument_id="xnys:aapl",
            event_time=datetime(2026, 7, 28, 13, 30, tzinfo=timezone.utc),
            event_type="quote",
            payload={"ask": 101.0, "bid": 100.5},
            source="fixture:api",
        ),
    ]
    replay_engine = MarketDataReplayEngine(
        replay_id="replay-api",
        events=events,
    )
    replay_engine.start()
    replay_engine.next_event()
    replay_engine.pause()
    replay = create_market_data_replay_record(
        session=replay_engine.session,
        events=replay_engine.events,
    )
    empty_engine = MarketDataReplayEngine(
        replay_id="replay-empty",
        events=[],
    )
    empty = create_market_data_replay_record(
        session=empty_engine.session,
        events=empty_engine.events,
    )
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=regular)
        repository.add_replay(replay=replay)
        repository.add_replay(replay=empty)
    engine.dispose()
    return create_app(product_database_path=path)


def test_calendar_list_and_detail_are_deterministic_and_read_only(
    configured_app,
) -> None:
    client = TestClient(configured_app)

    calendars = client.get(
        "/api/v1/market-time/calendars",
        params={"market": "xnys"},
    )
    detail = client.get(
        "/api/v1/market-time/calendars/xnys-2026-v1",
        params={
            "start_date": "2026-07-28",
            "end_date": "2026-07-28",
            "session_type": "REGULAR",
        },
    )

    assert calendars.status_code == 200
    assert calendars.json() == [
        {
            "schema_version": 1,
            "id": "xnys-2026-v1",
            "market": "XNYS",
            "timezone": "America/New_York",
            "calendar_version": 1,
            "created_at": "2026-07-28T08:00:00+00:00",
        }
    ]
    assert detail.status_code == 200
    assert detail.json() == {
        "calendar": calendars.json()[0],
        "sessions": [
            {
                "schema_version": 1,
                "id": "xnys-2026-07-28-regular",
                "calendar_id": "xnys-2026-v1",
                "trading_date": "2026-07-28",
                "open_time": "2026-07-28T13:30:00+00:00",
                "close_time": "2026-07-28T20:00:00+00:00",
                "session_type": "regular",
            }
        ],
    }


def test_replay_list_status_and_detail_preserve_domain_serialization(
    configured_app,
) -> None:
    client = TestClient(configured_app)

    paused = client.get(
        "/api/v1/market-time/replays",
        params={"status": "paused"},
    )
    detail = client.get("/api/v1/market-time/replays/replay-api")

    assert paused.status_code == 200
    assert len(paused.json()) == 1
    assert paused.json()[0]["replay_id"] == "replay-api"
    assert paused.json()[0]["status"] == "paused"
    assert paused.json()[0]["cursor"]["position"] == 1
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["record_schema_version"] == 1
    assert payload["session"] == paused.json()[0]
    assert payload["event_count"] == 2
    assert [event["event_id"] for event in payload["events"]] == [
        "event-001",
        "event-002",
    ]
    assert payload["events"][0] == {
        "schema_version": 1,
        "event_id": "event-001",
        "instrument_id": "XNYS:AAPL",
        "event_time": "2026-07-28T13:30:00+00:00",
        "event_type": "quote",
        "payload": {"ask": 101.0, "bid": 100.5},
        "source": "fixture:api",
    }


def test_market_time_errors_are_stable_and_database_unavailability_is_closed(
    configured_app,
) -> None:
    client = TestClient(configured_app)
    missing = client.get("/api/v1/market-time/replays/missing")
    invalid = client.get(
        "/api/v1/market-time/calendars",
        params={"market": "not valid"},
    )
    unavailable = TestClient(create_app(product_database_path="")).get(
        "/api/v1/market-time/replays"
    )

    assert missing.status_code == 404
    assert missing.json()["error"] == {
        "code": "market_time_not_found",
        "message": "Market-time state was not found",
    }
    assert invalid.status_code == 422
    assert invalid.json()["error"] == {
        "code": "market_time_invalid",
        "message": "Market-time inspection request is invalid",
    }
    assert unavailable.status_code == 503
    assert unavailable.json()["error"] == {
        "code": "product_database_unavailable",
        "message": "Product database is unavailable",
    }


def test_openapi_exposes_exactly_four_get_only_market_time_operations() -> None:
    document = create_app().openapi()
    paths = document["paths"]
    market_time_paths = {
        path for path in paths if path.startswith("/api/v1/market-time")
    }

    assert market_time_paths == {
        "/api/v1/market-time/calendars",
        "/api/v1/market-time/calendars/{calendar_id}",
        "/api/v1/market-time/replays",
        "/api/v1/market-time/replays/{replay_id}",
    }
    assert all(set(paths[path]) == {"get"} for path in market_time_paths)
    schemas = document["components"]["schemas"]
    assert "TradingCalendarResponse" in schemas
    assert "TradingCalendarDetailResponse" in schemas
    assert "ReplaySessionResponse" in schemas
    assert "MarketDataReplayDetailResponse" in schemas
    assert not any(
        forbidden in path
        for path in market_time_paths
        for forbidden in ("orders", "execution", "accounts", "signals")
    )
