"""Focused deterministic coverage for Sprint 200 Order Intent contracts."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from typing import cast
from zoneinfo import ZoneInfo

import pytest

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import (
    ClosePaperAccountCommand,
    FreezePaperAccountCommand,
    PaperAccountCloseEligibility,
    PaperAccountLedgerState,
    PaperAccountIdentity,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    apply_paper_account_lifecycle_command,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
    validate_paper_account_ledger_state,
)
from el_psy_quant.strategy_order import (
    DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
    ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION,
    ORDER_INTENT_NO_ACTION_SCHEMA_VERSION,
    ORDER_INTENT_NO_ACTION_TARGET_SATISFIED,
    ORDER_INTENT_POLICY_VERSION,
    ORDER_INTENT_REFERENCE_SCHEMA_VERSION,
    ORDER_INTENT_SCHEMA_VERSION,
    ORDER_INTENT_SIDE_BUY,
    ORDER_INTENT_SIDE_SELL,
    SUPPORTED_ORDER_INTENT_RISK_STATUSES,
    DeriveOrderIntentCommand,
    OrderIntent,
    OrderIntentAccountReference,
    OrderIntentNoAction,
    OrderIntentReference,
    StrategySignal,
    create_derive_order_intent_command,
    create_evaluate_strategy_signal_command,
    create_moving_average_crossover_runtime_reference,
    create_order_intent_account_reference,
    create_order_intent_reference,
    create_strategy_signal_market_reference,
    derive_order_intent,
    validate_derive_order_intent_command,
    validate_order_intent,
    validate_order_intent_account_reference,
    validate_order_intent_no_action,
    validate_order_intent_reference,
    validate_order_intent_risk_status,
)
from el_psy_quant.strategy_order.signals import (
    _create_strategy_signal_from_evaluation,
)

UTC = timezone.utc
CREATED = datetime(2026, 7, 30, 8, tzinfo=UTC)
INSTRUMENT = "XNYS:AAPL"


def _digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _signal(
    *,
    target: str = "10",
    configured: str | None = None,
    instrument: str = INSTRUMENT,
    replay_id: str = "replay-s200",
    created_at: datetime = CREATED,
) -> StrategySignal:
    configured_target = target if configured is None else configured
    if configured_target == "0":
        configured_target = "10"
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse(configured_target),
    )
    calendar = create_trading_calendar(
        id="xnys-2026",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=1,
        created_at=CREATED,
    )
    local = ZoneInfo("America/New_York")
    session = create_trading_session(
        id="xnys-2026-07-28-regular",
        calendar_id=calendar.id,
        trading_date=date(2026, 7, 28),
        open_time=datetime(2026, 7, 28, 9, 30, tzinfo=local),
        close_time=datetime(2026, 7, 28, 16, tzinfo=local),
        session_type="regular",
    )
    event = create_market_data_event(
        event_id=f"signal-event-{replay_id}",
        instrument_id=instrument,
        event_time=datetime(2026, 7, 28, 14, tzinfo=UTC),
        event_type="trade",
        payload={"price": 100},
        source="fixture:s200",
    )
    engine = MarketDataReplayEngine(replay_id=replay_id, events=[event])
    engine.start()
    assert engine.next_event() == event
    market = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=engine.session,
        current_event=event,
    )
    command = create_evaluate_strategy_signal_command(
        strategy_runtime_reference=runtime,
        market_reference=market,
        command_idempotency_key="evaluate-s200",
        actor="founder",
    )
    return _create_strategy_signal_from_evaluation(
        command=command,
        target_position_quantity=PaperQuantity.parse(target),
        created_at=created_at,
    )


def _identity(*, account_id: str = "account-s200") -> PaperAccountIdentity:
    return PaperAccountIdentity(
        account_id=account_id,
        display_name="Sprint 200 Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )


def _state(
    *,
    quantity: str | None = "4",
    symbol: str = INSTRUMENT,
    initial_cash: str = "1000",
    account_id: str = "account-s200",
) -> tuple[PaperAccountLedgerState, list[object]]:
    command = create_paper_account_command(
        account_identity=_identity(account_id=account_id),
        initial_cash=PaperMoney.parse(initial_cash),
        command_idempotency_key=f"create-{account_id}",
        actor="founder",
    )
    creation = create_paper_account_event_bundle(
        command,
        event_id=f"{account_id}-event-001",
        cash_entry_id=f"{account_id}-cash-001",
        recorded_timestamp_utc=CREATED,
    )
    history: list[object] = [creation]
    state = replay_paper_account_ledger(history)
    if quantity is not None and PaperQuantity.parse(quantity).decimal_value != 0:
        position_command = create_post_paper_position_adjustment_command(
            account_id=account_id,
            expected_account_version=state.head_version,
            command_idempotency_key=f"position-{account_id}",
            actor="founder",
            reason="Replay-derived test position",
            symbol=symbol,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse(quantity),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        )
        position = apply_paper_position_adjustment(
            state,
            position_command,
            event_id=f"{account_id}-event-002",
            position_entry_id=f"{account_id}-position-002",
            recorded_timestamp_utc=CREATED + timedelta(minutes=1),
        )
        history.append(position)
        state = replay_paper_account_ledger(history)
    return state, history


def _advance_cash(
    state: PaperAccountLedgerState,
    history: list[object],
) -> PaperAccountLedgerState:
    version = state.head_version + 1
    bundle = apply_paper_cash_movement(
        state.to_cash_state(),
        PostPaperCashMovementCommand(
            account_id=state.account_identity.account_id,
            expected_account_version=state.head_version,
            command_idempotency_key=f"cash-{version}",
            actor="founder",
            reason="Advance account head without changing position",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        ),
        event_id=f"event-cash-{version}",
        cash_entry_id=f"cash-entry-{version}",
        recorded_timestamp_utc=CREATED + timedelta(minutes=version),
    )
    return replay_paper_account_ledger([*history, bundle])


def _command(
    *,
    signal: StrategySignal | None = None,
    state: PaperAccountLedgerState | None = None,
    key: str = "derive-s200",
    actor: str = "founder",
):
    selected_signal = _signal() if signal is None else signal
    selected_state = _state()[0] if state is None else state
    return create_derive_order_intent_command(
        signal=selected_signal,
        account_state=selected_state,
        command_idempotency_key=key,
        actor=actor,
    )


def _derive(
    *,
    signal: StrategySignal | None = None,
    state: PaperAccountLedgerState | None = None,
    key: str = "derive-s200",
    actor: str = "founder",
    created_at: datetime = CREATED,
):
    selected_signal = _signal() if signal is None else signal
    selected_state = _state()[0] if state is None else state
    command = _command(
        signal=selected_signal,
        state=selected_state,
        key=key,
        actor=actor,
    )
    return derive_order_intent(
        command,
        signal=selected_signal,
        account_state=selected_state,
        created_at=created_at,
    )


def test_public_m31_validator_accepts_exact_state_without_side_effect() -> None:
    state, _ = _state()
    before = state.to_dict()

    assert validate_paper_account_ledger_state(state) is state
    assert state.to_dict() == before
    with pytest.raises(ValueError, match="PaperAccountLedgerState"):
        validate_paper_account_ledger_state(object())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lifecycle_status", "unknown"),
        ("cash_balance", PaperMoney.parse("999")),
        ("available_cash", PaperMoney.parse("999")),
        ("positions", []),
        ("head_version", 0),
        ("head_event_id", " changed "),
        ("head_chain_digest", "not-a-digest"),
    ],
)
def test_public_m31_validator_fails_closed_on_tampered_state(
    field: str,
    value: object,
) -> None:
    state, _ = _state()
    object.__setattr__(state, field, value)
    with pytest.raises(ValueError):
        validate_paper_account_ledger_state(state)


def test_account_reference_preserves_exact_m31_and_signal_evidence() -> None:
    signal = _signal()
    state, _ = _state(quantity="4")
    reference = create_order_intent_account_reference(
        signal=signal,
        account_state=state,
    )
    payload = reference.to_dict()
    payload.pop("reference_digest")

    assert reference.to_dict() == {
        "schema_version": ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION,
        "account_id": state.account_identity.account_id,
        "base_currency": "USD",
        "lifecycle_status": "active",
        "account_head_version": state.head_version,
        "account_head_event_id": state.head_event_id,
        "account_head_chain_digest": state.head_chain_digest,
        "cash_balance": "1000",
        "available_cash": "1000",
        "instrument_id": INSTRUMENT,
        "current_instrument_quantity": "4",
        "reference_digest": reference.reference_digest,
    }
    assert reference.reference_digest == _digest(payload)
    assert validate_order_intent_account_reference(reference) is reference


def test_account_reference_missing_exact_instrument_is_zero_without_aliases() -> None:
    signal = _signal(instrument=INSTRUMENT)
    state, _ = _state(quantity="4", symbol="AAPL")
    reference = create_order_intent_account_reference(
        signal=signal,
        account_state=state,
    )

    assert reference.current_instrument_quantity == PaperQuantity.parse("0")
    assert reference.instrument_id == INSTRUMENT


def test_account_reference_rejects_frozen_and_closed_replay_states() -> None:
    signal = _signal()
    active, history = _state(quantity=None)
    frozen_bundle = apply_paper_account_lifecycle_command(
        active.to_cash_state(),
        FreezePaperAccountCommand(
            account_id=active.account_identity.account_id,
            expected_account_version=active.head_version,
            command_idempotency_key="freeze",
            actor="founder",
            reason="Freeze fixture",
        ),
        event_id="event-freeze",
        recorded_timestamp_utc=CREATED + timedelta(minutes=2),
    )
    frozen = replay_paper_account_ledger([*history, frozen_bundle])

    zero, zero_history = _state(quantity=None, initial_cash="0")
    closed_bundle = apply_paper_account_lifecycle_command(
        zero.to_cash_state(),
        ClosePaperAccountCommand(
            account_id=zero.account_identity.account_id,
            expected_account_version=zero.head_version,
            command_idempotency_key="close",
            actor="founder",
            reason="Close fixture",
        ),
        event_id="event-close",
        recorded_timestamp_utc=CREATED + timedelta(minutes=2),
        close_eligibility=PaperAccountCloseEligibility(
            cash_is_zero=True,
            position_quantities_are_zero=True,
            aggregate_cost_bases_are_zero=True,
        ),
    )
    closed = replay_paper_account_ledger([*zero_history, closed_bundle])

    for state in (frozen, closed):
        with pytest.raises(ValueError, match="active"):
            create_order_intent_account_reference(
                signal=signal,
                account_state=state,
            )


def test_command_is_exact_normalized_and_digest_sensitive() -> None:
    signal = _signal()
    state, _ = _state()
    command = _command(
        signal=signal,
        state=state,
        key="  derive-key  ",
        actor=" founder ",
    )
    payload = command.to_dict()
    payload.pop("command_digest")

    assert command.schema_version == DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION
    assert command.command_idempotency_key == "derive-key"
    assert command.actor == "founder"
    assert command.command_digest == _digest(payload)
    assert validate_derive_order_intent_command(command) is command
    assert "side" not in command.to_dict()
    assert "requested_quantity" not in command.to_dict()
    assert "target_position_quantity" not in command.to_dict()

    changed_signal = _command(
        signal=_signal(replay_id="different-replay"),
        state=state,
    )
    changed_state = _command(
        signal=signal,
        state=_state(quantity="5")[0],
    )
    changed_key = _command(signal=signal, state=state, key="other")
    changed_actor = _command(signal=signal, state=state, actor="operator")
    assert len(
        {
            command.command_digest,
            changed_signal.command_digest,
            changed_state.command_digest,
            changed_key.command_digest,
            changed_actor.command_digest,
        }
    ) == 5


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("command_idempotency_key", ""),
        ("command_idempotency_key", "x" * 129),
        ("actor", ""),
        ("actor", "x" * 513),
        ("intent_policy_version", "v2"),
        ("schema_version", 2),
    ],
)
def test_command_rejects_invalid_bounds_policy_and_schema(
    field: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "signal": _signal(),
        "account_state": _state()[0],
        "command_idempotency_key": "key",
        "actor": "founder",
    }
    values[field] = value
    with pytest.raises(ValueError):
        create_derive_order_intent_command(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("target", "current", "expected_type", "side", "quantity"),
    [
        ("10", "4", OrderIntent, ORDER_INTENT_SIDE_BUY, "6"),
        ("0", "4", OrderIntent, ORDER_INTENT_SIDE_SELL, "4"),
        ("10", "10", OrderIntentNoAction, None, None),
        ("10", None, OrderIntent, ORDER_INTENT_SIDE_BUY, "10"),
        ("0", None, OrderIntentNoAction, None, None),
    ],
)
def test_exact_buy_sell_and_no_action_conversion(
    target: str,
    current: str | None,
    expected_type: type[object],
    side: str | None,
    quantity: str | None,
) -> None:
    signal = _signal(target=target)
    state, _ = _state(quantity=current)
    result = _derive(signal=signal, state=state)

    assert type(result) is expected_type
    if type(result) is OrderIntent:
        assert result.side == side
        assert result.requested_quantity == PaperQuantity.parse(
            cast(str, quantity)
        )
        assert validate_order_intent(result) is result
    else:
        assert type(result) is OrderIntentNoAction
        assert result.reason_code == ORDER_INTENT_NO_ACTION_TARGET_SATISFIED
        assert "side" not in result.to_dict()
        assert "requested_quantity" not in result.to_dict()
        assert validate_order_intent_no_action(result) is result


def test_exact_maximum_scale_delta_has_no_rounding_or_signed_zero() -> None:
    maximum = "999999999999999999.999999999999"
    current = "999999999999999999.999999999998"
    signal = _signal(target=maximum)
    state, _ = _state(quantity=current)

    intent = _derive(signal=signal, state=state)
    assert type(intent) is OrderIntent
    assert intent.requested_quantity.to_json_value() == "0.000000000001"
    assert isinstance(intent.requested_quantity.decimal_value, type(
        PaperQuantity.parse("1").decimal_value
    ))
    assert "-" not in intent.requested_quantity.to_json_value()


def test_conversion_fails_closed_for_stale_signal_and_every_account_head() -> None:
    signal = _signal()
    state, history = _state()
    command = _command(signal=signal, state=state)
    before_signal = signal.to_dict()
    before_state = state.to_dict()

    changed_signal = _signal(replay_id="changed-replay")
    with pytest.raises(ValueError, match="stale or mismatched"):
        derive_order_intent(
            command,
            signal=changed_signal,
            account_state=state,
            created_at=CREATED,
        )
    advanced = _advance_cash(state, history)
    with pytest.raises(ValueError, match="stale or mismatched"):
        derive_order_intent(
            command,
            signal=signal,
            account_state=advanced,
            created_at=CREATED,
        )
    assert signal.to_dict() == before_signal
    assert state.to_dict() == before_state


def test_intent_identity_excludes_command_and_audit_but_covers_authority() -> None:
    signal = _signal()
    state, history = _state()
    first = _derive(
        signal=signal,
        state=state,
        key="key-one",
        actor="founder",
        created_at=CREATED,
    )
    second = _derive(
        signal=signal,
        state=state,
        key="key-two",
        actor="operator",
        created_at=CREATED + timedelta(hours=1),
    )
    assert type(first) is OrderIntent
    assert type(second) is OrderIntent
    assert first.intent_id == second.intent_id
    assert first.intent_digest == second.intent_digest
    assert first.origin_command_digest != second.origin_command_digest

    advanced = _advance_cash(state, history)
    changed_head = _derive(signal=signal, state=advanced)
    changed_signal = _derive(
        signal=_signal(replay_id="identity-change"),
        state=state,
    )
    assert type(changed_head) is OrderIntent
    assert type(changed_signal) is OrderIntent
    assert len(
        {
            first.intent_digest,
            changed_head.intent_digest,
            changed_signal.intent_digest,
        }
    ) == 3


def test_intent_and_no_action_digests_match_exact_authoritative_payloads() -> None:
    intent = _derive(signal=_signal(target="10"), state=_state(quantity="4")[0])
    no_action = _derive(
        signal=_signal(target="10"),
        state=_state(quantity="10")[0],
    )
    assert type(intent) is OrderIntent
    assert type(no_action) is OrderIntentNoAction

    intent_payload = intent.to_dict()
    for field in (
        "intent_id",
        "intent_digest",
        "origin_command_idempotency_key",
        "origin_command_digest",
        "origin_actor",
        "created_at",
    ):
        intent_payload.pop(field)
    no_action_payload = no_action.to_dict()
    for field in (
        "no_action_id",
        "no_action_digest",
        "origin_command_idempotency_key",
        "origin_command_digest",
        "origin_actor",
        "created_at",
    ):
        no_action_payload.pop(field)

    assert intent.intent_digest == _digest(intent_payload)
    assert intent.intent_id == f"oi_{intent.intent_digest}"
    assert no_action.no_action_digest == _digest(no_action_payload)
    assert no_action.no_action_id == (
        f"no_action_{no_action.no_action_digest}"
    )


def test_no_action_identity_converges_across_commands_and_changes_with_head() -> None:
    signal = _signal(target="10")
    state, history = _state(quantity="10")
    first = _derive(signal=signal, state=state, key="one", actor="founder")
    second = _derive(signal=signal, state=state, key="two", actor="operator")
    advanced = _advance_cash(state, history)
    changed = _derive(signal=signal, state=advanced)

    assert type(first) is OrderIntentNoAction
    assert type(second) is OrderIntentNoAction
    assert type(changed) is OrderIntentNoAction
    assert first.no_action_id == second.no_action_id
    assert first.no_action_digest == second.no_action_digest
    assert first.origin_command_digest != second.origin_command_digest
    assert first.no_action_id != changed.no_action_id


def test_compact_intent_reference_accepts_only_complete_valid_intent() -> None:
    intent = _derive()
    no_action = _derive(
        signal=_signal(target="10"),
        state=_state(quantity="10")[0],
    )
    assert type(intent) is OrderIntent
    assert type(no_action) is OrderIntentNoAction
    reference = create_order_intent_reference(intent)

    assert reference.to_dict() == {
        "schema_version": ORDER_INTENT_REFERENCE_SCHEMA_VERSION,
        "intent_id": intent.intent_id,
        "intent_digest": intent.intent_digest,
    }
    assert validate_order_intent_reference(reference) is reference
    with pytest.raises(ValueError, match="OrderIntent"):
        create_order_intent_reference(no_action)  # type: ignore[arg-type]


def test_direct_construction_immutability_and_strict_json_exports() -> None:
    for contract in (
        OrderIntentAccountReference,
        DeriveOrderIntentCommand,
        OrderIntent,
        OrderIntentNoAction,
        OrderIntentReference,
    ):
        with pytest.raises(TypeError, match="trusted factory"):
            contract()  # type: ignore[call-arg]

    result = _derive()
    with pytest.raises(FrozenInstanceError):
        result.intent_id = "changed"  # type: ignore[misc,union-attr]

    values = [
        create_order_intent_account_reference(
            signal=_signal(),
            account_state=_state()[0],
        ).to_dict(),
        _command().to_dict(),
        result.to_dict(),
        create_order_intent_reference(cast(OrderIntent, result)).to_dict(),
        _derive(
            signal=_signal(target="10"),
            state=_state(quantity="10")[0],
        ).to_dict(),
    ]
    for exported in values:
        encoded = json.dumps(
            exported,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert json.loads(encoded) == exported


def test_tampering_policy_side_quantity_reason_and_identity_fails_closed() -> None:
    intent = _derive()
    assert type(intent) is OrderIntent
    for field, value in (
        ("side", "hold"),
        ("requested_quantity", PaperQuantity.parse("7")),
        ("intent_policy_version", "v2"),
        ("intent_digest", "0" * 64),
    ):
        tampered = copy.deepcopy(intent)
        object.__setattr__(tampered, field, value)
        with pytest.raises(ValueError, match="invalid"):
            validate_order_intent(tampered)

    no_action = _derive(
        signal=_signal(target="10"),
        state=_state(quantity="10")[0],
    )
    assert type(no_action) is OrderIntentNoAction
    object.__setattr__(no_action, "reason_code", "unknown")
    with pytest.raises(ValueError, match="invalid"):
        validate_order_intent_no_action(no_action)


def test_closed_future_risk_status_vocabulary_has_no_mutation_behavior() -> None:
    assert SUPPORTED_ORDER_INTENT_RISK_STATUSES == (
        "proposed",
        "risk_allowed",
        "risk_rejected",
    )
    for status in SUPPORTED_ORDER_INTENT_RISK_STATUSES:
        assert validate_order_intent_risk_status(status) == status
    with pytest.raises(ValueError, match="unsupported"):
        validate_order_intent_risk_status("executed")

    intent = _derive()
    assert "risk_status" not in intent.to_dict()
    assert not hasattr(intent, "set_status")
    assert not hasattr(intent, "execute")


def test_s200_modules_have_no_persistence_api_execution_or_network_dependency() -> None:
    from el_psy_quant.strategy_order import account_references
    from el_psy_quant.strategy_order import intent_commands
    from el_psy_quant.strategy_order import order_intents

    source = "\n".join(
        inspect.getsource(module)
        for module in (account_references, intent_commands, order_intents)
    ).lower()
    for forbidden in (
        "sqlalchemy",
        "alembic",
        "fastapi",
        "requests",
        "httpx",
        "socket",
        "repository",
        "pandas",
        "paperorderrecord",
        "el_psy_quant.execution",
    ):
        assert forbidden not in source


def test_s200_schema_and_policy_constants_remain_exact() -> None:
    assert {
        ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION,
        DERIVE_ORDER_INTENT_COMMAND_SCHEMA_VERSION,
        ORDER_INTENT_SCHEMA_VERSION,
        ORDER_INTENT_REFERENCE_SCHEMA_VERSION,
        ORDER_INTENT_NO_ACTION_SCHEMA_VERSION,
    } == {1}
    assert ORDER_INTENT_POLICY_VERSION == "target_position_quantity_delta_v1"
    assert ORDER_INTENT_SIDE_BUY == "buy"
    assert ORDER_INTENT_SIDE_SELL == "sell"
