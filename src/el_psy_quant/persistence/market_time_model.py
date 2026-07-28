"""Internal SQLAlchemy models for durable market-time authority."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
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
