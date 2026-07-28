"""Versioned read-only durable market-time inspection routes."""

from datetime import date
from http import HTTPStatus
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from el_psy_quant.api.dependencies import (
    get_product_session_factory,
    product_database_unavailable,
)
from el_psy_quant.api.errors import PublicApiError
from el_psy_quant.api.market_time_schemas import (
    MarketDataEventResponse,
    MarketDataReplayDetailResponse,
    ReplaySessionResponse,
    ReplayStatus,
    TradingCalendarDetailResponse,
    TradingCalendarResponse,
    TradingSessionResponse,
)
from el_psy_quant.application import (
    MarketTimeNotFoundError,
    get_market_data_replay_detail,
    get_trading_calendar_detail,
    list_market_data_replays,
    list_trading_calendars,
)
from el_psy_quant.persistence import (
    MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION,
)

router = APIRouter(prefix="/market-time")
SessionFactory = Annotated[
    sessionmaker[Session],
    Depends(get_product_session_factory),
]


def _raise_application_error(exc: Exception) -> NoReturn:
    if isinstance(exc, MarketTimeNotFoundError):
        error = PublicApiError(
            status_code=HTTPStatus.NOT_FOUND,
            code="market_time_not_found",
            message="Market-time state was not found",
        )
    elif isinstance(exc, ValueError):
        error = PublicApiError(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="market_time_invalid",
            message="Market-time inspection request is invalid",
        )
    else:
        raise exc
    raise error from exc


def _calendar_response(value) -> TradingCalendarResponse:
    return TradingCalendarResponse.model_validate(value.to_dict())


def _trading_session_response(value) -> TradingSessionResponse:
    return TradingSessionResponse.model_validate(value.to_dict())


def _replay_session_response(value) -> ReplaySessionResponse:
    return ReplaySessionResponse.model_validate(value.to_dict())


@router.get(
    "/calendars",
    response_model=list[TradingCalendarResponse],
)
def get_trading_calendars(
    session_factory: SessionFactory,
    market: Annotated[str | None, Query()] = None,
) -> list[TradingCalendarResponse]:
    """List immutable calendar versions without inferring availability."""
    try:
        return [
            _calendar_response(calendar)
            for calendar in list_trading_calendars(
                session_factory=session_factory,
                market=market,
            )
        ]
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get(
    "/calendars/{calendar_id}",
    response_model=TradingCalendarDetailResponse,
)
def get_trading_calendar(
    calendar_id: str,
    session_factory: SessionFactory,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    session_type: Annotated[str | None, Query()] = None,
) -> TradingCalendarDetailResponse:
    """Inspect one calendar and a bounded deterministic session list."""
    try:
        detail = get_trading_calendar_detail(
            session_factory=session_factory,
            calendar_id=calendar_id,
            start_date=start_date,
            end_date=end_date,
            session_type=session_type,
        )
        return TradingCalendarDetailResponse(
            calendar=_calendar_response(detail.calendar),
            sessions=[
                _trading_session_response(session)
                for session in detail.sessions
            ],
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get(
    "/replays",
    response_model=list[ReplaySessionResponse],
)
def get_market_data_replays(
    session_factory: SessionFactory,
    status: Annotated[ReplayStatus | None, Query()] = None,
) -> list[ReplaySessionResponse]:
    """List persisted replay status without advancing any cursor."""
    try:
        return [
            _replay_session_response(replay)
            for replay in list_market_data_replays(
                session_factory=session_factory,
                status=status,
            )
        ]
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


@router.get(
    "/replays/{replay_id}",
    response_model=MarketDataReplayDetailResponse,
)
def get_market_data_replay(
    replay_id: str,
    session_factory: SessionFactory,
) -> MarketDataReplayDetailResponse:
    """Inspect one validated checkpoint and exact canonical event stream."""
    try:
        detail = get_market_data_replay_detail(
            session_factory=session_factory,
            replay_id=replay_id,
        )
        return MarketDataReplayDetailResponse(
            record_schema_version=(
                MARKET_TIME_PERSISTENCE_RECORD_SCHEMA_VERSION
            ),
            session=_replay_session_response(detail.session),
            event_count=len(detail.events),
            events=[
                MarketDataEventResponse.model_validate(event.to_dict())
                for event in detail.events
            ],
        )
    except SQLAlchemyError as exc:
        raise product_database_unavailable() from exc
    except Exception as exc:
        _raise_application_error(exc)


__all__ = ["router"]
