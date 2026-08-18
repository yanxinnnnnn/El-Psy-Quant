"""Focused deterministic Sprint 209 one-event execution coverage."""

from __future__ import annotations

import json
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
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
)
from el_psy_quant.paper_execution import (
    PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED,
    PAPER_EXECUTION_ATTEMPT_RESULT_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL,
    PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED,
    PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE,
    PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH,
    PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID,
    PAPER_EXECUTION_ORDER_STATUS_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED,
    PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED,
    PAPER_EXECUTION_ORDER_STATUS_REJECTED,
    PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_CASH,
    PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_POSITION,
    PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_NOTIONAL,
    PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_QUANTITY,
    PAPER_EXECUTION_RISK_REASON_NEGATIVE_SELL_PROCEEDS,
    PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED,
    PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED,
    PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED,
    PaperExecutionBasisPoints,
    create_paper_execution_cost_evidence,
    create_paper_execution_order,
    create_paper_execution_order_command,
    create_paper_execution_order_reference,
    create_paper_execution_policy_reference,
    create_paper_execution_risk_handoff_reference,
    create_step_paper_execution_order_command,
    reconstruct_paper_execution_order_state,
    step_paper_execution_order,
    validate_paper_execution_attempt,
    validate_paper_execution_cost_evidence,
    validate_paper_execution_fill,
    validate_paper_execution_price_evidence,
    validate_paper_execution_risk_revalidation,
    validate_paper_execution_step_result,
)
from el_psy_quant.paper_execution.attempts import _build_attempt
from el_psy_quant.paper_execution.costs import _build as _build_cost_evidence
from el_psy_quant.paper_execution.execution_risk import (
    _derive as _derive_execution_risk,
)
from el_psy_quant.paper_execution.fills import (
    _build_fill,
    _create_paper_execution_fill,
)
from el_psy_quant.paper_execution.orders import _build_order
from el_psy_quant.paper_execution.pricing import _build as _build_price_evidence
from el_psy_quant.paper_execution.upstream_references import _build_market_handoff
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
CREATED = datetime(2026, 8, 18, 8, tzinfo=UTC)
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


