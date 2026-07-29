"""Focused deterministic coverage for the Sprint 198 M33 contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from typing import cast
from zoneinfo import ZoneInfo

import pytest

from el_psy_quant import strategies
from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    ReplaySession,
    TradingCalendar,
    TradingSession,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import PaperQuantity
from el_psy_quant.strategy_order import (
    EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION,
    MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
    MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
    MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
    STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION,
    STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION,
    STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION,
    STRATEGY_SIGNAL_SCHEMA_VERSION,
    TARGET_POSITION_QUANTITY,
    EvaluateStrategySignalCommand,
    StrategyRuntimeReference,
    StrategySignal,
    StrategySignalMarketReference,
    StrategySignalReference,
    create_evaluate_strategy_signal_command,
    create_moving_average_crossover_runtime_reference,
    create_strategy_signal_market_reference,
    create_strategy_signal_reference,
    validate_evaluate_strategy_signal_command,
    validate_strategy_runtime_reference,
    validate_strategy_signal,
    validate_strategy_signal_market_reference,
    validate_strategy_signal_reference,
)
from el_psy_quant.strategy_order.signals import (
    _create_strategy_signal_from_evaluation,
)


def _digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _runtime(
    *,
    fast_window: int = 5,
    slow_window: int = 20,
    quantity: str = "10.25",
) -> StrategyRuntimeReference:
    return create_moving_average_crossover_runtime_reference(
        fast_window=fast_window,
        slow_window=slow_window,
        target_position_quantity=PaperQuantity.parse(quantity),
    )


def _calendar(
    *,
    identity: str = "xnys-2026-v1",
    version: int = 1,
) -> TradingCalendar:
    return create_trading_calendar(
        id=identity,
        market="XNYS",
        timezone="America/New_York",
        calendar_version=version,
        created_at=datetime(2026, 7, 29, 8, tzinfo=timezone.utc),
    )


def _session(
    *,
    calendar_id: str = "xnys-2026-v1",
    identity: str = "xnys-2026-07-28-regular",
) -> TradingSession:
    market_timezone = ZoneInfo("America/New_York")
    return create_trading_session(
        id=identity,
        calendar_id=calendar_id,
        trading_date=date(2026, 7, 28),
        open_time=datetime(
            2026,
            7,
            28,
            9,
            30,
            tzinfo=market_timezone,
        ),
        close_time=datetime(
            2026,
            7,
            28,
            16,
            tzinfo=market_timezone,
        ),
        session_type="regular",
    )


def _event(
    *,
    identity: str = "event-001",
    instrument_id: str = "XNYS:AAPL",
    event_time: datetime | None = None,
    payload: object | None = None,
    source: str = "fixture:s198",
) -> MarketDataEvent:
    if event_time is None:
        event_time = datetime(2026, 7, 28, 14, tzinfo=timezone.utc)
    if payload is None:
        payload = {"opaque": {"price": "123.45"}}
    return create_market_data_event(
        event_id=identity,
        instrument_id=instrument_id,
        event_time=event_time,
        event_type="quote",
        payload=payload,
        source=source,
    )


def _market_authority(
    *,
    calendar: TradingCalendar | None = None,
    session: TradingSession | None = None,
    replay_id: str = "replay-s198",
    current_event: MarketDataEvent | None = None,
) -> tuple[
    TradingCalendar,
    TradingSession,
    ReplaySession,
    MarketDataEvent,
    MarketDataReplayEngine,
]:
    selected_calendar = _calendar() if calendar is None else calendar
    selected_session = (
        _session(calendar_id=selected_calendar.id)
        if session is None
        else session
    )
    selected_event = _event() if current_event is None else current_event
    later_event = _event(
        identity="event-later",
        instrument_id=selected_event.instrument_id,
        event_time=selected_event.event_time + timedelta(minutes=1),
    )
    engine = MarketDataReplayEngine(
        replay_id=replay_id,
        events=[later_event, selected_event],
    )
    engine.start()
    consumed = engine.next_event()
    assert consumed == selected_event
    return (
        selected_calendar,
        selected_session,
        engine.session,
        selected_event,
        engine,
    )


def _market_reference(
    **changes: object,
) -> StrategySignalMarketReference:
    authority = _market_authority(**changes)  # type: ignore[arg-type]
    calendar, session, replay, event, _ = authority
    return create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=replay,
        current_event=event,
    )


def _command(
    *,
    runtime: StrategyRuntimeReference | None = None,
    market: StrategySignalMarketReference | None = None,
    key: str = "signal-command-001",
    actor: str = "founder",
) -> EvaluateStrategySignalCommand:
    return create_evaluate_strategy_signal_command(
        strategy_runtime_reference=_runtime() if runtime is None else runtime,
        market_reference=_market_reference() if market is None else market,
        command_idempotency_key=key,
        actor=actor,
    )


def _signal(
    *,
    command: EvaluateStrategySignalCommand | None = None,
    target: str = "10.25",
    created_at: datetime | None = None,
) -> StrategySignal:
    return _create_strategy_signal_from_evaluation(
        command=_command() if command is None else command,
        target_position_quantity=PaperQuantity.parse(target),
        created_at=(
            datetime(2026, 7, 29, 9, tzinfo=timezone.utc)
            if created_at is None
            else created_at
        ),
    )


def test_runtime_reference_has_exact_canonical_contract_and_digests() -> None:
    reference = _runtime()
    expected_parameters: dict[str, object] = {
        "fast_window": 5,
        "slow_window": 20,
        "target_position_quantity": "10.25",
    }
    expected_without_digest: dict[str, object] = {
        "schema_version": STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION,
        "strategy_name": MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME,
        "strategy_version": MOVING_AVERAGE_CROSSOVER_STRATEGY_VERSION,
        "adapter_version": MOVING_AVERAGE_CROSSOVER_ADAPTER_VERSION,
        "runtime_sizing_semantics": TARGET_POSITION_QUANTITY,
        "parameters": expected_parameters,
        "parameters_digest": _digest(expected_parameters),
    }

    assert reference.parameters_digest == _digest(expected_parameters)
    assert reference.reference_digest == _digest(expected_without_digest)
    assert reference.to_dict() == {
        **expected_without_digest,
        "reference_digest": reference.reference_digest,
    }
    assert validate_strategy_runtime_reference(reference) is reference
    assert hash(reference) == hash(_runtime())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("fast_window", True, "fast_window"),
        ("fast_window", 1.5, "fast_window"),
        ("fast_window", 0, "fast_window"),
        ("fast_window", -1, "fast_window"),
        ("slow_window", False, "slow_window"),
        ("slow_window", 0, "slow_window"),
        ("slow_window", 5, "less than"),
        ("slow_window", 4, "less than"),
    ],
)
def test_runtime_reference_rejects_invalid_window_parameters(
    field: str,
    value: object,
    message: str,
) -> None:
    values: dict[str, object] = {
        "fast_window": 5,
        "slow_window": 20,
        "target_position_quantity": PaperQuantity.parse("10"),
    }
    values[field] = value
    with pytest.raises(ValueError, match=message):
        create_moving_average_crossover_runtime_reference(
            **values  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"schema_version": True}, "schema_version"),
        ({"schema_version": 2}, "schema_version"),
        ({"strategy_name": "moving-average"}, "strategy_name"),
        ({"strategy_version": "v2"}, "strategy_version"),
        ({"adapter_version": "v2"}, "adapter_version"),
        ({"runtime_sizing_semantics": "target_weight"}, "semantics"),
    ],
)
def test_runtime_reference_vocabulary_fails_closed(
    change: dict[str, object],
    message: str,
) -> None:
    values: dict[str, object] = {
        "fast_window": 5,
        "slow_window": 20,
        "target_position_quantity": PaperQuantity.parse("10"),
    }
    values.update(change)
    with pytest.raises(ValueError, match=message):
        create_moving_average_crossover_runtime_reference(
            **values  # type: ignore[arg-type]
        )


def test_runtime_reference_rejects_extra_parameters() -> None:
    with pytest.raises(TypeError, match="unexpected"):
        create_moving_average_crossover_runtime_reference(
            fast_window=5,
            slow_window=20,
            target_position_quantity=PaperQuantity.parse("10"),
            unexpected_parameter="not-approved",  # type: ignore[call-arg]
        )


@pytest.mark.parametrize("quantity", ["0", "-1"])
def test_runtime_reference_requires_positive_exact_paper_quantity(
    quantity: str,
) -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        create_moving_average_crossover_runtime_reference(
            fast_window=5,
            slow_window=20,
            target_position_quantity=PaperQuantity.parse(quantity),
        )
    with pytest.raises(ValueError, match="PaperQuantity"):
        create_moving_average_crossover_runtime_reference(
            fast_window=5,
            slow_window=20,
            target_position_quantity=quantity,  # type: ignore[arg-type]
        )


def test_runtime_reference_is_immutable_isolated_and_digest_sensitive() -> None:
    reference = _runtime()
    exported = reference.parameters
    exported["fast_window"] = 999

    assert reference.parameters["fast_window"] == 5
    assert len(
        {
            reference.reference_digest,
            _runtime(fast_window=6).reference_digest,
            _runtime(slow_window=21).reference_digest,
            _runtime(quantity="10.5").reference_digest,
        }
    ) == 4
    with pytest.raises(FrozenInstanceError):
        reference.strategy_name = "other"  # type: ignore[misc]


def test_runtime_and_command_construction_never_resolve_a_strategy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(name: str) -> object:
        raise AssertionError(f"strategy resolver was called for {name}")

    monkeypatch.setattr(strategies, "resolve_strategy", fail_if_called)
    runtime = _runtime()
    command = _command(runtime=runtime)

    assert runtime.strategy_name == "moving_average_crossover"
    assert command.strategy_runtime_reference == runtime


def test_market_reference_binds_exact_m32_authority_without_mutation() -> None:
    calendar, session, replay, event, engine = _market_authority()
    before_cursor = engine.cursor
    before_session = replay.to_dict()

    reference = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=replay,
        current_event=event,
    )

    assert reference.to_dict() == {
        "schema_version": STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION,
        "calendar_id": calendar.id,
        "calendar_version": calendar.calendar_version,
        "trading_session_id": session.id,
        "replay_id": replay.replay_id,
        "event_stream_digest": replay.cursor.event_stream_digest,
        "cursor_position": 1,
        "last_event_id": event.event_id,
        "signal_event_id": event.event_id,
        "signal_time": event.event_time.isoformat(),
        "instrument_id": event.instrument_id,
        "reference_digest": reference.reference_digest,
    }
    without_digest = reference.to_dict()
    without_digest.pop("reference_digest")
    assert reference.reference_digest == _digest(without_digest)
    assert validate_strategy_signal_market_reference(reference) is reference
    assert engine.cursor == before_cursor
    assert replay.to_dict() == before_session


def test_market_reference_excludes_payload_source_and_replay_status() -> None:
    calendar, session, replay, event, engine = _market_authority()
    running = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=replay,
        current_event=event,
    )
    paused_session = engine.pause()
    paused = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=paused_session,
        current_event=event,
    )
    exported = running.to_dict()

    assert running == paused
    assert running.reference_digest == paused.reference_digest
    assert "payload" not in exported
    assert "source" not in exported
    assert "status" not in exported
    assert "event_type" not in exported


@pytest.mark.parametrize(
    "field",
    [
        "calendar_id",
        "calendar_version",
        "trading_session_id",
        "replay_id",
        "event_stream_digest",
        "cursor_position",
        "last_event_id",
        "signal_event_id",
        "signal_time",
        "instrument_id",
    ],
)
def test_market_reference_digest_covers_every_anchor(field: str) -> None:
    reference = _market_reference()
    payload = reference.to_dict()
    payload.pop("reference_digest")
    changed = copy.deepcopy(payload)
    original = changed[field]
    changed[field] = (
        original + 1 if type(original) is int else f"{original}-changed"
    )

    assert _digest(changed) != reference.reference_digest


def test_market_reference_rejects_wrong_types_and_unconsumed_cursor() -> None:
    calendar, session, replay, event, _ = _market_authority()
    with pytest.raises(ValueError, match="calendar"):
        create_strategy_signal_market_reference(
            calendar=object(),  # type: ignore[arg-type]
            session=session,
            replay_session=replay,
            current_event=event,
        )
    with pytest.raises(ValueError, match="session"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=object(),  # type: ignore[arg-type]
            replay_session=replay,
            current_event=event,
        )
    ready_engine = MarketDataReplayEngine(
        replay_id="ready-replay",
        events=[event],
    )
    with pytest.raises(ValueError, match="consumed"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=session,
            replay_session=ready_engine.session,
            current_event=event,
        )


def test_market_reference_rejects_calendar_event_and_cursor_mismatches() -> None:
    calendar, session, replay, event, _ = _market_authority()
    wrong_session = _session(calendar_id="another-calendar")
    with pytest.raises(ValueError, match="exact calendar"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=wrong_session,
            replay_session=replay,
            current_event=event,
        )
    with pytest.raises(ValueError, match="event ID"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=session,
            replay_session=replay,
            current_event=_event(identity="different-event"),
        )
    with pytest.raises(ValueError, match="event time"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=session,
            replay_session=replay,
            current_event=_event(
                event_time=event.event_time + timedelta(seconds=1)
            ),
        )


def test_market_reference_rejects_event_outside_session_and_tampering() -> None:
    outside = _event(
        event_time=datetime(2026, 7, 28, 21, tzinfo=timezone.utc)
    )
    calendar, session, replay, event, _ = _market_authority(
        current_event=outside
    )
    with pytest.raises(ValueError, match="within"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=session,
            replay_session=replay,
            current_event=event,
        )

    valid = _market_authority()
    calendar, session, replay, event, _ = valid
    tampered = copy.deepcopy(replay)
    object.__setattr__(
        tampered.cursor,
        "event_stream_digest",
        "not-a-digest",
    )
    with pytest.raises(ValueError, match="valid ReplaySession"):
        create_strategy_signal_market_reference(
            calendar=calendar,
            session=session,
            replay_session=tampered,
            current_event=event,
        )


def test_market_reference_preserves_exact_utc_event_and_instrument() -> None:
    local_time = datetime(
        2026,
        7,
        28,
        22,
        tzinfo=timezone(timedelta(hours=8)),
    )
    reference = _market_reference(
        current_event=_event(
            instrument_id="xnys:aapl",
            event_time=local_time,
        )
    )

    assert reference.signal_time == datetime(
        2026,
        7,
        28,
        14,
        tzinfo=timezone.utc,
    )
    assert reference.instrument_id == "XNYS:AAPL"


def test_command_is_exact_canonical_pure_input() -> None:
    command = _command(key="  signal-command-001  ", actor=" founder ")
    without_digest = command.to_dict()
    without_digest.pop("command_digest")

    assert command.schema_version == (
        EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION
    )
    assert command.command_idempotency_key == "signal-command-001"
    assert command.actor == "founder"
    assert command.command_digest == _digest(without_digest)
    assert validate_evaluate_strategy_signal_command(command) is command
    assert set(command.to_dict()) == {
        "schema_version",
        "strategy_runtime_reference",
        "market_reference",
        "command_idempotency_key",
        "actor",
        "command_digest",
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("command_idempotency_key", "", "idempotency"),
        ("command_idempotency_key", " " * 3, "idempotency"),
        ("command_idempotency_key", "x" * 129, "at most"),
        ("actor", "", "actor"),
        ("actor", "x" * 513, "at most"),
        ("schema_version", 2, "schema_version"),
    ],
)
def test_command_validation_fails_closed(
    field: str,
    value: object,
    message: str,
) -> None:
    values: dict[str, object] = {
        "strategy_runtime_reference": _runtime(),
        "market_reference": _market_reference(),
        "command_idempotency_key": "key",
        "actor": "founder",
    }
    values[field] = value
    with pytest.raises(ValueError, match=message):
        create_evaluate_strategy_signal_command(
            **values  # type: ignore[arg-type]
        )


def test_command_digest_is_stable_and_sensitive_to_all_authority() -> None:
    base = _command()
    identical = _command()
    changed_runtime = _command(runtime=_runtime(fast_window=6))
    changed_market = _command(
        market=_market_reference(replay_id="another-replay")
    )
    changed_key = _command(key="another-key")
    changed_actor = _command(actor="another-actor")

    assert base.command_digest == identical.command_digest
    assert len(
        {
            base.command_digest,
            changed_runtime.command_digest,
            changed_market.command_digest,
            changed_key.command_digest,
            changed_actor.command_digest,
        }
    ) == 5


def test_signal_accepts_only_zero_or_configured_target() -> None:
    zero = _signal(target="0")
    configured = _signal(target="10.25")

    assert zero.target_position_quantity == PaperQuantity.parse("0")
    assert configured.target_position_quantity == PaperQuantity.parse("10.25")
    for rejected in ("-1", "1", "10.24", "10.250000000001"):
        with pytest.raises(ValueError, match="non-negative|zero or"):
            _signal(target=rejected)


def test_signal_identity_and_digest_cover_only_deterministic_evidence() -> None:
    command = _command()
    signal = _signal(command=command)
    payload = signal.to_dict()
    payload.pop("signal_id")
    payload.pop("signal_digest")
    payload.pop("created_at")

    assert signal.signal_digest == _digest(payload)
    assert signal.signal_id == f"sig_{signal.signal_digest}"
    assert validate_strategy_signal(signal) is signal
    assert signal.market_reference.signal_time == datetime(
        2026,
        7,
        28,
        14,
        tzinfo=timezone.utc,
    )


def test_signal_identity_ignores_command_audit_fields_and_created_at() -> None:
    first = _signal(
        command=_command(key="key-one", actor="founder"),
        created_at=datetime(2026, 7, 29, 9, tzinfo=timezone.utc),
    )
    second = _signal(
        command=_command(key="key-two", actor="operator"),
        created_at=datetime(
            2026,
            7,
            29,
            18,
            tzinfo=timezone(timedelta(hours=8)),
        ),
    )

    assert first.signal_id == second.signal_id
    assert first.signal_digest == second.signal_digest
    assert first.created_at != second.created_at


def test_signal_identity_changes_with_runtime_market_or_target() -> None:
    base = _signal()
    changed_runtime = _signal(
        command=_command(runtime=_runtime(fast_window=6))
    )
    changed_market = _signal(
        command=_command(
            market=_market_reference(replay_id="different-replay")
        )
    )
    changed_target = _signal(target="0")

    assert len(
        {
            base.signal_digest,
            changed_runtime.signal_digest,
            changed_market.signal_digest,
            changed_target.signal_digest,
        }
    ) == 4


def test_signal_target_semantics_are_closed_and_digest_authoritative() -> None:
    signal = _signal()
    original_payload = signal.to_dict()
    original_payload.pop("signal_id")
    original_payload.pop("signal_digest")
    original_payload.pop("created_at")
    changed_payload = copy.deepcopy(original_payload)
    changed_payload["target_semantics"] = "target_weight"

    assert _digest(changed_payload) != signal.signal_digest
    tampered = copy.deepcopy(signal)
    object.__setattr__(tampered, "target_semantics", "target_weight")
    with pytest.raises(ValueError, match="invalid"):
        validate_strategy_signal(tampered)


def test_signal_created_at_requires_awareness_and_normalizes_to_utc() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _signal(created_at=datetime(2026, 7, 29, 9))
    signal = _signal(
        created_at=datetime(
            2026,
            7,
            29,
            17,
            tzinfo=timezone(timedelta(hours=8)),
        )
    )
    assert signal.created_at == datetime(
        2026,
        7,
        29,
        9,
        tzinfo=timezone.utc,
    )
    assert signal.to_dict()["created_at"] == "2026-07-29T09:00:00+00:00"


def test_signal_and_other_authorities_block_direct_construction() -> None:
    for contract in (
        StrategyRuntimeReference,
        StrategySignalMarketReference,
        EvaluateStrategySignalCommand,
        StrategySignal,
        StrategySignalReference,
    ):
        with pytest.raises(TypeError, match="trusted factory"):
            contract()  # type: ignore[call-arg]


def test_signal_reference_is_compact_and_requires_valid_signal() -> None:
    signal = _signal()
    reference = create_strategy_signal_reference(signal)

    assert reference.schema_version == (
        STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION
    )
    assert reference.to_dict() == {
        "schema_version": STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION,
        "signal_id": signal.signal_id,
        "signal_digest": signal.signal_digest,
    }
    assert validate_strategy_signal_reference(reference) is reference
    with pytest.raises(ValueError, match="StrategySignal"):
        create_strategy_signal_reference(object())  # type: ignore[arg-type]

    tampered = copy.deepcopy(signal)
    object.__setattr__(tampered, "signal_digest", "0" * 64)
    with pytest.raises(ValueError, match="invalid"):
        create_strategy_signal_reference(tampered)


def test_all_exports_are_strict_json_primitives_and_stable() -> None:
    values = [
        _runtime().to_dict(),
        _market_reference().to_dict(),
        _command().to_dict(),
        _signal().to_dict(),
        create_strategy_signal_reference(_signal()).to_dict(),
    ]
    for exported in values:
        first = json.dumps(
            exported,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        second = json.dumps(
            exported,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert first == second
        assert json.loads(first) == exported


def test_caller_mutation_cannot_change_existing_authority() -> None:
    payload = {"nested": {"price": "100"}}
    event = _event(payload=payload)
    calendar, session, replay, _, _ = _market_authority(
        current_event=event
    )
    reference = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=replay,
        current_event=event,
    )
    runtime = _runtime()
    command = _command(runtime=runtime, market=reference)
    runtime_export = runtime.parameters
    command_export = cast(
        dict[str, object],
        command.to_dict()["strategy_runtime_reference"],
    )

    cast(dict[str, object], payload["nested"])["price"] = "999"
    runtime_export["fast_window"] = 999
    command_export["strategy_name"] = "mutated"

    assert event.payload == {"nested": {"price": "100"}}
    assert runtime.parameters["fast_window"] == 5
    assert command.strategy_runtime_reference.strategy_name == (
        MOVING_AVERAGE_CROSSOVER_STRATEGY_NAME
    )
    assert validate_evaluate_strategy_signal_command(command) is command


def test_contracts_contain_no_order_account_risk_or_execution_authority() -> None:
    command_fields = set(_command().to_dict())
    signal_fields = set(_signal().to_dict())
    forbidden = {
        "account_id",
        "account_version",
        "current_position",
        "side",
        "order_quantity",
        "cash",
        "risk_decision",
        "fill",
        "ledger_posting",
        "execution_state",
        "price_history",
    }

    assert command_fields.isdisjoint(forbidden)
    assert signal_fields.isdisjoint(forbidden)
    assert "signal_id" not in command_fields
    assert "target_position_quantity" not in command_fields


def test_schema_constants_remain_exactly_version_one() -> None:
    assert {
        STRATEGY_RUNTIME_REFERENCE_SCHEMA_VERSION,
        STRATEGY_SIGNAL_MARKET_REFERENCE_SCHEMA_VERSION,
        EVALUATE_STRATEGY_SIGNAL_COMMAND_SCHEMA_VERSION,
        STRATEGY_SIGNAL_SCHEMA_VERSION,
        STRATEGY_SIGNAL_REFERENCE_SCHEMA_VERSION,
    } == {1}


def test_new_package_import_has_no_persistence_or_application_dependency() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import el_psy_quant.strategy_order; "
                "assert 'el_psy_quant.persistence' not in sys.modules; "
                "assert 'el_psy_quant.application' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
