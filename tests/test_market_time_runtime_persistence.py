"""Durable replay recovery coverage for Sprint 193 market-time state."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DatabaseError

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
)
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
    create_market_data_replay_record,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.config import PRODUCT_DATABASE_PATH_ENV
from el_psy_quant.persistence.schema import (
    CURRENT_PRODUCT_SCHEMA_REVISION,
    REQUIRED_PRODUCT_INDEXES,
    REQUIRED_PRODUCT_TABLE_COLUMNS,
    REQUIRED_PRODUCT_TRIGGERS,
    read_product_schema_revision,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_REVISION = "0008_market_time_foundation"
REVISION = "0009_market_time_runtime"
NEW_TABLES = {
    "market_data_events",
    "market_data_replay_events",
    "market_data_replays",
}


def _config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def _engine(path: Path):
    return create_product_database_engine(
        config=resolve_product_database_config(database_path=path)
    )


def _current(path: Path) -> str | None:
    engine = _engine(path)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def _events():
    return [
        create_market_data_event(
            event_id="event-002",
            instrument_id="XNYS:AAPL",
            event_time=datetime(2026, 7, 28, 9, 31, tzinfo=timezone.utc),
            event_type="quote",
            payload={"ask": 102.0, "bid": 101.5},
            source="fixture:persistence",
        ),
        create_market_data_event(
            event_id="event-001",
            instrument_id="XNYS:AAPL",
            event_time=datetime(2026, 7, 28, 9, 30, tzinfo=timezone.utc),
            event_type="quote",
            payload={"ask": 101.0, "bid": 100.5},
            source="fixture:persistence",
        ),
    ]


def test_0009_is_additive_linear_and_seeds_no_runtime_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == [CURRENT_PRODUCT_SCHEMA_REVISION]
    assert scripts.get_revision(REVISION).down_revision == PREVIOUS_REVISION

    command.upgrade(_config(), PREVIOUS_REVISION)
    engine = _engine(path)
    try:
        before_tables = set(inspect(engine).get_table_names())
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO trading_calendars "
                    "(record_schema_version, calendar_id, market, timezone, "
                    "calendar_version, created_at) "
                    "VALUES (1, 'preserved-calendar', 'XNYS', "
                    "'America/New_York', 1, '2026-07-28 00:00:00')"
                )
            )
        with engine.connect() as connection:
            before_rows = tuple(
                connection.execute(
                    text(
                        "SELECT * FROM trading_calendars ORDER BY calendar_id"
                    )
                )
            )
            before_m31_sql = tuple(
                connection.execute(
                    text(
                        "SELECT name, sql FROM sqlite_master "
                        "WHERE type = 'table' AND name LIKE 'paper_account%' "
                        "ORDER BY name"
                    )
                )
            )
    finally:
        engine.dispose()

    command.upgrade(_config(), REVISION)
    assert _current(path) == REVISION
    engine = _engine(path)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == before_tables | NEW_TABLES
        for table_name in NEW_TABLES:
            assert tuple(
                item["name"] for item in inspector.get_columns(table_name)
            ) == REQUIRED_PRODUCT_TABLE_COLUMNS[table_name]
            assert {
                item["name"] for item in inspector.get_indexes(table_name)
            } == set(REQUIRED_PRODUCT_INDEXES.get(table_name, ()))
        with engine.connect() as connection:
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in NEW_TABLES
            )
            assert tuple(
                connection.execute(
                    text(
                        "SELECT * FROM trading_calendars ORDER BY calendar_id"
                    )
                )
            ) == before_rows
            assert tuple(
                connection.execute(
                    text(
                        "SELECT name, sql FROM sqlite_master "
                        "WHERE type = 'table' AND name LIKE 'paper_account%' "
                        "ORDER BY name"
                    )
                )
            ) == before_m31_sql
            triggers = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type = 'trigger'"
                    )
                )
            }
        assert {
            name
            for name in REQUIRED_PRODUCT_TRIGGERS
            if name.startswith("trg_market_data_")
        }.issubset(triggers)
        assert read_product_schema_revision(path) == REVISION
    finally:
        engine.dispose()

    command.downgrade(_config(), PREVIOUS_REVISION)
    engine = _engine(path)
    try:
        assert set(inspect(engine).get_table_names()) == before_tables
        with engine.connect() as connection:
            assert tuple(
                connection.execute(
                    text(
                        "SELECT * FROM trading_calendars ORDER BY calendar_id"
                    )
                )
            ) == before_rows
    finally:
        engine.dispose()


def test_repository_restores_exact_stream_and_checkpoint_without_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    original = MarketDataReplayEngine(
        replay_id="replay-persisted",
        events=_events(),
    )
    initial = create_market_data_replay_record(
        session=original.session,
        events=list(reversed(original.events)),
    )
    expected_json = initial.to_json()

    with session_factory.begin() as session:
        SqlAlchemyMarketTimeRepository(session=session).add_replay(
            replay=initial
        )
    engine.dispose()

    reopened = _engine(path)
    reopened_factory = create_product_session_factory(engine=reopened)
    with reopened_factory() as session:
        restored = SqlAlchemyMarketTimeRepository(session=session).get_replay(
            replay_id="replay-persisted"
        )
    assert restored is not None
    assert restored == initial
    assert restored.to_json() == expected_json
    assert [event.event_id for event in restored.events] == [
        "event-001",
        "event-002",
    ]

    progressing = MarketDataReplayEngine(
        replay_id=restored.session.replay_id,
        events=restored.events,
        cursor=restored.session.cursor,
    )
    progressing.start()
    assert progressing.next_event().event_id == "event-001"
    paused = progressing.pause()
    with reopened_factory.begin() as session:
        replaced = SqlAlchemyMarketTimeRepository(
            session=session
        ).replace_replay_checkpoint(
            expected_cursor=restored.session.cursor,
            session=paused,
        )
    assert replaced

    with reopened_factory() as session:
        checkpoint = SqlAlchemyMarketTimeRepository(
            session=session
        ).get_replay(replay_id="replay-persisted")
    assert checkpoint is not None
    resumed = MarketDataReplayEngine(
        replay_id=checkpoint.session.replay_id,
        events=checkpoint.events,
        cursor=checkpoint.session.cursor,
    )
    resumed.resume()
    assert [event.event_id for event in resumed.iter_remaining()] == [
        "event-002"
    ]
    assert resumed.session.status == "completed"
    with reopened_factory.begin() as session:
        assert SqlAlchemyMarketTimeRepository(
            session=session
        ).replace_replay_checkpoint(
            expected_cursor=checkpoint.session.cursor,
            session=resumed.session,
        )
    with reopened_factory() as session:
        completed = SqlAlchemyMarketTimeRepository(
            session=session
        ).get_replay(replay_id="replay-persisted")
    assert completed is not None
    assert completed.session == resumed.session
    reopened.dispose()


def test_repository_rejects_event_identity_conflict_and_stale_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    first_engine = MarketDataReplayEngine(
        replay_id="replay-first",
        events=_events(),
    )
    first = create_market_data_replay_record(
        session=first_engine.session,
        events=first_engine.events,
    )
    with session_factory.begin() as session:
        SqlAlchemyMarketTimeRepository(session=session).add_replay(replay=first)

    changed_event = create_market_data_event(
        event_id="event-001",
        instrument_id="XNYS:AAPL",
        event_time=datetime(2026, 7, 28, 9, 30, tzinfo=timezone.utc),
        event_type="quote",
        payload={"ask": 999.0},
        source="fixture:persistence",
    )
    changed_engine = MarketDataReplayEngine(
        replay_id="replay-conflict",
        events=[changed_event],
    )
    changed = create_market_data_replay_record(
        session=changed_engine.session,
        events=changed_engine.events,
    )
    with session_factory() as session:
        with pytest.raises(ValueError, match="identity conflicts"):
            SqlAlchemyMarketTimeRepository(session=session).add_replay(
                replay=changed
            )
        session.rollback()

    first_engine.start()
    first_engine.next_event()
    paused = first_engine.pause()
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        assert repository.replace_replay_checkpoint(
            expected_cursor=first.session.cursor,
            session=paused,
        )
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        assert not repository.replace_replay_checkpoint(
            expected_cursor=first.session.cursor,
            session=paused,
        )
    engine.dispose()


def test_database_keeps_event_stream_immutable_but_allows_checkpoint_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    replay_engine = MarketDataReplayEngine(
        replay_id="replay-immutable",
        events=_events(),
    )
    replay = create_market_data_replay_record(
        session=replay_engine.session,
        events=replay_engine.events,
    )
    with session_factory.begin() as session:
        SqlAlchemyMarketTimeRepository(session=session).add_replay(replay=replay)

    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="append-only"):
            connection.execute(
                text(
                    "UPDATE market_data_events SET instrument_id = 'XNAS:MSFT' "
                    "WHERE event_id = 'event-001'"
                )
            )
    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="stream authority"):
            connection.execute(
                text(
                    "UPDATE market_data_replays SET event_count = 99 "
                    "WHERE replay_id = 'replay-immutable'"
                )
            )
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE market_data_replays SET status = 'running' "
                "WHERE replay_id = 'replay-immutable'"
            )
        )
    engine.dispose()