def _account_state(
    *,
    cash: str = "1000",
    quantity: str = "4",
    account_id: str = "account-s209",
):
    identity = PaperAccountIdentity(
        account_id=account_id,
        display_name="Sprint 209 Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )
    command = create_paper_account_command(
        account_identity=identity,
        initial_cash=PaperMoney.parse(cash),
        command_idempotency_key=f"create-{account_id}",
        actor="founder",
    )
    created = create_paper_account_event_bundle(
        command,
        event_id=f"{account_id}-event-1",
        cash_entry_id=f"{account_id}-cash-1",
        recorded_timestamp_utc=CREATED,
    )
    history: list[Any] = [created]
    state = replay_paper_account_ledger(history)
    if PaperQuantity.parse(quantity).decimal_value > 0:
        position_command = create_post_paper_position_adjustment_command(
            account_id=identity.account_id,
            expected_account_version=state.head_version,
            command_idempotency_key=f"position-{account_id}",
            actor="founder",
            reason="Sprint 209 opening position",
            symbol=INSTRUMENT,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse(quantity),
            signed_cost_basis_delta=PaperMoney.parse("0"),
        )
        position = apply_paper_position_adjustment(
            state,
            position_command,
            event_id=f"{account_id}-event-2",
            position_entry_id=f"{account_id}-position-2",
            recorded_timestamp_utc=CREATED + timedelta(minutes=1),
        )
        history.append(position)
        state = replay_paper_account_ledger(history)
    return state


def _scenario(
    *,
    cash: str = "1000",
    current_quantity: str = "4",
    target_quantity: str = "10",
    future_events: list[dict[str, object]] | None = None,
    execution_policy=None,
    maximum_order_quantity: str | None = None,
    maximum_order_notional: str | None = None,
):
    calendar = create_trading_calendar(
        id="xnys-s209",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=1,
        created_at=CREATED,
    )
    local = ZoneInfo("America/New_York")
    session = create_trading_session(
        id="xnys-2026-08-18-regular",
        calendar_id=calendar.id,
        trading_date=date(2026, 8, 18),
        open_time=datetime(2026, 8, 18, 9, 30, tzinfo=local),
        close_time=datetime(2026, 8, 18, 16, tzinfo=local),
        session_type="regular",
    )
    current_event = create_market_data_event(
        event_id="trade-s209-current",
        instrument_id=INSTRUMENT,
        event_time=datetime(2026, 8, 18, 14, tzinfo=UTC),
        event_type="trade",
        payload={"price": 100},
        source="fixture:s209",
    )
    specs = (
        [
            {
                "instrument_id": INSTRUMENT,
                "event_type": "trade",
                "price": 101,
            }
        ]
        if future_events is None
        else future_events
    )
    events = [current_event]
    for index, spec in enumerate(specs, 1):
        payload = spec.get("payload", {"price": spec.get("price")})
        events.append(
            create_market_data_event(
                event_id=f"event-s209-{index}",
                instrument_id=str(spec.get("instrument_id", INSTRUMENT)),
                event_time=spec.get(
                    "event_time",
                    current_event.event_time + timedelta(minutes=index),
                ),  # type: ignore[arg-type]
                event_type=str(spec.get("event_type", "trade")),
                payload=payload,
                source="fixture:s209",
            )
        )
    engine = MarketDataReplayEngine(replay_id="replay-s209", events=events)
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
        target_position_quantity=PaperQuantity.parse(target_quantity),
    )
    signal_command = create_evaluate_strategy_signal_command(
        strategy_runtime_reference=runtime,
        market_reference=market_reference,
        command_idempotency_key="signal-s209",
        actor="founder",
    )
    signal = _create_strategy_signal_from_evaluation(
        command=signal_command,
        target_position_quantity=PaperQuantity.parse(target_quantity),
        created_at=CREATED + timedelta(hours=1),
    )
    account_state = _account_state(cash=cash, quantity=current_quantity)
    intent_command = create_derive_order_intent_command(
        signal=signal,
        account_state=account_state,
        command_idempotency_key="intent-s209",
        actor="founder",
    )
    intent = derive_order_intent(
        intent_command,
        signal=signal,
        account_state=account_state,
        created_at=CREATED + timedelta(hours=2),
    )
    risk_policy = create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=(
            None
            if maximum_order_quantity is None
            else PaperQuantity.parse(maximum_order_quantity)
        ),
        maximum_order_notional=(
            None
            if maximum_order_notional is None
            else PaperMoney.parse(maximum_order_notional)
        ),
    )
    risk_command = create_evaluate_pre_trade_risk_command(
        intent=intent,
        risk_policy_reference=risk_policy,
        command_idempotency_key="risk-s209",
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
    assert decision.outcome == "allow"
    policy = execution_policy or _policy()
    risk_handoff = create_paper_execution_risk_handoff_reference(
        decision=decision,
        intent=intent,
    )
    create_command = create_paper_execution_order_command(
        order_intent_reference=create_order_intent_reference(intent),
        risk_handoff_reference=risk_handoff,
        execution_policy_reference=policy,
        command_idempotency_key="create-order-s209",
        actor="founder",
    )
    order = create_paper_execution_order(
        create_command,
        intent=intent,
        decision=decision,
        account_state=account_state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED + timedelta(hours=4),
    )
    return {
        "calendar": calendar,
        "session": session,
        "engine": engine,
        "state": account_state,
        "order": order,
        "decision": decision,
    }


def _step(data, version: int, *, attempts=(), fills=(), account_state=None):
    command = create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(
            data["order"]
        ),
        expected_execution_version=version,
        command_idempotency_key=f"step-s209-{version}",
        actor="founder",
    )
    return step_paper_execution_order(
        command,
        order=data["order"],
        account_state=account_state or data["state"],
        calendar=data["calendar"],
        session=data["session"],
        replay_engine=data["engine"],
        created_at=CREATED + timedelta(hours=5, minutes=version),
        attempts=attempts,
        fills=fills,
    )


