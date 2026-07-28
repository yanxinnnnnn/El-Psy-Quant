"""Internal SQLAlchemy models for durable market-time authority."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from el_psy_quant.persistence.base import ProductPersistenceBase


class TradingCalendarRow(ProductPersistenceBase):
    """Internal persisted representation of one calendar version."""

    __tablename__ = "trading_calendars"
    __table_args__ = (
        PrimaryKeyConstraint("calendar_id", name="pk_trading_calendars"),
        UniqueConstraint(
            "market",
            "calendar_version",
            name="uq_trading_calendars_market_version",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_trading_calendars_record_schema_version",
        ),
        CheckConstraint(
            "length(calendar_id) BETWEEN 1 AND 512 "
            "AND calendar_id = trim(calendar_id)",
            name="ck_trading_calendars_identity",
        ),
        CheckConstraint(
            "length(market) BETWEEN 1 AND 64 AND market = trim(market) "
            "AND market = upper(market) "
            "AND market NOT GLOB '*[^A-Z0-9._:-]*' "
            "AND substr(market, 1, 1) GLOB '[A-Z0-9]'",
            name="ck_trading_calendars_market",
        ),
        CheckConstraint(
            "length(timezone) BETWEEN 1 AND 128 AND timezone = trim(timezone)",
            name="ck_trading_calendars_timezone",
        ),
        CheckConstraint(
            "calendar_version >= 1",
            name="ck_trading_calendars_version",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    market: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(128), nullable=False)
    calendar_version: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class TradingSessionRow(ProductPersistenceBase):
    """Internal persisted representation of one immutable trading session."""

    __tablename__ = "trading_sessions"
    __table_args__ = (
        PrimaryKeyConstraint("session_id", name="pk_trading_sessions"),
        ForeignKeyConstraint(
            ("calendar_id",),
            ("trading_calendars.calendar_id",),
            name="fk_trading_sessions_calendar_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "calendar_id",
            "trading_date",
            "open_time",
            "close_time",
            "session_type",
            name="uq_trading_sessions_definition",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_trading_sessions_record_schema_version",
        ),
        CheckConstraint(
            "length(session_id) BETWEEN 1 AND 512 "
            "AND session_id = trim(session_id)",
            name="ck_trading_sessions_identity",
        ),
        CheckConstraint(
            "length(calendar_id) BETWEEN 1 AND 512 "
            "AND calendar_id = trim(calendar_id)",
            name="ck_trading_sessions_calendar_identity",
        ),
        CheckConstraint(
            "open_time < close_time",
            name="ck_trading_sessions_boundaries",
        ),
        CheckConstraint(
            "length(session_type) BETWEEN 1 AND 64 "
            "AND session_type = trim(session_type) "
            "AND session_type = lower(session_type) "
            "AND session_type NOT GLOB '*[^a-z0-9_]*' "
            "AND substr(session_type, 1, 1) GLOB '[a-z]'",
            name="ck_trading_sessions_type",
        ),
        Index(
            "ix_trading_sessions_calendar_date_open",
            "calendar_id",
            "trading_date",
            "open_time",
            "session_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    session_id: Mapped[str] = mapped_column(String(512), nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(512), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date(), nullable=False)
    open_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    close_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    session_type: Mapped[str] = mapped_column(String(64), nullable=False)


class MarketDataEventRow(ProductPersistenceBase):
    """Internal persisted representation of one canonical market-data event."""

    __tablename__ = "market_data_events"
    __table_args__ = (
        PrimaryKeyConstraint("event_id", name="pk_market_data_events"),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_events_record_schema_version",
        ),
        CheckConstraint(
            "event_schema_version = 1",
            name="ck_market_data_events_event_schema_version",
        ),
        CheckConstraint(
            "length(event_id) BETWEEN 1 AND 512 "
            "AND event_id = trim(event_id)",
            name="ck_market_data_events_identity",
        ),
        CheckConstraint(
            "length(instrument_id) BETWEEN 1 AND 512 "
            "AND instrument_id = trim(instrument_id)",
            name="ck_market_data_events_instrument_identity",
        ),
        CheckConstraint(
            "length(event_json) >= 2",
            name="ck_market_data_events_canonical_json",
        ),
        Index(
            "ix_market_data_events_time_id",
            "event_time",
            "event_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    event_schema_version: Mapped[int] = mapped_column(nullable=False)
    event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    event_json: Mapped[str] = mapped_column(Text(), nullable=False)


class MarketDataReplayRow(ProductPersistenceBase):
    """Internal persisted representation of one replay recovery checkpoint."""

    __tablename__ = "market_data_replays"
    __table_args__ = (
        PrimaryKeyConstraint("replay_id", name="pk_market_data_replays"),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_replays_record_schema_version",
        ),
        CheckConstraint(
            "replay_state_schema_version = 1",
            name="ck_market_data_replays_state_schema_version",
        ),
        CheckConstraint(
            "length(replay_id) BETWEEN 1 AND 512 "
            "AND replay_id = trim(replay_id)",
            name="ck_market_data_replays_identity",
        ),
        CheckConstraint(
            "length(event_stream_digest) = 64 "
            "AND event_stream_digest NOT GLOB '*[^0-9a-f]*'",
            name="ck_market_data_replays_stream_digest",
        ),
        CheckConstraint(
            "event_count >= 0 AND position >= 0 AND position <= event_count",
            name="ck_market_data_replays_positions",
        ),
        CheckConstraint(
            "(event_count = 0 AND start_time IS NULL) "
            "OR (event_count > 0 AND start_time IS NOT NULL)",
            name="ck_market_data_replays_start_time",
        ),
        CheckConstraint(
            "(last_event_id IS NULL AND current_event_time IS NULL) "
            "OR (last_event_id IS NOT NULL AND current_event_time IS NOT NULL)",
            name="ck_market_data_replays_cursor_pair",
        ),
        CheckConstraint(
            "(position = 0 AND last_event_id IS NULL) "
            "OR (position > 0 AND last_event_id IS NOT NULL)",
            name="ck_market_data_replays_consumed_event",
        ),
        CheckConstraint(
            "status IN ('ready', 'running', 'paused', 'completed')",
            name="ck_market_data_replays_status",
        ),
        CheckConstraint(
            "status != 'ready' OR position = 0",
            name="ck_market_data_replays_ready_position",
        ),
        CheckConstraint(
            "status != 'completed' OR position = event_count",
            name="ck_market_data_replays_completed_position",
        ),
        Index(
            "ix_market_data_replays_status_id",
            "status",
            "replay_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    replay_state_schema_version: Mapped[int] = mapped_column(nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_stream_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    event_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(Integer(), nullable=False)
    last_event_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    current_event_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)


class MarketDataReplayEventRow(ProductPersistenceBase):
    """Immutable membership and canonical order for one replay event stream."""

    __tablename__ = "market_data_replay_events"
    __table_args__ = (
        PrimaryKeyConstraint(
            "replay_id",
            "event_position",
            name="pk_market_data_replay_events",
        ),
        ForeignKeyConstraint(
            ("replay_id",),
            ("market_data_replays.replay_id",),
            name="fk_market_data_replay_events_replay_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("event_id",),
            ("market_data_events.event_id",),
            name="fk_market_data_replay_events_event_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "replay_id",
            "event_id",
            name="uq_market_data_replay_events_identity",
        ),
        CheckConstraint(
            "record_schema_version = 1",
            name="ck_market_data_replay_events_record_schema_version",
        ),
        CheckConstraint(
            "length(replay_id) BETWEEN 1 AND 512 "
            "AND replay_id = trim(replay_id)",
            name="ck_market_data_replay_events_replay_identity",
        ),
        CheckConstraint(
            "event_position >= 0",
            name="ck_market_data_replay_events_position",
        ),
        CheckConstraint(
            "length(event_id) BETWEEN 1 AND 512 "
            "AND event_id = trim(event_id)",
            name="ck_market_data_replay_events_event_identity",
        ),
        Index(
            "ix_market_data_replay_events_event_id",
            "event_id",
        ),
    )

    record_schema_version: Mapped[int] = mapped_column(nullable=False)
    replay_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_position: Mapped[int] = mapped_column(Integer(), nullable=False)
    event_id: Mapped[str] = mapped_column(String(512), nullable=False)
