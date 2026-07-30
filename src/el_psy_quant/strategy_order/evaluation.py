"""Pure deterministic Strategy Signal evaluation over exact M32 authority."""

from __future__ import annotations

from datetime import datetime

from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    ReplayCursor,
    TradingCalendar,
    TradingSession,
)
from el_psy_quant.strategy_order._canonical import normalize_utc_datetime
from el_psy_quant.strategy_order.adapters import (
    resolve_strategy_signal_runtime_adapter,
)
from el_psy_quant.strategy_order.market_references import (
    create_strategy_signal_market_reference,
)
from el_psy_quant.strategy_order.signal_commands import (
    EvaluateStrategySignalCommand,
    validate_evaluate_strategy_signal_command,
)
from el_psy_quant.strategy_order.signals import (
    StrategySignal,
    _create_strategy_signal_from_evaluation,
)


def _clone_exact_event(value: object) -> MarketDataEvent:
    if type(value) is not MarketDataEvent:
        raise ValueError("replay events must be MarketDataEvent values")
    try:
        rebuilt = MarketDataEvent(
            event_id=value.event_id,
            instrument_id=value.instrument_id,
            event_time=value.event_time,
            event_type=value.event_type,
            payload=value.payload,
            schema_version=value.schema_version,
            source=value.source,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("replay event is invalid") from exc
    if rebuilt != value or rebuilt.to_json() != value.to_json():
        raise ValueError("replay event is invalid")
    return rebuilt


def _validated_engine_snapshot(
    value: object,
) -> MarketDataReplayEngine:
    if type(value) is not MarketDataReplayEngine:
        raise ValueError("replay_engine must be a MarketDataReplayEngine")
    try:
        source_events = value.events
        source_cursor = value.cursor
        source_session = value.session
        events = tuple(_clone_exact_event(event) for event in source_events)
        cursor = ReplayCursor(
            replay_id=source_cursor.replay_id,
            event_stream_digest=source_cursor.event_stream_digest,
            position=source_cursor.position,
            last_event_id=source_cursor.last_event_id,
            current_event_time=source_cursor.current_event_time,
            status=source_cursor.status,
        )
        rebuilt = MarketDataReplayEngine(
            replay_id=source_session.replay_id,
            events=events,
            cursor=cursor,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("replay_engine is invalid") from exc
    if rebuilt.events != source_events:
        raise ValueError("replay_engine events are invalid")
    if rebuilt.cursor != source_cursor:
        raise ValueError("replay_engine cursor is invalid")
    if rebuilt.session != source_session:
        raise ValueError("replay_engine session is invalid")
    return rebuilt


def evaluate_strategy_signal(
    command: EvaluateStrategySignalCommand,
    *,
    calendar: TradingCalendar,
    session: TradingSession,
    replay_engine: MarketDataReplayEngine,
    created_at: datetime,
) -> StrategySignal:
    """Evaluate one immutable Signal without mutating M31 or M32 authority."""
    validate_evaluate_strategy_signal_command(command)
    normalized_created_at = normalize_utc_datetime(
        created_at,
        field_name="created_at",
    )
    rebuilt_engine = _validated_engine_snapshot(replay_engine)
    cursor = rebuilt_engine.cursor
    if cursor.position <= 0:
        raise ValueError("replay_engine must have consumed at least one event")
    current_event = rebuilt_engine.events[cursor.position - 1]
    recreated_market_reference = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=rebuilt_engine.session,
        current_event=current_event,
    )
    if (
        recreated_market_reference != command.market_reference
        or recreated_market_reference.to_dict()
        != command.market_reference.to_dict()
    ):
        raise ValueError("command market reference is stale or mismatched")

    adapter = resolve_strategy_signal_runtime_adapter(
        command.strategy_runtime_reference
    )
    replay_prefix = rebuilt_engine.events[: cursor.position]
    target = adapter.evaluate_target(
        runtime_reference=command.strategy_runtime_reference,
        replay_prefix=replay_prefix,
        market_reference=command.market_reference,
        session=session,
    )
    return _create_strategy_signal_from_evaluation(
        command=command,
        target_position_quantity=target,
        created_at=normalized_created_at,
    )