def _rebuild_risk(risk, **changes: object):
    values: dict[str, object] = {
        "order_reference": risk.execution_order_reference,
        "execution_version": risk.execution_version,
        "account_id": risk.account_id,
        "account_head_version": risk.account_head_version,
        "account_head_event_id": risk.account_head_event_id,
        "account_head_chain_digest": risk.account_head_chain_digest,
        "available_cash": risk.available_cash,
        "current_instrument_quantity": risk.current_instrument_quantity,
        "side": risk.execution_price_evidence.side,
        "risk_policy_reference": risk.risk_policy_reference,
        "execution_price_evidence": risk.execution_price_evidence,
        "cost_evidence": risk.cost_evidence,
        "requested_quantity": risk.requested_quantity,
        "remaining_quantity_before_step": risk.remaining_quantity_before_step,
        "candidate_fill_quantity": risk.candidate_fill_quantity,
        "cumulative_filled_gross_notional": (
            risk.cumulative_filled_gross_notional
        ),
    }
    values.update(changes)
    return _derive_execution_risk(**values)  # type: ignore[arg-type]


def _rebuild_attempt(attempt, *, risk, result: str | None = None):
    attempt_result = result or attempt.attempt_result
    return _build_attempt(
        execution_order_reference=attempt.execution_order_reference,
        prior_order_state=attempt.prior_order_state,
        pre_step_cursor=attempt.pre_step_cursor,
        post_step_cursor=attempt.post_step_cursor,
        consumed_event_reference=attempt.consumed_event_reference,
        attempt_result=attempt_result,
        no_fill_reason_code=None,
        terminal_reason_code=(
            PAPER_EXECUTION_TERMINAL_REASON_EXECUTION_RISK_REJECTED
            if attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED
            else attempt.terminal_reason_code
        ),
        risk_revalidation=risk,
        created_at=attempt.created_at,
    )


def test_full_fill_has_exact_price_cost_risk_attempt_and_fill_authority() -> None:
    data = _scenario()
    decision_before = data["decision"].to_dict()
    account_before = data["state"].to_dict()
    result = _step(data, 0)

    assert validate_paper_execution_step_result(result) is result
    assert result.attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_FILL
    assert result.attempt.attempt_id == f"pea_{result.attempt.attempt_digest}"
    assert result.fill is not None
    assert result.fill.fill_id == f"pef_{result.fill.fill_digest}"
    assert result.fill.fill_quantity.to_json_value() == "6"
    assert result.fill.execution_price_evidence.base_trade_price.to_json_value() == "101"
    assert result.fill.execution_price_evidence.execution_price.to_json_value() == (
        "101.012625"
    )
    assert result.fill.cost_evidence.gross_notional.to_json_value() == "606.07575"
    assert result.fill.cost_evidence.commission.to_json_value() == "0.03030379"
    assert result.fill.cost_evidence.total_charges.to_json_value() == "0.03030379"
    assert result.attempt.risk_revalidation is not None
    assert result.attempt.risk_revalidation.outcome == "allow"
    assert result.attempt.risk_revalidation.reason_codes == ()
    assert result.order_state.status == PAPER_EXECUTION_ORDER_STATUS_FILLED
    assert result.order_state.execution_version == 1
    assert data["state"].to_dict() == account_before
    assert data["decision"].to_dict() == decision_before


def test_partial_fills_reconstruct_contiguously_and_next_event_runs_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _scenario(
        future_events=[{"price": 101}, {"price": 102}, {"price": 103}],
        execution_policy=_policy(
            max_fill_quantity_per_trade_event=PaperQuantity.parse("2")
        ),
    )
    original = MarketDataReplayEngine.next_event
    calls = 0

    def counted(engine: MarketDataReplayEngine):
        nonlocal calls
        calls += 1
        return original(engine)

    monkeypatch.setattr(MarketDataReplayEngine, "next_event", counted)
    first = _step(data, 0)
    assert calls == 1
    assert first.order_state.status == PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED
    second = _step(
        data,
        1,
        attempts=(first.attempt,),
        fills=(first.fill,),
    )
    third = _step(
        data,
        2,
        attempts=(first.attempt, second.attempt),
        fills=(first.fill, second.fill),
    )
    attempts = (first.attempt, second.attempt, third.attempt)
    fills = (first.fill, second.fill, third.fill)
    assert calls == 3
    assert third.order_state.status == PAPER_EXECUTION_ORDER_STATUS_FILLED
    assert third.attempt.terminal_reason_code is None
    assert reconstruct_paper_execution_order_state(
        data["order"], attempts=attempts, fills=fills  # type: ignore[arg-type]
    ) == third.order_state


