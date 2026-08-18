"""Focused deterministic coverage for Sprint 208 M34 contracts."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from el_psy_quant.market_time import (
    MarketDataReplayEngine,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import (
    PaperAccountIdentity,
    PaperMoney,
    PaperQuantity,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_cash_movement_command,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
)
from el_psy_quant.paper_execution import (
    PAPER_EXECUTION_ORDER_STATUS_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED,
    PAPER_EXECUTION_ORDER_STATUS_REJECTED,
    PAPER_EXECUTION_ORDER_STATUS_WORKING,
    PaperExecutionBasisPoints,
    PaperExecutionOrder,
    create_initial_paper_execution_order_state,
    create_paper_execution_account_handoff_reference,
    create_paper_execution_market_handoff_reference,
    create_paper_execution_order,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_paper_execution_policy_reference,
    create_paper_execution_risk_handoff_reference,
    create_step_paper_execution_order_command,
    validate_create_paper_execution_order_command,
    validate_paper_execution_account_handoff_reference,
    validate_paper_execution_market_handoff_reference,
    validate_paper_execution_order,
    validate_paper_execution_order_reference,
    validate_paper_execution_order_state,
    validate_paper_execution_policy_reference,
    validate_paper_execution_risk_handoff_reference,
    validate_step_paper_execution_order_command,
)
from el_psy_quant.paper_execution.lifecycle import (
    _derive_paper_execution_order_state,
)
from el_psy_quant.strategy_order import (
    create_derive_order_intent_command,
    create_evaluate_pre_trade_risk_command,
    create_evaluate_strategy_signal_command,
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
    create_order_intent_reference,
    create_strategy_signal_market_reference,
    derive_order_intent,
    evaluate_pre_trade_risk,
)
from el_psy_quant.strategy_order.signals import (
    _create_strategy_signal_from_evaluation,
)

UTC = timezone.utc
CREATED = datetime(2026, 8, 14, 8, tzinfo=UTC)
INSTRUMENT = "XNYS:AAPL"


def _policy(**changes: object):
    values: dict[str, object] = {
        "max_fill_quantity_per_trade_event": None,
        "slippage_bps": PaperExecutionBasisPoints.parse("1.25"),
        "commission_bps": PaperExecutionBasisPoints.parse("0.5"),
        "fee_bps": PaperExecutionBasisPoints.parse("0"),
        "buy_tax_bps": PaperExecutionBasisPoints.parse("0"),
        "sell_tax_bps": PaperExecutionBasisPoints.parse("2"),
    }
    values.update(changes)
    return create_paper_execution_policy_reference(**values)  # type: ignore[arg-type]


def _state(*, cash: str = "1000", quantity: str = "4"):
    identity = PaperAccountIdentity(
        account_id="account-s208",
        display_name="Sprint 208 Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )
    command = create_paper_account_command(
        account_identity=identity,
        initial_cash=PaperMoney.parse(cash),
        command_idempotency_key="create-account-s208",
        actor="founder",
    )
    created = create_paper_account_event_bundle(
        command,
        event_id="account-s208-event-1",
        cash_entry_id="account-s208-cash-1",
        recorded_timestamp_utc=CREATED,
    )
    history: list[Any] = [created]
    state = replay_paper_account_ledger(history)
    if PaperQuantity.parse(quantity).decimal_value > 0:
        position_command = create_post_paper_position_adjustment_command(
            account_id=identity.account_id,
            expected_account_version=state.head_version,
            command_idempotency_key="position-account-s208",
            actor="founder",
            reason="Sprint 208 exact opening position",
            symbol=INSTRUMENT,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse(quantity),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        )
        position = apply_paper_position_adjustment(
            state,
            position_command,
            event_id="account-s208-event-2",
            position_entry_id="account-s208-position-2",
            recorded_timestamp_utc=CREATED + timedelta(minutes=1),
        )
        history.append(position)
        state = replay_paper_account_ledger(history)
    return state, history


def _fixture(
    *,
    cash: str = "1000",
    target: str = "10",
    command_key: str = "create-order-s208",
    actor: str = "founder",
    order_created_at: datetime = CREATED + timedelta(hours=4),
):
    calendar = create_trading_calendar(
        id="xnys-2026",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=1,
        created_at=CREATED,
    )
    local = ZoneInfo("America/New_York")
    session = create_trading_session(
        id="xnys-2026-08-14-regular",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 14),
        open_time=datetime(2026, 8, 14, 9, 30, tzinfo=local),
        close_time=datetime(2026, 8, 14, 16, tzinfo=local),
        session_type="regular",
    )
    current_event = create_market_data_event(
        event_id="trade-s208-1",
        instrument_id=INSTRUMENT,
        event_time=datetime(2026, 8, 14, 14, tzinfo=UTC),
        event_type="trade",
        payload={"price": 100},
        source="fixture:s208",
    )
    future_event = create_market_data_event(
        event_id="trade-s208-2",
        instrument_id=INSTRUMENT,
        event_time=current_event.event_time + timedelta(minutes=1),
        event_type="trade",
        payload={"price": 101},
        source="fixture:s208",
    )
    engine = MarketDataReplayEngine(
        replay_id="replay-s208",
        events=[future_event, current_event],
    )
    engine.start()
    assert engine.next_event() == current_event
    market_reference = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=engine.session,
        current_event=current_event,
    )
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse(target),
    )
    signal_command = create_evaluate_strategy_signal_command(
        strategy_runtime_reference=runtime,
        market_reference=market_reference,
        command_idempotency_key="signal-s208",
        actor="founder",
    )
    signal = _create_strategy_signal_from_evaluation(
        command=signal_command,
        target_position_quantity=PaperQuantity.parse(target),
        created_at=CREATED + timedelta(hours=1),
    )
    account_state, history = _state(cash=cash)
    intent_command = create_derive_order_intent_command(
        signal=signal,
        account_state=account_state,
        command_idempotency_key="intent-s208",
        actor="founder",
    )
    intent = derive_order_intent(
        intent_command,
        signal=signal,
        account_state=account_state,
        created_at=CREATED + timedelta(hours=2),
    )
    risk_policy = create_long_only_cash_risk_policy_reference()
    risk_command = create_evaluate_pre_trade_risk_command(
        intent=intent,
        risk_policy_reference=risk_policy,
        command_idempotency_key="risk-s208",
        actor="founder",
    )
    decision = evaluate_pre_trade_risk(
        risk_command,
        intent=intent,
        account_state=account_state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED + timedelta(hours=3),
    )
    policy = _policy()
    result: dict[str, Any] = {
        "calendar": calendar,
        "session": session,
        "engine": engine,
        "signal": signal,
        "state": account_state,
        "history": history,
        "intent": intent,
        "decision": decision,
        "policy": policy,
    }
    if decision.outcome == "allow":
        risk_handoff = create_paper_execution_risk_handoff_reference(
            decision=decision,
            intent=intent,
        )
        command = create_paper_execution_order_command(
            order_intent_reference=create_order_intent_reference(intent),
            risk_handoff_reference=risk_handoff,
            execution_policy_reference=policy,
            command_idempotency_key=command_key,
            actor=actor,
        )
        order = create_paper_execution_order(
            command,
            intent=intent,
            decision=decision,
            account_state=account_state,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=order_created_at,
        )
        result.update(
            risk_handoff=risk_handoff,
            command=command,
            order=order,
        )
    return result


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0", "0"), ("1", "1"), ("1.25", "1.25"), ("9999.99999999", "9999.99999999")],
)
def test_basis_points_parse_exact_canonical_values(
    text: str,
    expected: str,
) -> None:
    value = PaperExecutionBasisPoints.parse(text)
    assert value.to_json_value() == expected
    assert value == PaperExecutionBasisPoints.parse(expected)
    assert hash(value) == hash(PaperExecutionBasisPoints.parse(expected))


@pytest.mark.parametrize(
    "value",
    [
        1.0,
        True,
        None,
        "-1",
        "10000",
        "1e-2",
        "1.0",
        "01",
        "NaN",
        "Infinity",
        "0.000000001",
        " 1",
    ],
)
def test_basis_points_reject_noncanonical_or_out_of_range(value: object) -> None:
    with pytest.raises(ValueError):
        PaperExecutionBasisPoints.parse(value)  # type: ignore[arg-type]


def test_policy_is_deterministic_sensitive_immutable_and_json_safe() -> None:
    policy = _policy()
    assert policy == _policy()
    assert validate_paper_execution_policy_reference(policy) is policy
    json.dumps(policy.to_dict(), allow_nan=False)
    changed = [
        _policy(max_fill_quantity_per_trade_event=PaperQuantity.parse("5")),
        _policy(slippage_bps=PaperExecutionBasisPoints.parse("1.5")),
        _policy(commission_bps=PaperExecutionBasisPoints.parse("0.6")),
        _policy(fee_bps=PaperExecutionBasisPoints.parse("0.1")),
        _policy(buy_tax_bps=PaperExecutionBasisPoints.parse("0.1")),
        _policy(sell_tax_bps=PaperExecutionBasisPoints.parse("2.1")),
    ]
    assert all(
        item.configuration_digest != policy.configuration_digest for item in changed
    )
    assert all(item.reference_digest != policy.reference_digest for item in changed)
    with pytest.raises(FrozenInstanceError):
        policy.policy_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError):
        _policy(max_fill_quantity_per_trade_event=PaperQuantity.parse("0"))


def test_exact_handoffs_and_order_preserve_authority_without_mutation() -> None:
    data = _fixture()
    state_before = data["state"].to_dict()
    cursor_before = data["engine"].cursor
    decision_before = data["decision"].to_dict()

    account = create_paper_execution_account_handoff_reference(
        intent=data["intent"],
        account_state=data["state"],
    )
    market = create_paper_execution_market_handoff_reference(
        calendar=data["calendar"],
        session=data["session"],
        replay_engine=data["engine"],
        intent=data["intent"],
        decision=data["decision"],
    )
    risk = create_paper_execution_risk_handoff_reference(
        decision=data["decision"],
        intent=data["intent"],
    )
    assert validate_paper_execution_account_handoff_reference(account) is account
    assert validate_paper_execution_market_handoff_reference(market) is market
    assert validate_paper_execution_risk_handoff_reference(risk) is risk
    assert "price" not in risk.to_dict()
    assert data["state"].to_dict() == state_before
    assert data["engine"].cursor == cursor_before
    assert data["decision"].to_dict() == decision_before

    order = data["order"]
    assert validate_paper_execution_order(order) is order
    assert order.execution_order_id == f"peo_{order.execution_order_digest}"
    assert order.side == data["intent"].side
    assert order.requested_quantity == data["intent"].requested_quantity
    assert data["state"].to_dict() == state_before
    assert data["engine"].cursor == cursor_before


def test_stale_account_and_market_handoffs_fail_without_repair_or_progression() -> None:
    data = _fixture()
    cash_command = create_post_paper_cash_movement_command(
        account_id=data["state"].account_identity.account_id,
        expected_account_version=data["state"].head_version,
        command_idempotency_key="advance-cash-s208",
        actor="founder",
        reason="Make old allow stale",
        movement_type="deposit",
        requested_amount=PaperMoney.parse("1"),
    )
    bundle = apply_paper_cash_movement(
        data["state"].to_cash_state(),
        cash_command,
        event_id="account-s208-event-3",
        cash_entry_id="account-s208-cash-3",
        recorded_timestamp_utc=CREATED + timedelta(hours=5),
    )
    stale_state = replay_paper_account_ledger([*data["history"], bundle])
    with pytest.raises(ValueError, match="stale|mismatched"):
        create_paper_execution_account_handoff_reference(
            intent=data["intent"],
            account_state=stale_state,
        )

    engine = data["engine"]
    assert engine.next_event() is not None
    cursor_before = engine.cursor
    with pytest.raises(ValueError):
        create_paper_execution_market_handoff_reference(
            calendar=data["calendar"],
            session=data["session"],
            replay_engine=engine,
            intent=data["intent"],
            decision=data["decision"],
        )
    assert engine.cursor == cursor_before


def test_non_active_account_and_non_running_replay_fail_closed() -> None:
    frozen = _fixture()
    object.__setattr__(frozen["state"], "lifecycle_status", "frozen")
    with pytest.raises(ValueError, match="active"):
        create_paper_execution_account_handoff_reference(
            intent=frozen["intent"],
            account_state=frozen["state"],
        )

    paused = _fixture()
    paused["engine"].pause()
    paused_cursor = paused["engine"].cursor
    with pytest.raises(ValueError, match="running"):
        create_paper_execution_market_handoff_reference(
            calendar=paused["calendar"],
            session=paused["session"],
            replay_engine=paused["engine"],
            intent=paused["intent"],
            decision=paused["decision"],
        )
    assert paused["engine"].cursor == paused_cursor

    ready_source = _fixture()
    ready_engine = MarketDataReplayEngine(
        replay_id=ready_source["engine"].cursor.replay_id,
        events=ready_source["engine"].events,
    )
    ready_cursor = ready_engine.cursor
    with pytest.raises(ValueError, match="running"):
        create_paper_execution_market_handoff_reference(
            calendar=ready_source["calendar"],
            session=ready_source["session"],
            replay_engine=ready_engine,
            intent=ready_source["intent"],
            decision=ready_source["decision"],
        )
    assert ready_engine.cursor == ready_cursor


def test_rejected_decision_cannot_become_execution_handoff() -> None:
    data = _fixture(cash="100")
    assert data["decision"].outcome == "reject"
    with pytest.raises(ValueError, match="allow"):
        create_paper_execution_risk_handoff_reference(
            decision=data["decision"],
            intent=data["intent"],
        )


def test_commands_are_exact_deterministic_and_contain_no_execution_result() -> None:
    data = _fixture()
    command = data["command"]
    assert validate_create_paper_execution_order_command(command) is command
    assert command == create_paper_execution_order_command(
        order_intent_reference=command.order_intent_reference,
        risk_handoff_reference=command.risk_handoff_reference,
        execution_policy_reference=command.execution_policy_reference,
        command_idempotency_key=command.command_idempotency_key,
        actor=command.actor,
    )
    assert not {
        "price",
        "fill",
        "status",
        "account_delta",
        "market_event",
    }.intersection(command.to_dict())
    with pytest.raises(ValueError):
        create_paper_execution_order_command(
            order_intent_reference=command.order_intent_reference,
            risk_handoff_reference=command.risk_handoff_reference,
            execution_policy_reference=command.execution_policy_reference,
            command_idempotency_key=" ",
            actor="founder",
        )

    reference = create_paper_execution_order_reference(data["order"])
    step = create_step_paper_execution_order_command(
        execution_order_reference=reference,
        expected_execution_version=0,
        command_idempotency_key="step-s208",
        actor="founder",
    )
    assert validate_step_paper_execution_order_command(step) is step
    assert set(step.to_dict()) == {
        "schema_version",
        "execution_order_reference",
        "expected_execution_version",
        "command_idempotency_key",
        "actor",
        "command_digest",
    }
    for invalid in (-1, True, 1.5):
        with pytest.raises(ValueError):
            create_step_paper_execution_order_command(
                execution_order_reference=reference,
                expected_execution_version=invalid,  # type: ignore[arg-type]
                command_idempotency_key="step-s208",
                actor="founder",
            )


def test_order_business_identity_excludes_command_and_audit_provenance() -> None:
    first = _fixture()
    second = _fixture(
        command_key="alternate-key-s208",
        actor="operator",
        order_created_at=CREATED + timedelta(days=1),
    )
    assert first["order"].execution_order_id == second["order"].execution_order_id
    assert (
        first["order"].execution_order_digest == second["order"].execution_order_digest
    )
    assert first["order"].origin_command_digest != second["order"].origin_command_digest
    assert first["order"].created_at != second["order"].created_at
    assert first["order"].to_dict() != second["order"].to_dict()


def test_order_reference_tampering_and_arbitrary_construction_fail_closed() -> None:
    order = _fixture()["order"]
    reference = create_paper_execution_order_reference(order)
    assert validate_paper_execution_order_reference(reference) is reference
    assert reference.to_dict() == {
        "schema_version": 1,
        "execution_order_id": order.execution_order_id,
        "execution_order_digest": order.execution_order_digest,
    }
    with pytest.raises(TypeError):
        PaperExecutionOrder()  # type: ignore[call-arg]
    object.__setattr__(order, "side", "sell")
    with pytest.raises(ValueError):
        validate_paper_execution_order(order)


def test_initial_and_controlled_derived_lifecycle_state() -> None:
    order = _fixture()["order"]
    initial = create_initial_paper_execution_order_state(order)
    assert initial.to_dict() == {
        "schema_version": 1,
        "execution_order_reference": create_paper_execution_order_reference(
            order
        ).to_dict(),
        "execution_version": 0,
        "status": PAPER_EXECUTION_ORDER_STATUS_WORKING,
        "requested_quantity": "6",
        "cumulative_filled_quantity": "0",
        "remaining_quantity": "6",
        "terminal": False,
    }
    assert validate_paper_execution_order_state(initial) is initial

    cases = [
        ("2", False, PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED, False),
        ("6", False, PAPER_EXECUTION_ORDER_STATUS_FILLED, True),
        ("0", True, PAPER_EXECUTION_ORDER_STATUS_REJECTED, True),
        ("2", True, PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED, True),
    ]
    for index, (filled, rejected, status, terminal) in enumerate(cases, 1):
        state = _derive_paper_execution_order_state(
            order,
            execution_version=index,
            cumulative_filled_quantity=PaperQuantity.parse(filled),
            terminal_rejected=rejected,
        )
        assert state.status == status
        assert state.terminal is terminal
        assert (
            state.cumulative_filled_quantity.decimal_value
            + state.remaining_quantity.decimal_value
            == state.requested_quantity.decimal_value
        )
        assert validate_paper_execution_order_state(state) is state
    with pytest.raises(ValueError):
        _derive_paper_execution_order_state(
            order,
            execution_version=1,
            cumulative_filled_quantity=PaperQuantity.parse("7"),
            terminal_rejected=False,
        )
    with pytest.raises(ValueError):
        _derive_paper_execution_order_state(
            order,
            execution_version=1,
            cumulative_filled_quantity=PaperQuantity.parse("6"),
            terminal_rejected=True,
        )


def test_all_public_s208_exports_are_stable_strict_json() -> None:
    data = _fixture()
    values = [
        data["policy"],
        data["risk_handoff"],
        data["command"],
        data["order"],
        create_paper_execution_order_reference(data["order"]),
        create_initial_paper_execution_order_state(data["order"]),
    ]
    for value in values:
        first = json.dumps(
            value.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        second = json.dumps(
            value.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert first == second
