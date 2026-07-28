"""Caller-transaction-owned repository for durable market-time authority."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from el_psy_quant.market_time import (
    MARKET_DATA_EVENT_SCHEMA_VERSION,
    MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION,
    MARKET_TIME_RECORD_SCHEMA_VERSION,
    SUPPORTED_MARKET_DATA_REPLAY_STATUSES,
    MarketDataEvent,
    MarketDataReplayStatus,
    ReplayCursor,
    ReplaySession,
    TradingCalendar,
    TradingSession,
    create_trading_calendar,
    create_trading_session,
    market_data_event_from_json,
    sort_and_validate_trading_sessions,
    validate_trading_session_for_calendar,
)
from el_psy_quant.persistence.market_time_model import (
    MarketDataEventRow,
    MarketDataReplayEventRow,
    MarketDataReplayRow,
    TradingCalendarRow,
    TradingSessionRow,
)
from el_psy_quant.persistence.market_time_replays import (
    MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION,
    MarketDataReplayRecord,
    create_market_data_replay_record,
)


class MarketTimeRepository(Protocol):
    """Caller-owned persistence operations for market-time authority."""

    def add_calendar(self, *, calendar: TradingCalendar) -> TradingCalendar: ...

    def add_session(self, *, session: TradingSession) -> TradingSession: ...

    def add_sessions(
        self, *, sessions: tuple[TradingSession, ...] | list[TradingSession]
    ) -> tuple[TradingSession, ...]: ...

    def get_calendar(self, *, calendar_id: str) -> TradingCalendar | None: ...

    def get_calendar_by_market_version(
        self, *, market: str, calendar_version: int
    ) -> TradingCalendar | None: ...

    def list_calendars(
        self, *, market: str | None = None
    ) -> tuple[TradingCalendar, ...]: ...

    def get_session(self, *, session_id: str) -> TradingSession | None: ...

    def list_sessions(
        self,
        *,
        calendar_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        session_type: str | None = None,
    ) -> tuple[TradingSession, ...]: ...

    def sessions_for_date(
        self, *, calendar_id: str, trading_date: date
    ) -> tuple[TradingSession, ...]: ...

    def is_trading_day(self, *, calendar_id: str, trading_date: date) -> bool: ...

    def add_replay(
        self, *, replay: MarketDataReplayRecord
    ) -> MarketDataReplayRecord: ...

    def get_replay(
        self, *, replay_id: str
    ) -> MarketDataReplayRecord | None: ...

    def list_replay_sessions(
        self,
        *,
        status: MarketDataReplayStatus | None = None,
    ) -> tuple[ReplaySession, ...]: ...

    def replace_replay_checkpoint(
        self,
        *,
        expected_cursor: ReplayCursor,
        session: ReplaySession,
    ) -> bool: ...


def _utc_from_sqlite(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _calendar_from_row(row: TradingCalendarRow) -> TradingCalendar:
    if row.record_schema_version != MARKET_TIME_RECORD_SCHEMA_VERSION:
        raise ValueError("persisted trading calendar schema is unsupported")
    return create_trading_calendar(
        id=row.calendar_id,
        market=row.market,
        timezone=row.timezone,
        calendar_version=row.calendar_version,
        created_at=_utc_from_sqlite(row.created_at),
    )


def _session_from_row(row: TradingSessionRow) -> TradingSession:
    if row.record_schema_version != MARKET_TIME_RECORD_SCHEMA_VERSION:
        raise ValueError("persisted trading session schema is unsupported")
    return create_trading_session(
        id=row.session_id,
        calendar_id=row.calendar_id,
        trading_date=row.trading_date,
        open_time=_utc_from_sqlite(row.open_time),
        close_time=_utc_from_sqlite(row.close_time),
        session_type=row.session_type,
    )


def _market_data_event_from_row(row: MarketDataEventRow) -> MarketDataEvent:
    if (
        row.record_schema_version
        != MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
    ):
        raise ValueError("persisted market-data event record is unsupported")
    if row.event_schema_version != MARKET_DATA_EVENT_SCHEMA_VERSION:
        raise ValueError("persisted market-data event schema is unsupported")
    event = market_data_event_from_json(row.event_json)
    if (
        event.schema_version != row.event_schema_version
        or event.event_id != row.event_id
        or event.instrument_id != row.instrument_id
        or event.event_time != _utc_from_sqlite(row.event_time)
        or event.to_json() != row.event_json
    ):
        raise ValueError("persisted market-data event is inconsistent")
    return event


def _replay_session_from_row(row: MarketDataReplayRow) -> ReplaySession:
    if (
        row.record_schema_version
        != MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
    ):
        raise ValueError("persisted replay record schema is unsupported")
    if (
        row.replay_state_schema_version
        != MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION
    ):
        raise ValueError("persisted replay state schema is unsupported")
    cursor = ReplayCursor(
        replay_id=row.replay_id,
        event_stream_digest=row.event_stream_digest,
        position=row.position,
        last_event_id=row.last_event_id,
        current_event_time=(
            None
            if row.current_event_time is None
            else _utc_from_sqlite(row.current_event_time)
        ),
        status=row.status,  # type: ignore[arg-type]
    )
    return ReplaySession(
        replay_id=row.replay_id,
        status=row.status,  # type: ignore[arg-type]
        start_time=(
            None
            if row.start_time is None
            else _utc_from_sqlite(row.start_time)
        ),
        current_time=cursor.current_event_time,
        cursor=cursor,
    )


def _calendar_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("calendar_id must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > 512:
        raise ValueError("calendar_id must be at most 512 characters")
    return normalized


def _session_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("session_id must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > 512:
        raise ValueError("session_id must be at most 512 characters")
    return normalized


def _date(value: object, *, field_name: str) -> date:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")
    return value


def _market_and_version(
    market: object,
    calendar_version: object,
) -> tuple[str, int]:
    probe = create_trading_calendar(
        id="validation-probe",
        market=market,  # type: ignore[arg-type]
        timezone="UTC",
        calendar_version=calendar_version,  # type: ignore[arg-type]
        created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
    )
    return probe.market, probe.calendar_version


def _session_type_filter(value: object) -> str:
    probe = create_trading_session(
        id="validation-probe",
        calendar_id="validation-calendar",
        trading_date=date(1970, 1, 1),
        open_time=datetime(1970, 1, 1, tzinfo=timezone.utc),
        close_time=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        session_type=value,  # type: ignore[arg-type]
    )
    return probe.session_type


def _replay_id(value: object) -> str:
    probe = ReplayCursor(
        replay_id=value,  # type: ignore[arg-type]
        event_stream_digest="0" * 64,
        position=0,
        last_event_id=None,
        current_event_time=None,
        status="ready",
    )
    return probe.replay_id


def _replay_status(value: object) -> MarketDataReplayStatus:
    if (
        not isinstance(value, str)
        or value not in SUPPORTED_MARKET_DATA_REPLAY_STATUSES
    ):
        supported = ", ".join(SUPPORTED_MARKET_DATA_REPLAY_STATUSES)
        raise ValueError(f"status must be one of: {supported}")
    return value  # type: ignore[return-value]


class SqlAlchemyMarketTimeRepository:
    """SQLAlchemy implementation that never commits the caller transaction."""

    def __init__(self, *, session: Session) -> None:
        if not isinstance(session, Session):
            raise TypeError("session must be a SQLAlchemy Session")
        self._session = session

    def add_calendar(self, *, calendar: TradingCalendar) -> TradingCalendar:
        """Add and flush one immutable calendar version."""
        if type(calendar) is not TradingCalendar:
            raise ValueError("calendar must be a TradingCalendar")
        self._session.add(
            TradingCalendarRow(
                record_schema_version=MARKET_TIME_RECORD_SCHEMA_VERSION,
                calendar_id=calendar.id,
                market=calendar.market,
                timezone=calendar.timezone,
                calendar_version=calendar.calendar_version,
                created_at=calendar.created_at,
            )
        )
        self._session.flush()
        return calendar

    def add_session(self, *, session: TradingSession) -> TradingSession:
        """Add and flush one calendar-validated, non-overlapping session."""
        if type(session) is not TradingSession:
            raise ValueError("session must be a TradingSession")
        calendar = self.get_calendar(calendar_id=session.calendar_id)
        if calendar is None:
            raise ValueError("session calendar does not exist")
        validate_trading_session_for_calendar(
            calendar=calendar,
            session=session,
        )
        self._ensure_no_overlap(session)
        self._session.add(
            TradingSessionRow(
                record_schema_version=MARKET_TIME_RECORD_SCHEMA_VERSION,
                session_id=session.id,
                calendar_id=session.calendar_id,
                trading_date=session.trading_date,
                open_time=session.open_time,
                close_time=session.close_time,
                session_type=session.session_type,
            )
        )
        self._session.flush()
        return session

    def add_sessions(
        self,
        *,
        sessions: tuple[TradingSession, ...] | list[TradingSession],
    ) -> tuple[TradingSession, ...]:
        """Add a validated batch in deterministic boundary order."""
        if not isinstance(sessions, (tuple, list)):
            raise ValueError("sessions must be a tuple or list")
        if not sessions:
            return ()
        first = sessions[0]
        if type(first) is not TradingSession:
            raise ValueError("sessions must contain TradingSession values")
        calendar = self.get_calendar(calendar_id=first.calendar_id)
        if calendar is None:
            raise ValueError("session calendar does not exist")
        ordered = sort_and_validate_trading_sessions(
            calendar=calendar,
            sessions=sessions,
        )
        for session in ordered:
            self.add_session(session=session)
        return ordered

    def get_calendar(self, *, calendar_id: str) -> TradingCalendar | None:
        row = self._session.get(
            TradingCalendarRow,
            _calendar_id(calendar_id),
        )
        return None if row is None else _calendar_from_row(row)

    def get_calendar_by_market_version(
        self,
        *,
        market: str,
        calendar_version: int,
    ) -> TradingCalendar | None:
        normalized_market, normalized_version = _market_and_version(
            market,
            calendar_version,
        )
        row = self._session.scalar(
            select(TradingCalendarRow).where(
                TradingCalendarRow.market == normalized_market,
                TradingCalendarRow.calendar_version == normalized_version,
            )
        )
        return None if row is None else _calendar_from_row(row)

    def list_calendars(
        self,
        *,
        market: str | None = None,
    ) -> tuple[TradingCalendar, ...]:
        statement = select(TradingCalendarRow)
        if market is not None:
            normalized_market, _ = _market_and_version(market, 1)
            statement = statement.where(
                TradingCalendarRow.market == normalized_market
            )
        statement = statement.order_by(
            TradingCalendarRow.market,
            TradingCalendarRow.calendar_version,
            TradingCalendarRow.calendar_id,
        )
        return tuple(
            _calendar_from_row(row)
            for row in self._session.scalars(statement).all()
        )

    def get_session(self, *, session_id: str) -> TradingSession | None:
        row = self._session.get(
            TradingSessionRow,
            _session_id(session_id),
        )
        return None if row is None else _session_from_row(row)

    def list_sessions(
        self,
        *,
        calendar_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        session_type: str | None = None,
    ) -> tuple[TradingSession, ...]:
        validated_calendar_id = _calendar_id(calendar_id)
        validated_start = (
            None
            if start_date is None
            else _date(start_date, field_name="start_date")
        )
        validated_end = (
            None if end_date is None else _date(end_date, field_name="end_date")
        )
        if (
            validated_start is not None
            and validated_end is not None
            and validated_start > validated_end
        ):
            raise ValueError("start_date must not be later than end_date")

        statement = select(TradingSessionRow).where(
            TradingSessionRow.calendar_id == validated_calendar_id
        )
        if validated_start is not None:
            statement = statement.where(
                TradingSessionRow.trading_date >= validated_start
            )
        if validated_end is not None:
            statement = statement.where(
                TradingSessionRow.trading_date <= validated_end
            )
        if session_type is not None:
            statement = statement.where(
                TradingSessionRow.session_type
                == _session_type_filter(session_type)
            )
        statement = statement.order_by(
            TradingSessionRow.trading_date,
            TradingSessionRow.open_time,
            TradingSessionRow.close_time,
            TradingSessionRow.session_type,
            TradingSessionRow.session_id,
        )
        return tuple(
            _session_from_row(row)
            for row in self._session.scalars(statement).all()
        )

    def sessions_for_date(
        self,
        *,
        calendar_id: str,
        trading_date: date,
    ) -> tuple[TradingSession, ...]:
        validated_date = _date(trading_date, field_name="trading_date")
        return self.list_sessions(
            calendar_id=calendar_id,
            start_date=validated_date,
            end_date=validated_date,
        )

    def is_trading_day(
        self,
        *,
        calendar_id: str,
        trading_date: date,
    ) -> bool:
        """Return availability strictly from persisted calendar sessions."""
        validated_calendar_id = _calendar_id(calendar_id)
        validated_date = _date(trading_date, field_name="trading_date")
        return (
            self._session.scalar(
                select(TradingSessionRow.session_id)
                .where(
                    TradingSessionRow.calendar_id == validated_calendar_id,
                    TradingSessionRow.trading_date == validated_date,
                )
                .limit(1)
            )
            is not None
        )

    def _ensure_no_overlap(self, session: TradingSession) -> None:
        overlapping = self._session.scalar(
            select(TradingSessionRow.session_id)
            .where(
                TradingSessionRow.calendar_id == session.calendar_id,
                TradingSessionRow.open_time < session.close_time,
                TradingSessionRow.close_time > session.open_time,
            )
            .limit(1)
        )
        if overlapping is not None:
            raise ValueError("trading sessions must not overlap")

    def add_replay(
        self,
        *,
        replay: MarketDataReplayRecord,
    ) -> MarketDataReplayRecord:
        """Persist one exact event stream and its engine-owned checkpoint."""
        if type(replay) is not MarketDataReplayRecord:
            raise ValueError("replay must be a MarketDataReplayRecord")

        for event in replay.events:
            row = self._session.get(MarketDataEventRow, event.event_id)
            if row is None:
                self._session.add(
                    MarketDataEventRow(
                        record_schema_version=(
                            MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
                        ),
                        event_schema_version=event.schema_version,
                        event_id=event.event_id,
                        instrument_id=event.instrument_id,
                        event_time=event.event_time,
                        event_json=event.to_json(),
                    )
                )
            elif _market_data_event_from_row(row) != event:
                raise ValueError(
                    "market-data event identity conflicts with durable authority"
                )
        self._session.flush()

        cursor = replay.session.cursor
        self._session.add(
            MarketDataReplayRow(
                record_schema_version=(
                    MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
                ),
                replay_state_schema_version=(
                    MARKET_DATA_REPLAY_STATE_SCHEMA_VERSION
                ),
                replay_id=replay.session.replay_id,
                event_stream_digest=cursor.event_stream_digest,
                event_count=len(replay.events),
                start_time=replay.session.start_time,
                position=cursor.position,
                last_event_id=cursor.last_event_id,
                current_event_time=cursor.current_event_time,
                status=cursor.status,
            )
        )
        self._session.flush()
        self._session.add_all(
            [
                MarketDataReplayEventRow(
                    record_schema_version=(
                        MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
                    ),
                    replay_id=replay.session.replay_id,
                    event_position=position,
                    event_id=event.event_id,
                )
                for position, event in enumerate(replay.events)
            ]
        )
        self._session.flush()
        return replay

    def get_replay(
        self,
        *,
        replay_id: str,
    ) -> MarketDataReplayRecord | None:
        """Restore one exact event stream and validated engine checkpoint."""
        normalized_replay_id = _replay_id(replay_id)
        replay_row = self._session.get(
            MarketDataReplayRow,
            normalized_replay_id,
        )
        if replay_row is None:
            return None
        joined_rows = self._session.execute(
            select(MarketDataReplayEventRow, MarketDataEventRow)
            .join(
                MarketDataEventRow,
                MarketDataEventRow.event_id
                == MarketDataReplayEventRow.event_id,
            )
            .where(
                MarketDataReplayEventRow.replay_id == normalized_replay_id
            )
            .order_by(MarketDataReplayEventRow.event_position)
        ).all()
        if len(joined_rows) != replay_row.event_count:
            raise ValueError("persisted replay event stream is incomplete")

        events: list[MarketDataEvent] = []
        for expected_position, (mapping, event_row) in enumerate(joined_rows):
            if (
                mapping.record_schema_version
                != MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
                or mapping.event_position != expected_position
            ):
                raise ValueError("persisted replay event order is invalid")
            events.append(_market_data_event_from_row(event_row))
        return create_market_data_replay_record(
            session=_replay_session_from_row(replay_row),
            events=events,
        )

    def list_replay_sessions(
        self,
        *,
        status: MarketDataReplayStatus | None = None,
    ) -> tuple[ReplaySession, ...]:
        """List exact-stream-validated checkpoints in identity order."""
        statement = select(MarketDataReplayRow.replay_id)
        if status is not None:
            statement = statement.where(
                MarketDataReplayRow.status == _replay_status(status)
            )
        statement = statement.order_by(MarketDataReplayRow.replay_id)
        sessions: list[ReplaySession] = []
        for replay_id in self._session.scalars(statement).all():
            replay = self.get_replay(replay_id=replay_id)
            if replay is None:
                raise ValueError("persisted replay disappeared during inspection")
            sessions.append(replay.session)
        return tuple(sessions)

    def replace_replay_checkpoint(
        self,
        *,
        expected_cursor: ReplayCursor,
        session: ReplaySession,
    ) -> bool:
        """Store one validated checkpoint with exact optimistic comparison."""
        if type(expected_cursor) is not ReplayCursor:
            raise ValueError("expected_cursor must be a ReplayCursor")
        if type(session) is not ReplaySession:
            raise ValueError("session must be a ReplaySession")
        if expected_cursor.replay_id != session.replay_id:
            raise ValueError("checkpoint replay identities must match")

        persisted = self.get_replay(replay_id=session.replay_id)
        if persisted is None:
            return False
        create_market_data_replay_record(
            session=session,
            events=persisted.events,
        )
        result = self._session.execute(
            update(MarketDataReplayRow)
            .where(
                MarketDataReplayRow.replay_id == session.replay_id,
                MarketDataReplayRow.event_stream_digest
                == expected_cursor.event_stream_digest,
                MarketDataReplayRow.position == expected_cursor.position,
                MarketDataReplayRow.last_event_id
                == expected_cursor.last_event_id,
                MarketDataReplayRow.current_event_time
                == expected_cursor.current_event_time,
                MarketDataReplayRow.status == expected_cursor.status,
            )
            .values(
                position=session.cursor.position,
                last_event_id=session.cursor.last_event_id,
                current_event_time=session.cursor.current_event_time,
                status=session.cursor.status,
            )
        )
        self._session.flush()
        return result.rowcount == 1


__all__ = [
    "MarketTimeRepository",
    "SqlAlchemyMarketTimeRepository",
]