def test_partial_fill_on_final_event_rejects_remainder_in_same_attempt() -> None:
    data = _scenario(
        execution_policy=_policy(
            max_fill_quantity_per_trade_event=PaperQuantity.parse("2")
        )
    )
    result = _step(data, 0)
    assert result.fill is not None
    assert result.attempt.terminal_reason_code == (
        PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
    )
    assert result.order_state.status == (
        PAPER_EXECUTION_ORDER_STATUS_PARTIALLY_FILLED_REJECTED
    )


@pytest.mark.parametrize(
    ("spec", "reason"),
    [
        (
            {"instrument_id": "XNYS:MSFT", "event_type": "trade", "price": 101},
            PAPER_EXECUTION_NO_FILL_REASON_INSTRUMENT_MISMATCH,
        ),
        (
            {"event_type": "quote", "payload": {"bid": 100}},
            PAPER_EXECUTION_NO_FILL_REASON_EVENT_TYPE_NOT_TRADE,
        ),
        ({"event_type": "trade", "payload": {}}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": True}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": "101"}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": None}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": 0}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": -1}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
        ({"price": 0.000000001}, PAPER_EXECUTION_NO_FILL_REASON_TRADE_PRICE_INVALID),
    ],
)
def test_invalid_or_irrelevant_final_events_are_consumed_no_fill(
    spec: dict[str, object],
    reason: str,
) -> None:
    data = _scenario(future_events=[spec])
    result = _step(data, 0)
    assert result.attempt.attempt_result == PAPER_EXECUTION_ATTEMPT_RESULT_NO_FILL
    assert result.attempt.no_fill_reason_code == reason
    assert result.attempt.terminal_reason_code == (
        PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
    )
    assert result.fill is None
    assert result.order_state.status == PAPER_EXECUTION_ORDER_STATUS_REJECTED
    assert data["engine"].cursor.status == "completed"


def test_session_boundary_rejects_without_consuming_close_event() -> None:
    data = _scenario(
        future_events=[
            {
                "price": 101,
                "event_time": datetime(2026, 8, 18, 20, tzinfo=UTC),
            }
        ]
    )
    before = data["engine"].cursor
    result = _step(data, 0)
    assert result.attempt.attempt_result == (
        PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED
    )
    assert result.attempt.terminal_reason_code == (
        PAPER_EXECUTION_TERMINAL_REASON_SESSION_EXHAUSTED
    )
    assert result.attempt.consumed_event_reference is None
    assert data["engine"].cursor == before
    assert result.order_state.status == PAPER_EXECUTION_ORDER_STATUS_REJECTED


def test_replay_exhausted_boundary_without_next_event_does_not_consume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _scenario(future_events=[{"price": 101}])
    assert data["engine"].next_event() == data["engine"].events[-1]
    original_order = data["order"]
    exhausted_handoff = _build_market_handoff(
        calendar=data["calendar"],
        session=data["session"],
        replay_engine=data["engine"],
    )
    data["order"] = _build_order(
        order_intent_reference=original_order.order_intent_reference,
        risk_handoff_reference=original_order.risk_handoff_reference,
        account_handoff_reference=original_order.account_handoff_reference,
        market_handoff_reference=exhausted_handoff,
        execution_policy_reference=original_order.execution_policy_reference,
        account_id=original_order.account_id,
        instrument_id=original_order.instrument_id,
        side=original_order.side,
        requested_quantity=original_order.requested_quantity,
        origin_command_idempotency_key=(
            original_order.origin_command_idempotency_key
        ),
        origin_command_digest=original_order.origin_command_digest,
        origin_actor=original_order.origin_actor,
        created_at=original_order.created_at,
    )
    before = data["engine"].cursor
    assert before.status == "completed"

    def forbidden_next_event(_engine: MarketDataReplayEngine):
        pytest.fail("boundary exhaustion must not call next_event")

    monkeypatch.setattr(
        MarketDataReplayEngine,
        "next_event",
        forbidden_next_event,
    )

    result = _step(data, 0)

    assert result.attempt.attempt_result == (
        PAPER_EXECUTION_ATTEMPT_RESULT_BOUNDARY_REJECTED
    )
    assert result.attempt.terminal_reason_code == (
        PAPER_EXECUTION_TERMINAL_REASON_REPLAY_EXHAUSTED
    )
    assert result.attempt.consumed_event_reference is None
    assert result.attempt.pre_step_cursor == before
    assert result.attempt.post_step_cursor == before
    assert data["engine"].cursor == before
    assert result.order_state.status == PAPER_EXECUTION_ORDER_STATUS_REJECTED


