"""Migration and repository coverage for Sprint 190 market-time authority."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.exc import DatabaseError

from el_psy_quant.market_time import (
    TradingCalendar,
    TradingSession,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.persistence import (
    SqlAlchemyMarketTimeRepository,
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
PREVIOUS_REVISION = "0007_paper_account_ledger"
REVISION = "0008_market_time_foundation"
CURRENT_REVISION = "0009_market_time_runtime"
NEW_TABLES = {"trading_calendars", "trading_sessions"}


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


def _calendar(
    *,
    identity: str = "xnys-2026-v1",
    market: str = "XNYS",
    version: int = 1,
) -> TradingCalendar:
    return create_trading_calendar(
        id=identity,
        market=market,
        timezone="America/New_York",
        calendar_version=version,
        created_at=datetime(2026, 7, 27, 9, tzinfo=timezone.utc),
    )


def _session(
    *,
    identity: str,
    hour_open: int,
    minute_open: int,
    hour_close: int,
    minute_close: int,
    session_type: str,
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


def test_migration_is_one_additive_linear_head_without_seed_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    scripts = ScriptDirectory.from_config(_config())
    assert scripts.get_heads() == [CURRENT_REVISION]
    assert scripts.get_revision(CURRENT_REVISION).down_revision == REVISION
    assert scripts.get_revision(REVISION).down_revision == PREVIOUS_REVISION
    assert CURRENT_PRODUCT_SCHEMA_REVISION == CURRENT_REVISION

    command.upgrade(_config(), PREVIOUS_REVISION)
    engine = _engine(path)
    try:
        before_tables = set(inspect(engine).get_table_names())
        with engine.connect() as connection:
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
        assert inspector.get_pk_constraint("trading_calendars") == {
            "name": "pk_trading_calendars",
            "constrained_columns": ["calendar_id"],
        }
        assert inspector.get_pk_constraint("trading_sessions") == {
            "name": "pk_trading_sessions",
            "constrained_columns": ["session_id"],
        }
        foreign_keys = inspector.get_foreign_keys("trading_sessions")
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "trading_calendars"
        assert foreign_keys[0]["options"]["ondelete"] == "RESTRICT"
        assert {
            item["name"] for item in inspector.get_indexes("trading_sessions")
        } == set(REQUIRED_PRODUCT_INDEXES["trading_sessions"])
        with engine.connect() as connection:
            assert all(
                connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')) == 0
                for table in NEW_TABLES
            )
            after_m31_sql = tuple(
                connection.execute(
                    text(
                        "SELECT name, sql FROM sqlite_master "
                        "WHERE type = 'table' AND name LIKE 'paper_account%' "
                        "ORDER BY name"
                    )
                )
            )
            triggers = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type = 'trigger'"
                    )
                )
            }
        assert after_m31_sql == before_m31_sql
        assert {
            name
            for name in REQUIRED_PRODUCT_TRIGGERS
            if name.startswith("trg_trading_")
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
                        "SELECT name, sql FROM sqlite_master "
                        "WHERE type = 'table' AND name LIKE 'paper_account%' "
                        "ORDER BY name"
                    )
                )
            ) == before_m31_sql
    finally:
        engine.dispose()


def test_repository_persists_and_queries_calendar_availability_deterministically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)

    calendar = _calendar()
    version_two = _calendar(identity="xnys-2026-v2", version=2)
    xnas = _calendar(identity="xnas-2026-v1", market="XNAS")
    pre_market = _session(
        identity="pre-market",
        hour_open=8,
        minute_open=0,
        hour_close=9,
        minute_close=30,
        session_type="pre_market",
    )
    regular = _session(
        identity="regular",
        hour_open=9,
        minute_open=30,
        hour_close=16,
        minute_close=0,
        session_type="regular",
    )
    post_market = _session(
        identity="post-market",
        hour_open=16,
        minute_open=0,
        hour_close=17,
        minute_close=0,
        session_type="post_market",
    )
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=version_two)
        repository.add_calendar(calendar=xnas)
        repository.add_calendar(calendar=calendar)
        assert repository.add_sessions(
            sessions=[post_market, regular, pre_market]
        ) == (pre_market, regular, post_market)

    with session_factory() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        assert repository.get_calendar(calendar_id=calendar.id) == calendar
        assert repository.get_calendar_by_market_version(
            market="xnys",
            calendar_version=1,
        ) == calendar
        assert repository.list_calendars() == (
            xnas,
            calendar,
            version_two,
        )
        assert repository.list_calendars(market="XNYS") == (
            calendar,
            version_two,
        )
        assert repository.sessions_for_date(
            calendar_id=calendar.id,
            trading_date=date(2026, 7, 27),
        ) == (pre_market, regular, post_market)
        assert repository.list_sessions(
            calendar_id=calendar.id,
            session_type="REGULAR",
        ) == (regular,)
        assert repository.get_session(session_id=regular.id) == regular
        assert repository.is_trading_day(
            calendar_id=calendar.id,
            trading_date=date(2026, 7, 27),
        )
        assert not repository.is_trading_day(
            calendar_id=calendar.id,
            trading_date=date(2026, 7, 28),
        )

    engine.dispose()
    reopened = _engine(path)
    try:
        with create_product_session_factory(engine=reopened)() as session:
            repository = SqlAlchemyMarketTimeRepository(session=session)
            assert repository.sessions_for_date(
                calendar_id=calendar.id,
                trading_date=date(2026, 7, 27),
            ) == (pre_market, regular, post_market)
    finally:
        reopened.dispose()


def test_repository_rejects_wrong_calendar_overlap_and_invalid_ranges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    calendar = _calendar()
    regular = _session(
        identity="regular",
        hour_open=9,
        minute_open=30,
        hour_close=16,
        minute_close=0,
        session_type="regular",
    )
    overlap = _session(
        identity="overlap",
        hour_open=15,
        minute_open=0,
        hour_close=17,
        minute_close=0,
        session_type="post_market",
    )
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=regular)

    with session_factory() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        with pytest.raises(ValueError, match="overlap"):
            repository.add_session(session=overlap)
        session.rollback()
        with pytest.raises(ValueError, match="later"):
            repository.list_sessions(
                calendar_id=calendar.id,
                start_date=date(2026, 7, 28),
                end_date=date(2026, 7, 27),
            )

    missing_calendar_session = create_trading_session(
        id="missing-calendar",
        calendar_id="missing",
        trading_date=regular.trading_date,
        open_time=regular.open_time,
        close_time=regular.close_time,
        session_type=regular.session_type,
    )
    with session_factory() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        with pytest.raises(ValueError, match="does not exist"):
            repository.add_session(session=missing_calendar_session)
    engine.dispose()


def test_database_constraints_preserve_immutable_market_time_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "product.sqlite3"
    monkeypatch.setenv(PRODUCT_DATABASE_PATH_ENV, str(path))
    command.upgrade(_config(), "head")
    engine = _engine(path)
    session_factory = create_product_session_factory(engine=engine)
    calendar = _calendar()
    regular = _session(
        identity="regular",
        hour_open=9,
        minute_open=30,
        hour_close=16,
        minute_close=0,
        session_type="regular",
    )
    with session_factory.begin() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        repository.add_calendar(calendar=calendar)
        repository.add_session(session=regular)

    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="append-only"):
            connection.execute(
                text(
                    "UPDATE trading_sessions "
                    "SET session_type = 'other' WHERE session_id = 'regular'"
                )
            )
    with engine.begin() as connection:
        with pytest.raises(DatabaseError, match="cannot be deleted"):
            connection.execute(
                text(
                    "DELETE FROM trading_calendars "
                    "WHERE calendar_id = 'xnys-2026-v1'"
                )
            )
    engine.dispose()
