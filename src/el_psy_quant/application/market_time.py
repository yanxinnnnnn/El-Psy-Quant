"""Read-only application boundary for durable market-time inspection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayStatus,
    ReplaySession,
    TradingCalendar,
    TradingSession,
)
from el_psy_quant.persistence import SqlAlchemyMarketTimeRepository


class MarketTimeNotFoundError(Exception):
    """Raised when one requested durable market-time identity is absent."""


@dataclass(frozen=True)
class TradingCalendarDetailView:
    """One durable calendar and its deterministically ordered sessions."""

    calendar: TradingCalendar
    sessions: tuple[TradingSession, ...]


@dataclass(frozen=True)
class MarketDataReplayDetailView:
    """One validated replay checkpoint and its exact canonical event stream."""

    session: ReplaySession
    events: tuple[MarketDataEvent, ...]


def list_trading_calendars(
    *,
    session_factory: sessionmaker[Session],
    market: str | None = None,
) -> tuple[TradingCalendar, ...]:
    """List immutable calendars through the durable repository boundary."""
    with session_factory() as session:
        return SqlAlchemyMarketTimeRepository(session=session).list_calendars(
            market=market
        )


def get_trading_calendar_detail(
    *,
    session_factory: sessionmaker[Session],
    calendar_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    session_type: str | None = None,
) -> TradingCalendarDetailView:
    """Return one calendar and a bounded read-only session inspection."""
    with session_factory() as session:
        repository = SqlAlchemyMarketTimeRepository(session=session)
        calendar = repository.get_calendar(calendar_id=calendar_id)
        if calendar is None:
            raise MarketTimeNotFoundError()
        sessions = repository.list_sessions(
            calendar_id=calendar.id,
            start_date=start_date,
            end_date=end_date,
            session_type=session_type,
        )
        return TradingCalendarDetailView(
            calendar=calendar,
            sessions=sessions,
        )


def list_market_data_replays(
    *,
    session_factory: sessionmaker[Session],
    status: MarketDataReplayStatus | None = None,
) -> tuple[ReplaySession, ...]:
    """List replay lifecycle checkpoints without advancing any replay."""
    with session_factory() as session:
        return SqlAlchemyMarketTimeRepository(
            session=session
        ).list_replay_sessions(status=status)


def get_market_data_replay_detail(
    *,
    session_factory: sessionmaker[Session],
    replay_id: str,
) -> MarketDataReplayDetailView:
    """Restore one exact replay for read-only inspection."""
    with session_factory() as session:
        replay = SqlAlchemyMarketTimeRepository(
            session=session
        ).get_replay(replay_id=replay_id)
        if replay is None:
            raise MarketTimeNotFoundError()
        return MarketDataReplayDetailView(
            session=replay.session,
            events=replay.events,
        )


__all__ = [
    "MarketDataReplayDetailView",
    "MarketTimeNotFoundError",
    "TradingCalendarDetailView",
    "get_market_data_replay_detail",
    "get_trading_calendar_detail",
    "list_market_data_replays",
    "list_trading_calendars",
]