def test_stale_version_paused_replay_and_incompatible_account_do_not_advance() -> None:
    data = _scenario(future_events=[{"price": 101}, {"price": 102}])
    before = data["engine"].cursor
    stale = create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(
            data["order"]
        ),
        expected_execution_version=1,
        command_idempotency_key="stale-s209",
        actor="founder",
    )
    with pytest.raises(ValueError, match="expected_execution_version"):
        step_paper_execution_order(
            stale,
            order=data["order"],
            account_state=data["state"],
            calendar=data["calendar"],
            session=data["session"],
            replay_engine=data["engine"],
            created_at=CREATED,
        )
    assert data["engine"].cursor == before

    ready_engine = MarketDataReplayEngine(
        replay_id=data["engine"].cursor.replay_id,
        events=data["engine"].events,
    )
    ready_before = ready_engine.cursor
    ready_command = create_step_paper_execution_order_command(
        execution_order_reference=create_paper_execution_order_reference(
            data["order"]
        ),
        expected_execution_version=0,
        command_idempotency_key="ready-s209",
        actor="founder",
    )
    with pytest.raises(ValueError, match="running or exhausted"):
        step_paper_execution_order(
            ready_command,
            order=data["order"],
            account_state=data["state"],
            calendar=data["calendar"],
            session=data["session"],
            replay_engine=ready_engine,
            created_at=CREATED,
        )
    assert ready_engine.cursor == ready_before

    data["engine"].pause()
    paused = data["engine"].cursor
    with pytest.raises(ValueError, match="running or exhausted"):
        _step(data, 0)
    assert data["engine"].cursor == paused
    data["engine"].resume()
    running = data["engine"].cursor
    wrong_account = _account_state(account_id="other-account-s209")
    with pytest.raises(ValueError, match="account authority"):
        _step(data, 0, account_state=wrong_account)
    assert data["engine"].cursor == running


def test_execution_price_rounds_half_even_and_ignores_m33_price_authority() -> None:
    data = _scenario(
        future_events=[{"price": 3}],
        execution_policy=_policy(
            slippage_bps=PaperExecutionBasisPoints.parse("0.00005"),
            commission_bps=PaperExecutionBasisPoints.parse("0"),
        ),
    )
    result = _step(data, 0)
    assert result.fill is not None
    price = result.fill.execution_price_evidence
    assert price.base_trade_price.to_json_value() == "3"
    assert price.pre_round_execution_price == "3.000000015"
    assert price.execution_price.to_json_value() == "3.00000002"
    assert price.rounding_applied is True
    assert price.execution_event_reference.event_id == "event-s209-1"
    assert price.execution_event_reference.event_id != (
        data["order"].market_handoff_reference.current_event_id
    )
    assert validate_paper_execution_price_evidence(price) is price


def test_cost_components_round_independently_with_half_even() -> None:
    data = _scenario(
        cash="100",
        current_quantity="0",
        target_quantity="1",
        future_events=[{"price": 3}],
        execution_policy=_policy(
            slippage_bps=PaperExecutionBasisPoints.parse("0"),
            commission_bps=PaperExecutionBasisPoints.parse("0.00005"),
            fee_bps=PaperExecutionBasisPoints.parse("0.00005"),
            buy_tax_bps=PaperExecutionBasisPoints.parse("0.00005"),
        ),
    )
    result = _step(data, 0)
    assert result.fill is not None
    costs = result.fill.cost_evidence
    assert costs.commission_pre_round == "0.000000015"
    assert costs.commission.to_json_value() == "0.00000002"
    assert costs.fee.to_json_value() == "0.00000002"
    assert costs.tax.to_json_value() == "0.00000002"
    assert costs.total_charges.to_json_value() == "0.00000006"
    assert validate_paper_execution_cost_evidence(costs) is costs


