"""Focused deterministic coverage for the Sprint 199 signal evaluator."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import cast
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    TradingCalendar,
    TradingSession,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.strategies import MovingAverageCrossoverStrategy
from el_psy_quant.strategy_order import (
    EvaluateStrategySignalCommand,
    MovingAverageCrossoverSignalAdapter,
    StrategyRuntimeReference,
    StrategySignalRuntimeAdapter,
    create_evaluate_strategy_signal_command,
    create_moving_average_crossover_runtime_reference,
    create_strategy_signal_market_reference,
    evaluate_strategy_signal,
    resolve_strategy_signal_runtime_adapter,
)
from el_psy_quant.strategy_order import adapters as adapter_module

UTC = timezone.utc
INSTRUMENT = "XNYS:AAPL"
OTHER_INSTRUMENT = "XNYS:MSFT"
AUDIT_TIME = datetime(2026, 7, 30, 8, tzinfo=UTC)


def _calendar(*, version: int = 1) -> TradingCalendar:
    return create_trading_calendar(
        id="xnys-2026",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=version,
        created_at=datetime(2026, 7, 29, 8, tzinfo=UTC),
    )


def _session(*, identity: str = "xnys-2026-07-28-regular") -> TradingSession:
    local = ZoneInfo("America/New_York")
    return create_trading_session(
        id=identity,
        calendar_id="xnys-2026",
        trading_date=date(2026, 7, 28),
        open_time=datetime(2026, 7, 28, 9, 30, tzinfo=local),
        close_time=datetime(2026, 7, 28, 16, tzinfo=local),
        session_type="regular",
    )


def _runtime(
    *,
    fast_window: int = 2,
    slow_window: int = 3,
    quantity: str = "12.5",
) -> StrategyRuntimeReference:
    return create_moving_average_crossover_runtime_reference(
        fast_window=fast_window,
        slow_window=slow_window,
        target_position_quantity=PaperQuantity.parse(quantity),
    )


def _event(
    identity: str,
    minute: int,
    *,
    instrument_id: str = INSTRUMENT,
    event_type: str = "trade",
    payload: object,
    day: int = 28,
) -> MarketDataEvent:
    return create_market_data_event(
        event_id=identity,
        instrument_id=instrument_id,
        event_time=datetime(2026, 7, day, 14, minute, tzinfo=UTC),
        event_type=event_type,
        payload=payload,
        source="fixture:s199",
    )


def _trade_events(
    prices: list[object],
    *,
    identity_prefix: str = "trade",
) -> list[MarketDataEvent]:
    return [
        _event(
            f"{identity_prefix}-{index:03d}",
            index,
            payload={"price": price},
        )
        for index, price in enumerate(prices)
    ]


def _engine(
    prefix: list[MarketDataEvent],
    *,
    future: list[MarketDataEvent] | None = None,
    replay_id: str = "replay-s199",
) -> MarketDataReplayEngine:
    events = [*prefix, *(future or [])]
    engine = MarketDataReplayEngine(replay_id=replay_id, events=events)
    engine.start()
    for expected in sorted(prefix, key=lambda event: event.ordering_key):
        assert engine.next_event() == expected
    return engine


def _command(
    engine: MarketDataReplayEngine,
    *,
    runtime: StrategyRuntimeReference | None = None,
    calendar: TradingCalendar | None = None,
    session: TradingSession | None = None,
    key: str = "evaluate-s199-001",
    actor: str = "founder",
) -> EvaluateStrategySignalCommand:
    selected_calendar = _calendar() if calendar is None else calendar
    selected_session = _session() if session is None else session
    current = engine.events[engine.cursor.position - 1]
    reference = create_strategy_signal_market_reference(
        calendar=selected_calendar,
        session=selected_session,
        replay_session=engine.session,
        current_event=current,
    )
    return create_evaluate_strategy_signal_command(
        strategy_runtime_reference=_runtime() if runtime is None else runtime,
        market_reference=reference,
        command_idempotency_key=key,
        actor=actor,
    )


def _evaluate(
    engine: MarketDataReplayEngine,
    *,
    command: EvaluateStrategySignalCommand | None = None,
    calendar: TradingCalendar | None = None,
    session: TradingSession | None = None,
    created_at: datetime = AUDIT_TIME,
):
    return evaluate_strategy_signal(
        _command(engine) if command is None else command,
        calendar=_calendar() if calendar is None else calendar,
        session=_session() if session is None else session,
        replay_engine=engine,
        created_at=created_at,
    )


def test_exact_adapter_resolution_and_closed_protocol() -> None:
    runtime = _runtime()
    adapter = resolve_strategy_signal_runtime_adapter(runtime)

    assert type(adapter) is MovingAverageCrossoverSignalAdapter
    assert isinstance(adapter, StrategySignalRuntimeAdapter)
    assert (
        adapter.strategy_name,
        adapter.strategy_version,
        adapter.adapter_version,
    ) == ("moving_average_crossover", "v1", "v1")
    assert adapter == MovingAverageCrossoverSignalAdapter()

    source = inspect.getsource(adapter_module)
    for forbidden in (
        "importlib",
        "entry_points",
        "os.environ",
        "pathlib",
        "sqlalchemy",
        "fastapi",
    ):
        assert forbidden not in source.lower()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("strategy_name", "MovingAverageCrossover"),
        ("strategy_version", "v2"),
        ("adapter_version", "v2"),
        ("reference_digest", "0" * 64),
    ],
)
def test_adapter_resolution_rejects_unsupported_or_tampered_reference(
    field: str,
    value: object,
) -> None:
    runtime = _runtime()
    object.__setattr__(runtime, field, value)

    with pytest.raises(ValueError, match="runtime reference"):
        resolve_strategy_signal_runtime_adapter(runtime)


def test_valid_bullish_and_flat_evaluation_map_exact_targets() -> None:
    bullish_engine = _engine(_trade_events([3, 2, 1, 4]))
    bullish = _evaluate(bullish_engine)
    flat_engine = _engine(_trade_events([1, 1, 1, 1], identity_prefix="flat"))
    flat = _evaluate(flat_engine)

    assert bullish.target_position_quantity == PaperQuantity.parse("12.5")
    assert flat.target_position_quantity == PaperQuantity.parse("0")
    assert bullish.market_reference == _command(bullish_engine).market_reference
    assert bullish.strategy_runtime_reference == _runtime()


def test_evaluation_reconstructs_exact_authority_and_rejects_stale_advance() -> None:
    prefix = _trade_events([3, 2, 1, 4])
    future = [_event("trade-999", 20, payload={"price": 5})]
    engine = _engine(prefix, future=future)
    command = _command(engine)
    before = (engine.events, engine.cursor, engine.session)

    signal = _evaluate(engine, command=command)
    assert signal.market_reference.to_dict() == command.market_reference.to_dict()
    assert (engine.events, engine.cursor, engine.session) == before

    engine.next_event()
    advanced = (engine.events, engine.cursor, engine.session)
    with pytest.raises(ValueError, match="stale or mismatched"):
        _evaluate(engine, command=command)
    assert (engine.events, engine.cursor, engine.session) == advanced


def test_lifecycle_only_pause_resume_preserves_signal_identity() -> None:
    engine = _engine(
        _trade_events([3, 2, 1, 4]),
        future=[_event("future", 30, payload={"price": 1000})],
    )
    command = _command(engine)
    running = _evaluate(engine, command=command)
    engine.pause()
    paused = _evaluate(engine, command=command)
    engine.resume()
    resumed = _evaluate(engine, command=command)

    assert running.signal_id == paused.signal_id == resumed.signal_id
    assert running.signal_digest == paused.signal_digest == resumed.signal_digest


@pytest.mark.parametrize("mismatch", ["calendar", "session"])
def test_calendar_version_and_session_identity_mismatches_fail_closed(
    mismatch: str,
) -> None:
    engine = _engine(_trade_events([3, 2, 1, 4]))
    command = _command(engine)
    calendar = _calendar(version=2) if mismatch == "calendar" else _calendar()
    session = (
        _session(identity="xnys-2026-07-28-other")
        if mismatch == "session"
        else _session()
    )

    with pytest.raises(ValueError, match="stale or mismatched"):
        _evaluate(
            engine,
            command=command,
            calendar=calendar,
            session=session,
        )


def test_replay_identity_stream_cursor_event_and_instrument_are_exact() -> None:
    prefix = _trade_events([3, 2, 1, 4])
    original = _engine(
        prefix,
        future=[_event("future-a", 30, payload={"price": 5})],
    )
    command = _command(original)

    different_replay = _engine(
        prefix,
        future=[_event("future-a", 30, payload={"price": 5})],
        replay_id="replay-other",
    )
    different_stream = _engine(
        prefix,
        future=[_event("future-b", 30, payload={"price": 6})],
    )
    instrument_advance = _engine(
        prefix,
        future=[
            _event(
                "future-other-instrument",
                30,
                instrument_id=OTHER_INSTRUMENT,
                payload={"price": 6},
            )
        ],
    )
    instrument_advance.next_event()

    for engine in (different_replay, different_stream, instrument_advance):
        with pytest.raises(ValueError, match="stale or mismatched"):
            _evaluate(engine, command=command)


def test_unconsumed_future_events_do_not_affect_target_selection() -> None:
    prefix = _trade_events([3, 2, 1, 4])
    low_future = _engine(
        prefix,
        future=[_event("future-low", 30, payload={"price": 0.01})],
    )
    high_future = _engine(
        prefix,
        future=[_event("future-high", 30, payload={"price": 1_000_000})],
    )

    low_signal = _evaluate(low_future)
    high_signal = _evaluate(high_future)

    assert low_signal.target_position_quantity == PaperQuantity.parse("12.5")
    assert high_signal.target_position_quantity == PaperQuantity.parse("12.5")
    assert low_signal.market_reference.event_stream_digest != (
        high_signal.market_reference.event_stream_digest
    )


def test_mixed_instruments_and_event_types_preserve_m32_total_order() -> None:
    same_time = datetime(2026, 7, 28, 14, tzinfo=UTC)

    def event(
        identity: str,
        price: object,
        *,
        instrument: str = INSTRUMENT,
        event_type: str = "trade",
    ) -> MarketDataEvent:
        return create_market_data_event(
            event_id=identity,
            instrument_id=instrument,
            event_time=same_time,
            event_type=event_type,
            payload={"price": price},
            source="fixture:s199-total-order",
        )

    prefix = [
        event("d-current", 4),
        event("b-selected", 2.0),
        event("quote-ignored", "invalid", event_type="quote"),
        event("c-selected", 1),
        event("other-ignored", "invalid", instrument=OTHER_INSTRUMENT),
        event("a-selected", 3),
    ]
    engine = _engine(prefix)

    signal = _evaluate(engine)

    assert signal.target_position_quantity == PaperQuantity.parse("12.5")
    assert engine.cursor.last_event_id == "quote-ignored"
    assert signal.market_reference.instrument_id == INSTRUMENT


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"price": True},
        {"price": "1.25"},
        {"price": None},
        {"price": 0},
        {"price": -1},
        {"nested": {"price": 1.25}},
        {"price": 10**1000},
    ],
)
def test_invalid_selected_trade_price_fails_entire_evaluation(
    payload: object,
) -> None:
    prefix = [
        *_trade_events([3, 2, 1, 4]),
        _event("trade-invalid", 10, payload=payload),
    ]
    engine = _engine(prefix)

    with pytest.raises(ValueError, match="price"):
        _evaluate(engine)


@pytest.mark.parametrize("price", [float("inf"), float("-inf"), float("nan")])
def test_non_finite_market_payloads_are_rejected_by_m32(price: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        _event("non-finite", 1, payload={"price": price})


def test_invalid_ignored_event_prices_do_not_become_observations() -> None:
    prefix = [
        *_trade_events([3, 2, 1, 4]),
        _event(
            "other-invalid",
            4,
            instrument_id=OTHER_INSTRUMENT,
            payload={"price": "invalid"},
        ),
        _event(
            "quote-invalid",
            5,
            event_type="quote",
            payload={"price": False},
        ),
    ]
    engine = _engine(prefix)

    assert _evaluate(engine).target_position_quantity == PaperQuantity.parse(
        "12.5"
    )


def test_history_requires_exactly_slow_window_plus_one_selected_trades() -> None:
    insufficient = _engine(_trade_events([3, 2, 1]))
    exact = _engine(_trade_events([3, 2, 1, 4], identity_prefix="exact"))

    with pytest.raises(ValueError, match=r"slow_window \+ 1"):
        _evaluate(insufficient)
    assert _evaluate(exact).target_position_quantity == PaperQuantity.parse(
        "12.5"
    )


def test_prior_consumed_session_history_contributes_to_current_signal() -> None:
    prior = [
        _event("prior-0", 0, payload={"price": 3}, day=27),
        _event("prior-1", 1, payload={"price": 2}, day=27),
        _event("prior-2", 2, payload={"price": 1}, day=27),
    ]
    current = [_event("current", 0, payload={"price": 4})]
    engine = _engine([*prior, *current])

    signal = _evaluate(engine)

    assert signal.market_reference.signal_event_id == "current"
    assert signal.target_position_quantity == PaperQuantity.parse("12.5")


def test_exact_research_resolver_and_parameter_seam_are_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[pd.DataFrame, dict[str, object]]] = []

    @dataclass
    class RecordingStrategy:
        name: str = "moving_average_crossover"

        def run(
            self,
            prices: pd.DataFrame,
            parameters: dict[str, object],
        ) -> pd.DataFrame:
            calls.append((prices.copy(), dict(parameters)))
            return MovingAverageCrossoverStrategy().run(prices, parameters)

    monkeypatch.setattr(
        adapter_module,
        "resolve_strategy",
        lambda name: RecordingStrategy(),
    )
    engine = _engine(_trade_events([3, 2, 1, 4]))

    signal = _evaluate(engine)

    assert signal.target_position_quantity == PaperQuantity.parse("12.5")
    assert len(calls) == 1
    prices, parameters = calls[0]
    assert list(prices.columns) == ["Close"]
    assert prices.index.tolist() == [
        "trade-000",
        "trade-001",
        "trade-002",
        "trade-003",
    ]
    assert parameters == {"fast_window": 2, "slow_window": 3}


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_identity",
        "wrong_type",
        "wrong_rows",
        "wrong_index",
        "missing_position",
        "nan_position",
        "invalid_position",
        "boolean_position",
    ],
)
def test_research_resolution_and_result_tampering_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    class InvalidStrategy:
        name = (
            "other" if failure == "wrong_identity" else "moving_average_crossover"
        )

        def run(
            self,
            prices: pd.DataFrame,
            parameters: dict[str, object],
        ) -> object:
            if failure == "wrong_type":
                return {"position": [0, 1]}
            result = MovingAverageCrossoverStrategy().run(prices, parameters)
            if failure == "wrong_rows":
                return result.iloc[:-1]
            if failure == "wrong_index":
                result.index = pd.RangeIndex(len(result))
            elif failure == "missing_position":
                result = result.drop(columns=["position"])
            elif failure == "nan_position":
                result.loc[result.index[-1], "position"] = float("nan")
            elif failure == "invalid_position":
                result.loc[result.index[-1], "position"] = -1
            elif failure == "boolean_position":
                result["position"] = result["position"].astype(bool)
            return result

    monkeypatch.setattr(
        adapter_module,
        "resolve_strategy",
        lambda name: cast(object, InvalidStrategy()),
    )
    engine = _engine(_trade_events([3, 2, 1, 4]))

    with pytest.raises(ValueError):
        _evaluate(engine)


def test_signal_identity_is_deterministic_and_excludes_command_audit_facts() -> None:
    engine = _engine(_trade_events([3, 2, 1, 4]))
    first_command = _command(engine, key="key-one", actor="founder")
    second_command = _command(engine, key="key-two", actor="operator")

    first = _evaluate(engine, command=first_command, created_at=AUDIT_TIME)
    repeated = _evaluate(
        engine,
        command=first_command,
        created_at=AUDIT_TIME + timedelta(hours=1),
    )
    different_command = _evaluate(engine, command=second_command)

    assert first_command.command_digest != second_command.command_digest
    assert first.signal_id == repeated.signal_id == different_command.signal_id
    assert first.signal_digest == repeated.signal_digest
    assert first.created_at != repeated.created_at


def test_runtime_target_and_market_prefix_changes_change_signal_identity() -> None:
    engine = _engine(_trade_events([3, 2, 1, 4]))
    baseline = _evaluate(engine)
    changed_runtime = _runtime(quantity="20")
    changed_target = _evaluate(
        engine,
        command=_command(engine, runtime=changed_runtime),
    )
    changed_prefix_engine = _engine(
        _trade_events([3, 2, 1, 5], identity_prefix="changed")
    )
    changed_prefix = _evaluate(changed_prefix_engine)

    assert changed_target.target_position_quantity == PaperQuantity.parse("20")
    assert baseline.signal_id != changed_target.signal_id
    assert baseline.signal_id != changed_prefix.signal_id


def test_invalid_command_engine_and_audit_timestamp_fail_without_mutation() -> None:
    engine = _engine(_trade_events([3, 2, 1, 4]))
    command = _command(engine)
    before = (engine.events, engine.cursor, engine.session)
    object.__setattr__(command, "command_digest", "0" * 64)

    with pytest.raises(ValueError, match="command is invalid"):
        _evaluate(engine, command=command)
    assert (engine.events, engine.cursor, engine.session) == before

    valid_command = _command(engine)
    with pytest.raises(ValueError, match="timezone-aware"):
        _evaluate(
            engine,
            command=valid_command,
            created_at=datetime(2026, 7, 30, 8),
        )
    assert (engine.events, engine.cursor, engine.session) == before


def test_empty_unconsumed_and_wrong_runtime_types_fail_closed() -> None:
    events = _trade_events([3, 2, 1, 4])
    unconsumed = MarketDataReplayEngine(replay_id="unconsumed", events=events)
    consumed = _engine(events)
    command = _command(consumed)

    with pytest.raises(ValueError):
        evaluate_strategy_signal(
            command,
            calendar=_calendar(),
            session=_session(),
            replay_engine=cast(MarketDataReplayEngine, object()),
            created_at=AUDIT_TIME,
        )
    with pytest.raises(ValueError, match="consumed"):
        evaluate_strategy_signal(
            command,
            calendar=_calendar(),
            session=_session(),
            replay_engine=unconsumed,
            created_at=AUDIT_TIME,
        )


def test_strategy_order_package_remains_pure_and_scope_bounded() -> None:
    source = inspect.getsource(adapter_module)
    for forbidden in (
        "paper_account.repository",
        "orderintent",
        "riskdecision",
        "sqlalchemy",
        "alembic",
        "fastapi",
        "requests",
        "broker",
    ):
        assert forbidden not in source.lower()