@pytest.mark.parametrize(
    ("scenario_changes", "account_override", "reason"),
    [
        (
            {"cash": "700", "future_events": [{"price": 200}]},
            None,
            PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_CASH,
        ),
        (
            {
                "cash": "2000",
                "future_events": [{"price": 200}],
                "maximum_order_notional": "700",
            },
            None,
            PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_NOTIONAL,
        ),
        (
            {
                "cash": "1000",
                "current_quantity": "10",
                "target_quantity": "2",
            },
            {"cash": "1000", "quantity": "2"},
            PAPER_EXECUTION_RISK_REASON_INSUFFICIENT_POSITION,
        ),
        (
            {
                "cash": "1000",
                "current_quantity": "10",
                "target_quantity": "2",
                "execution_policy": _policy(
                    commission_bps=PaperExecutionBasisPoints.parse("9999"),
                    fee_bps=PaperExecutionBasisPoints.parse("9999"),
                    sell_tax_bps=PaperExecutionBasisPoints.parse("9999"),
                ),
            },
            None,
            PAPER_EXECUTION_RISK_REASON_NEGATIVE_SELL_PROCEEDS,
        ),
    ],
)
def test_execution_risk_rejections_consume_once_without_fill(
    scenario_changes: dict[str, object],
    account_override: dict[str, str] | None,
    reason: str,
) -> None:
    data = _scenario(**scenario_changes)  # type: ignore[arg-type]
    account = (
        data["state"]
        if account_override is None
        else _account_state(**account_override)
    )
    before_position = data["engine"].cursor.position
    result = _step(data, 0, account_state=account)
    assert result.attempt.attempt_result == (
        PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED
    )
    assert result.fill is None
    assert result.attempt.risk_revalidation is not None
    risk = result.attempt.risk_revalidation
    assert risk.outcome == "reject"
    assert reason in risk.reason_codes
    assert tuple(
        rule.reason_code for rule in risk.rules if rule.reason_code is not None
    ) == risk.reason_codes
    assert validate_paper_execution_risk_revalidation(risk) is risk
    assert data["engine"].cursor.position == before_position + 1


def test_maximum_notional_uses_prior_fill_gross_plus_remaining_at_current_price(
) -> None:
    data = _scenario(
        cash="2000",
        current_quantity="4",
        target_quantity="10",
        future_events=[{"price": 10}, {"price": 200}],
        execution_policy=_policy(
            max_fill_quantity_per_trade_event=PaperQuantity.parse("2"),
            slippage_bps=PaperExecutionBasisPoints.parse("0"),
            commission_bps=PaperExecutionBasisPoints.parse("0"),
        ),
        maximum_order_notional="650",
    )
    first = _step(data, 0)
    assert first.fill is not None
    assert first.fill.cost_evidence.gross_notional.to_json_value() == "20"

    second = _step(
        data,
        1,
        attempts=(first.attempt,),
        fills=(first.fill,),
    )

    assert second.fill is None
    assert second.attempt.attempt_result == (
        PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED
    )
    assert second.attempt.risk_revalidation is not None
    risk = second.attempt.risk_revalidation
    assert risk.cumulative_filled_gross_notional.to_json_value() == "20"
    assert risk.remaining_quantity_before_step.to_json_value() == "4"
    assert risk.projected_order_gross_notional.to_json_value() == "820"
    assert PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_NOTIONAL in risk.reason_codes
    assert reconstruct_paper_execution_order_state(
        data["order"],
        attempts=(first.attempt, second.attempt),
        fills=(first.fill,),
    ) == second.order_state

    corrupt_risk = _rebuild_risk(
        risk,
        cumulative_filled_gross_notional=PaperMoney.parse("0"),
    )
    corrupt_attempt = _rebuild_attempt(second.attempt, risk=corrupt_risk)
    with pytest.raises(ValueError, match="Order/prior state"):
        reconstruct_paper_execution_order_state(
            data["order"],
            attempts=(first.attempt, corrupt_attempt),
            fills=(first.fill,),
        )


def test_history_corruption_duplicate_fill_and_attempt_after_terminal_fail_closed() -> None:
    data = _scenario()
    result = _step(data, 0)
    assert result.fill is not None
    with pytest.raises(ValueError, match="duplicate Fills"):
        reconstruct_paper_execution_order_state(
            data["order"],
            attempts=(result.attempt,),
            fills=(result.fill, result.fill),
        )
    object.__setattr__(result.attempt, "execution_version_after", 3)
    with pytest.raises(ValueError):
        validate_paper_execution_attempt(result.attempt)


def test_history_rebinds_fill_quantity_price_and_cost_to_attempt_risk() -> None:
    data = _scenario()
    result = _step(data, 0)
    assert result.fill is not None
    fill = result.fill
    policy = data["order"].execution_policy_reference

    smaller_quantity = PaperQuantity.parse("1")
    smaller_costs = create_paper_execution_cost_evidence(
        execution_price_evidence=fill.execution_price_evidence,
        fill_quantity=smaller_quantity,
        execution_policy_reference=policy,
    )
    quantity_mismatch = _build_fill(
        execution_order_reference=fill.execution_order_reference,
        attempt_reference=fill.attempt_reference,
        execution_event_reference=fill.execution_event_reference,
        side=fill.side,
        fill_quantity=smaller_quantity,
        execution_price_evidence=fill.execution_price_evidence,
        cost_evidence=smaller_costs,
        created_at=fill.created_at,
    )
    alternate_price = _build_price_evidence(
        execution_event_reference=fill.execution_event_reference,
        side=fill.side,
        base_trade_price=PaperMoney.parse("99"),
        slippage_bps=policy.slippage_bps,
    )
    alternate_price_costs = create_paper_execution_cost_evidence(
        execution_price_evidence=alternate_price,
        fill_quantity=fill.fill_quantity,
        execution_policy_reference=policy,
    )
    price_mismatch = _build_fill(
        execution_order_reference=fill.execution_order_reference,
        attempt_reference=fill.attempt_reference,
        execution_event_reference=fill.execution_event_reference,
        side=fill.side,
        fill_quantity=fill.fill_quantity,
        execution_price_evidence=alternate_price,
        cost_evidence=alternate_price_costs,
        created_at=fill.created_at,
    )
    alternate_costs = _build_cost_evidence(
        execution_price_evidence=fill.execution_price_evidence,
        fill_quantity=fill.fill_quantity,
        commission_bps=PaperExecutionBasisPoints.parse("2"),
        fee_bps=policy.fee_bps,
        side_tax_bps=policy.buy_tax_bps,
    )
    cost_mismatch = _build_fill(
        execution_order_reference=fill.execution_order_reference,
        attempt_reference=fill.attempt_reference,
        execution_event_reference=fill.execution_event_reference,
        side=fill.side,
        fill_quantity=fill.fill_quantity,
        execution_price_evidence=fill.execution_price_evidence,
        cost_evidence=alternate_costs,
        created_at=fill.created_at,
    )

    for corrupt_fill in (quantity_mismatch, price_mismatch, cost_mismatch):
        assert validate_paper_execution_fill(corrupt_fill) is corrupt_fill
        with pytest.raises(ValueError, match="Fill economics"):
            reconstruct_paper_execution_order_state(
                data["order"],
                attempts=(result.attempt,),
                fills=(corrupt_fill,),
            )


def test_history_rebinds_risk_order_state_policy_price_and_cost_authority() -> None:
    data = _scenario()
    result = _step(data, 0)
    assert result.attempt.risk_revalidation is not None
    original = result.attempt.risk_revalidation
    policy = data["order"].execution_policy_reference

    alternate_risk_policy = create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=PaperQuantity.parse("100"),
        maximum_order_notional=None,
    )
    alternate_price = _build_price_evidence(
        execution_event_reference=original.execution_price_evidence.execution_event_reference,
        side=original.execution_price_evidence.side,
        base_trade_price=original.execution_price_evidence.base_trade_price,
        slippage_bps=PaperExecutionBasisPoints.parse("2"),
    )
    alternate_price_costs = create_paper_execution_cost_evidence(
        execution_price_evidence=alternate_price,
        fill_quantity=original.candidate_fill_quantity,
        execution_policy_reference=policy,
    )
    alternate_costs = _build_cost_evidence(
        execution_price_evidence=original.execution_price_evidence,
        fill_quantity=original.candidate_fill_quantity,
        commission_bps=PaperExecutionBasisPoints.parse("2"),
        fee_bps=policy.fee_bps,
        side_tax_bps=policy.buy_tax_bps,
    )
    corrupt_risks = (
        _rebuild_risk(
            original,
            requested_quantity=PaperQuantity.parse("5"),
        ),
        _rebuild_risk(
            original,
            remaining_quantity_before_step=PaperQuantity.parse("5"),
        ),
        _rebuild_risk(
            original,
            cumulative_filled_gross_notional=PaperMoney.parse("1"),
        ),
        _rebuild_risk(
            original,
            risk_policy_reference=alternate_risk_policy,
        ),
        _rebuild_risk(
            original,
            execution_price_evidence=alternate_price,
            cost_evidence=alternate_price_costs,
        ),
        _rebuild_risk(original, cost_evidence=alternate_costs),
    )

    for corrupt_risk in corrupt_risks:
        corrupt_attempt = _rebuild_attempt(result.attempt, risk=corrupt_risk)
        corrupt_fill = _create_paper_execution_fill(
            attempt=corrupt_attempt,
            fill_quantity=corrupt_risk.candidate_fill_quantity,
            created_at=result.fill.created_at,  # type: ignore[union-attr]
        )
        with pytest.raises(ValueError):
            reconstruct_paper_execution_order_state(
                data["order"],
                attempts=(corrupt_attempt,),
                fills=(corrupt_fill,),
            )


def test_history_enforces_exact_frozen_per_event_cap() -> None:
    data = _scenario(
        execution_policy=_policy(
            max_fill_quantity_per_trade_event=PaperQuantity.parse("2")
        )
    )
    result = _step(data, 0)
    assert result.attempt.risk_revalidation is not None
    original = result.attempt.risk_revalidation
    quantity = PaperQuantity.parse("1")
    costs = create_paper_execution_cost_evidence(
        execution_price_evidence=original.execution_price_evidence,
        fill_quantity=quantity,
        execution_policy_reference=data["order"].execution_policy_reference,
    )
    risk = _rebuild_risk(
        original,
        candidate_fill_quantity=quantity,
        cost_evidence=costs,
    )
    attempt = _rebuild_attempt(result.attempt, risk=risk)
    fill = _create_paper_execution_fill(
        attempt=attempt,
        fill_quantity=quantity,
        created_at=result.fill.created_at,  # type: ignore[union-attr]
    )

    with pytest.raises(ValueError, match="per-event cap"):
        reconstruct_paper_execution_order_state(
            data["order"],
            attempts=(attempt,),
            fills=(fill,),
        )


def test_maximum_original_quantity_reject_is_unreachable_from_allow_handoff(
) -> None:
    data = _scenario()
    result = _step(data, 0)
    assert result.attempt.risk_revalidation is not None
    lower_policy = create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=PaperQuantity.parse("5"),
        maximum_order_notional=None,
    )
    risk = _rebuild_risk(
        result.attempt.risk_revalidation,
        risk_policy_reference=lower_policy,
    )
    assert risk.outcome == "reject"
    assert PAPER_EXECUTION_RISK_REASON_MAXIMUM_ORDER_QUANTITY in risk.reason_codes
    attempt = _rebuild_attempt(
        result.attempt,
        risk=risk,
        result=PAPER_EXECUTION_ATTEMPT_RESULT_RISK_REJECTED,
    )

    # A valid frozen M33 allow handoff cannot have requested quantity above its
    # maximum. Reconstruction therefore rejects a self-consistent M34 risk
    # record that tries to substitute such a lower policy after Order creation.
    with pytest.raises(ValueError, match="frozen Order policy"):
        reconstruct_paper_execution_order_state(
            data["order"], attempts=(attempt,), fills=()
        )


def test_new_authority_is_stable_strict_json_and_tamper_safe() -> None:
    data = _scenario()
    result = _step(data, 0)
    assert result.fill is not None
    values = [
        result,
        result.attempt,
        result.fill,
        result.fill.execution_event_reference,
        result.fill.execution_price_evidence,
        result.fill.cost_evidence,
        result.attempt.risk_revalidation,
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
    event_copy = result.fill.execution_event_reference.to_dict()
    event_copy["event_id"] = "changed"
    assert result.fill.execution_event_reference.event_id == "event-s209-1"
    object.__setattr__(result.fill, "fill_digest", "0" * 64)
    with pytest.raises(ValueError):
        validate_paper_execution_fill(result.fill)
