"""Focused deterministic coverage for Sprint 201 pre-trade risk evidence."""

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

from el_psy_quant.execution import OrderIntent as BacktestOrderIntent
from el_psy_quant.market_time import (
    MarketDataEvent,
    MarketDataReplayEngine,
    TradingCalendar,
    TradingSession,
    create_market_data_event,
    create_trading_calendar,
    create_trading_session,
)
from el_psy_quant.paper_account import (
    PaperAccountIdentity,
    PaperAccountLedgerState,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    apply_paper_cash_movement,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
)
from el_psy_quant.strategy_order import (
    EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
    LATEST_TRADE_PRICE_POLICY_ID,
    LONG_ONLY_CASH_RISK_POLICY_ID,
    PRE_TRADE_RISK_DECISION_SCHEMA_VERSION,
    PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION,
    PRE_TRADE_RISK_OUTCOME_ALLOW,
    PRE_TRADE_RISK_OUTCOME_REJECT,
    PRE_TRADE_RISK_POLICY_SCHEMA_VERSION,
    PRE_TRADE_RISK_PRICE_REFERENCE_SCHEMA_VERSION,
    PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
    PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
    PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL,
    PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
    PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION,
    PRE_TRADE_RISK_RULE_ORDER,
    EvaluatePreTradeRiskCommand,
    OrderIntent,
    OrderIntentNoAction,
    PreTradeRiskDecision,
    PreTradeRiskInputSnapshot,
    PreTradeRiskPolicyReference,
    PreTradeRiskPriceReference,
    PreTradeRiskRuleEvidence,
    StrategySignal,
    create_derive_order_intent_command,
    create_evaluate_pre_trade_risk_command,
    create_evaluate_strategy_signal_command,
    create_long_only_cash_risk_policy_reference,
    create_moving_average_crossover_runtime_reference,
    create_strategy_signal_market_reference,
    derive_order_intent,
    evaluate_pre_trade_risk,
    validate_evaluate_pre_trade_risk_command,
    validate_pre_trade_risk_decision,
    validate_pre_trade_risk_input_snapshot,
    validate_pre_trade_risk_policy_reference,
    validate_pre_trade_risk_price_reference,
    validate_pre_trade_risk_rule_evidence,
)
from el_psy_quant.strategy_order.signals import (
    _create_strategy_signal_from_evaluation,
)

UTC = timezone.utc
CREATED = datetime(2026, 7, 30, 9, tzinfo=UTC)
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


def _calendar(*, version: int = 1) -> TradingCalendar:
    return create_trading_calendar(
        id="xnys-2026",
        market="XNYS",
        timezone="America/New_York",
        calendar_version=version,
        created_at=CREATED,
    )


def _session(
    *,
    identity: str = "xnys-2026-07-28-regular",
) -> TradingSession:
    local = ZoneInfo("America/New_York")
    return create_trading_session(
        id=identity,
        calendar_id="xnys-2026",
        trading_date=date(2026, 7, 28),
        open_time=datetime(2026, 7, 28, 9, 30, tzinfo=local),
        close_time=datetime(2026, 7, 28, 16, tzinfo=local),
        session_type="regular",
    )


def _event(
    *,
    identity: str,
    minute: int,
    price: object = 100,
    instrument: str = INSTRUMENT,
    event_type: str = "trade",
) -> MarketDataEvent:
    payload: dict[str, object]
    if price is _MISSING:
        payload = {"nested": {"price": 100}}
    else:
        payload = {"price": price}
    return create_market_data_event(
        event_id=identity,
        instrument_id=instrument,
        event_time=datetime(2026, 7, 28, 14, minute, tzinfo=UTC),
        event_type=event_type,
        payload=payload,
        source="fixture:s201",
    )


_MISSING = object()


def _market_authority(
    *,
    current_price: object = 100,
    prior_events: list[MarketDataEvent] | None = None,
    future_event: MarketDataEvent | None = None,
    replay_id: str = "replay-s201",
    instrument: str = INSTRUMENT,
) -> tuple[
    TradingCalendar,
    TradingSession,
    MarketDataReplayEngine,
    MarketDataEvent,
]:
    current = _event(
        identity="signal-event-s201",
        minute=10,
        price=current_price,
        instrument=instrument,
    )
    future = (
        _event(
            identity="future-quote-s201",
            minute=11,
            price=999,
            instrument=instrument,
            event_type="quote",
        )
        if future_event is None
        else future_event
    )
    events = [*(prior_events or []), current, future]
    engine = MarketDataReplayEngine(replay_id=replay_id, events=events)
    engine.start()
    while engine.cursor.last_event_id != current.event_id:
        engine.next_event()
    return _calendar(), _session(), engine, current


def _signal(
    *,
    target: str = "10",
    current_price: object = 100,
    prior_events: list[MarketDataEvent] | None = None,
    future_event: MarketDataEvent | None = None,
    replay_id: str = "replay-s201",
) -> tuple[
    StrategySignal,
    TradingCalendar,
    TradingSession,
    MarketDataReplayEngine,
]:
    calendar, session, engine, current = _market_authority(
        current_price=current_price,
        prior_events=prior_events,
        future_event=future_event,
        replay_id=replay_id,
    )
    configured_target = "10" if target == "0" else target
    runtime = create_moving_average_crossover_runtime_reference(
        fast_window=2,
        slow_window=3,
        target_position_quantity=PaperQuantity.parse(configured_target),
    )
    market = create_strategy_signal_market_reference(
        calendar=calendar,
        session=session,
        replay_session=engine.session,
        current_event=current,
    )
    command = create_evaluate_strategy_signal_command(
        strategy_runtime_reference=runtime,
        market_reference=market,
        command_idempotency_key="evaluate-s201",
        actor="founder",
    )
    signal = _create_strategy_signal_from_evaluation(
        command=command,
        target_position_quantity=PaperQuantity.parse(target),
        created_at=CREATED,
    )
    return signal, calendar, session, engine


def _state(
    *,
    quantity: str = "4",
    cash: str = "1000",
    account_id: str = "account-s201",
) -> tuple[PaperAccountLedgerState, list[object]]:
    identity = PaperAccountIdentity(
        account_id=account_id,
        display_name="Sprint 201 Account",
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
    creation = create_paper_account_event_bundle(
        command,
        event_id=f"{account_id}-event-001",
        cash_entry_id=f"{account_id}-cash-001",
        recorded_timestamp_utc=CREATED,
    )
    history: list[object] = [creation]
    state = replay_paper_account_ledger(history)
    if PaperQuantity.parse(quantity).decimal_value != 0:
        position_command = create_post_paper_position_adjustment_command(
            account_id=account_id,
            expected_account_version=state.head_version,
            command_idempotency_key=f"position-{account_id}",
            actor="founder",
            reason="Replay-derived risk fixture",
            symbol=INSTRUMENT,
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
            reason="Advance exact account head",
            movement_type="deposit",
            requested_amount=PaperMoney.parse("1"),
        ),
        event_id=f"cash-event-{version}",
        cash_entry_id=f"cash-entry-{version}",
        recorded_timestamp_utc=CREATED + timedelta(minutes=version),
    )
    return replay_paper_account_ledger([*history, bundle])


def _intent(
    *,
    target: str = "10",
    quantity: str = "4",
    cash: str = "1000",
    current_price: object = 100,
    prior_events: list[MarketDataEvent] | None = None,
    future_event: MarketDataEvent | None = None,
) -> tuple[
    OrderIntent | OrderIntentNoAction,
    PaperAccountLedgerState,
    list[object],
    TradingCalendar,
    TradingSession,
    MarketDataReplayEngine,
]:
    signal, calendar, session, engine = _signal(
        target=target,
        current_price=current_price,
        prior_events=prior_events,
        future_event=future_event,
    )
    state, history = _state(quantity=quantity, cash=cash)
    command = create_derive_order_intent_command(
        signal=signal,
        account_state=state,
        command_idempotency_key="derive-s201",
        actor="founder",
    )
    result = derive_order_intent(
        command,
        signal=signal,
        account_state=state,
        created_at=CREATED,
    )
    return result, state, history, calendar, session, engine


def _decision(
    *,
    target: str = "10",
    quantity: str = "4",
    cash: str = "1000",
    current_price: object = 100,
    maximum_quantity: str | None = None,
    maximum_notional: str | None = None,
    key: str = "risk-s201",
    actor: str = "founder",
    created_at: datetime = CREATED,
    prior_events: list[MarketDataEvent] | None = None,
) -> tuple[
    PreTradeRiskDecision,
    EvaluatePreTradeRiskCommand,
    OrderIntent,
    PaperAccountLedgerState,
    list[object],
    TradingCalendar,
    TradingSession,
    MarketDataReplayEngine,
]:
    result, state, history, calendar, session, engine = _intent(
        target=target,
        quantity=quantity,
        cash=cash,
        current_price=current_price,
        prior_events=prior_events,
    )
    assert isinstance(result, OrderIntent)
    policy = create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=(
            None
            if maximum_quantity is None
            else PaperQuantity.parse(maximum_quantity)
        ),
        maximum_order_notional=(
            None
            if maximum_notional is None
            else PaperMoney.parse(maximum_notional)
        ),
    )
    command = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=policy,
        command_idempotency_key=key,
        actor=actor,
    )
    decision = evaluate_pre_trade_risk(
        command,
        intent=result,
        account_state=state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=created_at,
    )
    return (
        decision,
        command,
        result,
        state,
        history,
        calendar,
        session,
        engine,
    )


def test_policy_references_are_exact_versioned_and_digestible() -> None:
    no_limits = create_long_only_cash_risk_policy_reference()
    bounded = create_long_only_cash_risk_policy_reference(
        maximum_order_quantity=PaperQuantity.parse("6.5"),
        maximum_order_notional=PaperMoney.parse("650.25"),
    )
    assert no_limits.to_dict() == {
        "schema_version": 1,
        "policy_id": LONG_ONLY_CASH_RISK_POLICY_ID,
        "reference_price_policy_id": LATEST_TRADE_PRICE_POLICY_ID,
        "maximum_order_quantity": None,
        "maximum_order_notional": None,
        "configuration_digest": _digest(
            {
                "maximum_order_quantity": None,
                "maximum_order_notional": None,
            }
        ),
        "reference_digest": no_limits.reference_digest,
    }
    assert bounded.maximum_order_quantity == PaperQuantity.parse("6.5")
    assert bounded.maximum_order_notional == PaperMoney.parse("650.25")
    assert validate_pre_trade_risk_policy_reference(bounded) is bounded
    assert bounded.reference_digest == _digest(
        {
            key: value
            for key, value in bounded.to_dict().items()
            if key != "reference_digest"
        }
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maximum_order_quantity", PaperQuantity.parse("0")),
        ("maximum_order_quantity", PaperQuantity.parse("-1")),
        ("maximum_order_quantity", 1.0),
        ("maximum_order_quantity", "1"),
        ("maximum_order_quantity", True),
        ("maximum_order_notional", PaperMoney.parse("0")),
        ("maximum_order_notional", PaperMoney.parse("-1")),
        ("maximum_order_notional", 1),
        ("maximum_order_notional", "1"),
        ("maximum_order_notional", False),
    ],
)
def test_policy_limits_reject_non_exact_or_non_positive_values(
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        create_long_only_cash_risk_policy_reference(**{field: value})


def test_policy_tampering_and_unsupported_versions_fail_closed() -> None:
    policy = create_long_only_cash_risk_policy_reference()
    object.__setattr__(policy, "policy_id", "other")
    with pytest.raises(ValueError):
        validate_pre_trade_risk_policy_reference(policy)
    with pytest.raises(ValueError):
        create_long_only_cash_risk_policy_reference(schema_version=2)


def test_risk_command_is_normalized_exact_and_digest_sensitive() -> None:
    result, *_ = _intent()
    assert isinstance(result, OrderIntent)
    policy = create_long_only_cash_risk_policy_reference()
    command = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=policy,
        command_idempotency_key="  risk-key  ",
        actor="  founder  ",
    )
    assert command.command_idempotency_key == "risk-key"
    assert command.actor == "founder"
    assert command.to_dict()["intent_reference"] == {
        "schema_version": 1,
        "intent_id": result.intent_id,
        "intent_digest": result.intent_digest,
    }
    assert command.command_digest == _digest(
        {
            key: value
            for key, value in command.to_dict().items()
            if key != "command_digest"
        }
    )
    changed_key = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=policy,
        command_idempotency_key="other",
        actor="founder",
    )
    changed_policy = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(
            maximum_order_quantity=PaperQuantity.parse("5")
        ),
        command_idempotency_key="risk-key",
        actor="founder",
    )
    assert len(
        {
            command.command_digest,
            changed_key.command_digest,
            changed_policy.command_digest,
        }
    ) == 3
    assert validate_evaluate_pre_trade_risk_command(command) is command


def test_risk_command_accepts_only_complete_m33_intent() -> None:
    no_action, *_ = _intent(target="4", quantity="4")
    assert isinstance(no_action, OrderIntentNoAction)
    policy = create_long_only_cash_risk_policy_reference()
    with pytest.raises(ValueError):
        create_evaluate_pre_trade_risk_command(
            intent=cast(OrderIntent, no_action),
            risk_policy_reference=policy,
            command_idempotency_key="risk",
            actor="founder",
        )
    with pytest.raises(ValueError):
        create_evaluate_pre_trade_risk_command(
            intent=cast(OrderIntent, object()),
            risk_policy_reference=policy,
            command_idempotency_key="risk",
            actor="founder",
        )
    assert BacktestOrderIntent is not OrderIntent


def test_sufficient_cash_buy_allows_with_complete_ordered_rules() -> None:
    decision, *_ = _decision()
    assert decision.outcome == PRE_TRADE_RISK_OUTCOME_ALLOW
    assert decision.reason_codes == ()
    snapshot = decision.input_snapshot
    assert snapshot.requested_quantity == PaperQuantity.parse("6")
    assert snapshot.price_reference.reference_price == PaperMoney.parse("100")
    assert snapshot.estimated_order_notional == PaperMoney.parse("600")
    assert tuple(rule.rule_code for rule in snapshot.rule_evidence) == (
        PRE_TRADE_RISK_RULE_ORDER
    )
    assert [rule.applicable for rule in snapshot.rule_evidence] == [
        False,
        False,
        False,
        True,
    ]
    assert all(rule.passed for rule in snapshot.rule_evidence)
    assert snapshot.rule_evidence[0].observed_value is None
    assert snapshot.rule_evidence[0].threshold_value is None


def test_insufficient_cash_buy_rejects_canonically() -> None:
    decision, *_ = _decision(cash="599.99999999")
    assert decision.outcome == PRE_TRADE_RISK_OUTCOME_REJECT
    assert decision.reason_codes == (
        PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
    )
    cash_rule = decision.input_snapshot.rule_evidence[-1]
    assert cash_rule.observed_value == PaperMoney.parse("599.99999999")
    assert cash_rule.threshold_value == PaperMoney.parse("600")
    assert not cash_rule.passed


def test_valid_sell_has_explicit_position_rule_and_no_cash_rule() -> None:
    decision, *_ = _decision(target="2", quantity="4", cash="0")
    assert decision.outcome == PRE_TRADE_RISK_OUTCOME_ALLOW
    position_rule = decision.input_snapshot.rule_evidence[0]
    cash_rule = decision.input_snapshot.rule_evidence[-1]
    assert position_rule.applicable
    assert position_rule.observed_value == PaperQuantity.parse("4")
    assert position_rule.threshold_value == PaperQuantity.parse("2")
    assert position_rule.passed
    assert not cash_rule.applicable
    assert cash_rule.observed_value is None


def test_quantity_notional_and_cash_failures_are_complete_and_ordered() -> None:
    decision, *_ = _decision(
        cash="100",
        maximum_quantity="5",
        maximum_notional="500",
    )
    assert decision.outcome == PRE_TRADE_RISK_OUTCOME_REJECT
    assert decision.reason_codes == (
        PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
        PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL,
        PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
    )


def test_exact_policy_and_cash_boundaries_pass() -> None:
    decision, *_ = _decision(
        cash="600",
        maximum_quantity="6",
        maximum_notional="600",
    )
    assert decision.outcome == PRE_TRADE_RISK_OUTCOME_ALLOW
    assert all(rule.passed for rule in decision.input_snapshot.rule_evidence)


def test_latest_consumed_same_instrument_trade_is_exact_price_evidence() -> None:
    prior = [
        _event(identity="older-trade", minute=1, price=90),
        _event(
            identity="other-instrument",
            minute=2,
            price=999,
            instrument="XNYS:MSFT",
        ),
        _event(
            identity="same-quote",
            minute=3,
            price=888,
            event_type="quote",
        ),
    ]
    decision, *_ = _decision(current_price=101.25, prior_events=prior)
    reference = decision.input_snapshot.price_reference
    assert reference.price_event_id == "signal-event-s201"
    assert reference.price_event_position == 4
    assert reference.cursor_position == 4
    assert reference.reference_price == PaperMoney.parse("101.25")
    event = next(
        item for item in decision.input_snapshot.price_reference.to_dict().items()
        if item[0] == "price_event_digest"
    )
    assert event[1] == _digest(
        _event(identity="signal-event-s201", minute=10, price=101.25).to_dict()
    )


def test_future_unconsumed_event_is_never_used_as_price() -> None:
    decision, *_, engine = _decision(current_price=100)
    reference = decision.input_snapshot.price_reference
    assert engine.events[-1].payload["price"] == 999
    assert engine.cursor.position < len(engine.events)
    assert reference.reference_price == PaperMoney.parse("100")


@pytest.mark.parametrize(
    "price",
    [
        _MISSING,
        True,
        "100",
        None,
        0,
        -1,
        1.234567891,
        10**18,
    ],
)
def test_invalid_latest_matching_trade_price_fails_without_decision(
    price: object,
) -> None:
    result, state, _, calendar, session, engine = _intent(
        current_price=price
    )
    assert isinstance(result, OrderIntent)
    command = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        command_idempotency_key="risk-invalid-price",
        actor="founder",
    )
    with pytest.raises(ValueError):
        evaluate_pre_trade_risk(
            command,
            intent=result,
            account_state=state,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )


def test_invalid_latest_trade_is_not_skipped_for_older_valid_trade() -> None:
    older = [_event(identity="older-valid", minute=1, price=100)]
    result, state, _, calendar, session, engine = _intent(
        current_price="invalid",
        prior_events=older,
    )
    assert isinstance(result, OrderIntent)
    command = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        command_idempotency_key="risk-invalid-latest",
        actor="founder",
    )
    with pytest.raises(ValueError):
        evaluate_pre_trade_risk(
            command,
            intent=result,
            account_state=state,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )


def test_unrepresentable_exact_notional_fails_closed() -> None:
    result, state, _, calendar, session, engine = _intent(
        target="999999999999999999",
        quantity="0",
        current_price=999999999999999999,
    )
    assert isinstance(result, OrderIntent)
    command = create_evaluate_pre_trade_risk_command(
        intent=result,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(),
        command_idempotency_key="risk-overflow",
        actor="founder",
    )
    with pytest.raises(ValueError, match="notional"):
        evaluate_pre_trade_risk(
            command,
            intent=result,
            account_state=state,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )


def test_changed_account_head_is_stale_even_if_position_is_unchanged() -> None:
    (
        _,
        command,
        intent,
        state,
        history,
        calendar,
        session,
        engine,
    ) = _decision()
    advanced = _advance_cash(state, history)
    before = (intent.to_dict(), engine.cursor.to_dict())
    with pytest.raises(ValueError, match="account authority"):
        evaluate_pre_trade_risk(
            command,
            intent=intent,
            account_state=advanced,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )
    assert before == (intent.to_dict(), engine.cursor.to_dict())


def test_replay_advance_calendar_and_session_changes_are_stale() -> None:
    (
        _,
        command,
        intent,
        state,
        _,
        calendar,
        session,
        engine,
    ) = _decision()
    engine.next_event()
    with pytest.raises(ValueError, match="market authority"):
        evaluate_pre_trade_risk(
            command,
            intent=intent,
            account_state=state,
            calendar=calendar,
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )
    fresh = _decision()
    _, command, intent, state, _, _, session, engine = fresh
    with pytest.raises(ValueError, match="market authority"):
        evaluate_pre_trade_risk(
            command,
            intent=intent,
            account_state=state,
            calendar=_calendar(version=2),
            session=session,
            replay_engine=engine,
            created_at=CREATED,
        )
    with pytest.raises(ValueError, match="market authority"):
        evaluate_pre_trade_risk(
            command,
            intent=intent,
            account_state=state,
            calendar=_calendar(),
            session=_session(identity="xnys-2026-07-28-other"),
            replay_engine=engine,
            created_at=CREATED,
        )


def test_lifecycle_only_replay_pause_preserves_exact_decision_identity() -> None:
    (
        first,
        command,
        intent,
        state,
        _,
        calendar,
        session,
        engine,
    ) = _decision()
    cursor_before = engine.cursor
    engine.pause()
    second = evaluate_pre_trade_risk(
        command,
        intent=intent,
        account_state=state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED + timedelta(hours=1),
    )
    assert engine.cursor.position == cursor_before.position
    assert engine.cursor.event_stream_digest == cursor_before.event_stream_digest
    assert first.input_snapshot.snapshot_id == second.input_snapshot.snapshot_id
    assert first.decision_id == second.decision_id


def test_key_actor_and_audit_time_do_not_change_snapshot_or_decision_identity() -> None:
    (
        first,
        _,
        intent,
        state,
        _,
        calendar,
        session,
        engine,
    ) = _decision()
    policy = first.input_snapshot.risk_policy_reference
    command = create_evaluate_pre_trade_risk_command(
        intent=intent,
        risk_policy_reference=policy,
        command_idempotency_key="risk-other",
        actor="reviewer",
    )
    second = evaluate_pre_trade_risk(
        command,
        intent=intent,
        account_state=state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED + timedelta(days=1),
    )
    assert first.input_snapshot.snapshot_id == second.input_snapshot.snapshot_id
    assert first.decision_id == second.decision_id
    assert first.origin_command_digest != second.origin_command_digest
    assert first.created_at != second.created_at


def test_policy_changes_snapshot_and_decision_identity() -> None:
    first, *rest = _decision()
    _, intent, state, _, calendar, session, engine = rest
    command = create_evaluate_pre_trade_risk_command(
        intent=intent,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(
            maximum_order_quantity=PaperQuantity.parse("100")
        ),
        command_idempotency_key="risk-policy-change",
        actor="founder",
    )
    second = evaluate_pre_trade_risk(
        command,
        intent=intent,
        account_state=state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED,
    )
    assert first.input_snapshot.snapshot_id != second.input_snapshot.snapshot_id
    assert first.decision_id != second.decision_id


def test_snapshot_and_decision_digests_match_exact_canonical_payloads() -> None:
    decision, *_ = _decision()
    snapshot = decision.input_snapshot
    snapshot_payload = {
        key: value
        for key, value in snapshot.to_dict().items()
        if key not in {"snapshot_id", "snapshot_digest"}
    }
    assert snapshot.snapshot_digest == _digest(snapshot_payload)
    assert snapshot.snapshot_id == f"risk_input_{snapshot.snapshot_digest}"
    decision_payload = {
        "schema_version": decision.schema_version,
        "input_snapshot": snapshot.to_dict(),
        "outcome": decision.outcome,
        "reason_codes": list(decision.reason_codes),
    }
    assert decision.decision_digest == _digest(decision_payload)
    assert decision.decision_id == f"risk_decision_{decision.decision_digest}"


@pytest.mark.parametrize(
    ("target_name", "field_name", "replacement"),
    [
        ("decision", "outcome", PRE_TRADE_RISK_OUTCOME_REJECT),
        ("decision", "reason_codes", (PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,)),
        ("decision", "origin_actor", "tampered"),
        ("decision", "origin_command_digest", "0" * 64),
        ("snapshot", "side", "hold"),
        ("snapshot", "snapshot_digest", "0" * 64),
        ("price", "reference_price", PaperMoney.parse("101")),
        ("rule", "passed", False),
    ],
)
def test_tampered_decision_snapshot_price_and_rules_fail_closed(
    target_name: str,
    field_name: str,
    replacement: object,
) -> None:
    decision, *_ = _decision()
    target: object
    if target_name == "decision":
        target = decision
    elif target_name == "snapshot":
        target = decision.input_snapshot
    elif target_name == "price":
        target = decision.input_snapshot.price_reference
    else:
        target = decision.input_snapshot.rule_evidence[-1]
    object.__setattr__(target, field_name, replacement)
    with pytest.raises(ValueError):
        validate_pre_trade_risk_decision(decision)


def test_public_validators_accept_complete_immutable_evidence() -> None:
    decision, command, *_ = _decision()
    snapshot = decision.input_snapshot
    assert validate_evaluate_pre_trade_risk_command(command) is command
    assert validate_pre_trade_risk_price_reference(snapshot.price_reference) is (
        snapshot.price_reference
    )
    for rule in snapshot.rule_evidence:
        assert validate_pre_trade_risk_rule_evidence(rule) is rule
    assert validate_pre_trade_risk_input_snapshot(snapshot) is snapshot
    assert validate_pre_trade_risk_decision(decision) is decision
    with pytest.raises(FrozenInstanceError):
        decision.outcome = PRE_TRADE_RISK_OUTCOME_REJECT  # type: ignore[misc]


def test_direct_public_construction_is_blocked() -> None:
    for contract in (
        PreTradeRiskPolicyReference,
        EvaluatePreTradeRiskCommand,
        PreTradeRiskPriceReference,
        PreTradeRiskRuleEvidence,
        PreTradeRiskInputSnapshot,
        PreTradeRiskDecision,
    ):
        with pytest.raises(TypeError):
            contract()  # type: ignore[call-arg]


def test_exports_are_strict_json_primitives_stable_and_isolated() -> None:
    decision, command, *_ = _decision()
    exports = [
        command.risk_policy_reference.to_dict(),
        command.to_dict(),
        decision.input_snapshot.price_reference.to_dict(),
        *[
            rule.to_dict()
            for rule in decision.input_snapshot.rule_evidence
        ],
        decision.input_snapshot.to_dict(),
        decision.to_dict(),
    ]
    for exported in exports:
        serialized = json.dumps(
            exported,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert serialized == json.dumps(
            exported,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        assert not any(
            isinstance(value, tuple)
            for value in _walk_values(exported)
        )
    mutated = decision.to_dict()
    cast(dict[str, object], mutated["input_snapshot"])["outcome"] = "other"
    assert decision.to_dict() != mutated


def _walk_values(value: object) -> list[object]:
    values = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))
    return values


def test_evaluation_does_not_mutate_intent_account_or_replay() -> None:
    (
        _,
        command,
        intent,
        state,
        _,
        calendar,
        session,
        engine,
    ) = _decision()
    before = (
        copy.deepcopy(intent.to_dict()),
        copy.deepcopy(state.to_dict()),
        copy.deepcopy(engine.cursor.to_dict()),
        tuple(event.to_dict() for event in engine.events),
    )
    evaluate_pre_trade_risk(
        command,
        intent=intent,
        account_state=state,
        calendar=calendar,
        session=session,
        replay_engine=engine,
        created_at=CREATED,
    )
    after = (
        intent.to_dict(),
        state.to_dict(),
        engine.cursor.to_dict(),
        tuple(event.to_dict() for event in engine.events),
    )
    assert before == after
    assert not hasattr(intent, "set_risk_status")
    assert not hasattr(intent, "execute")


def test_s201_modules_remain_pure_and_scope_bounded() -> None:
    modules = (
        inspect.getmodule(PreTradeRiskPolicyReference),
        inspect.getmodule(EvaluatePreTradeRiskCommand),
        inspect.getmodule(PreTradeRiskInputSnapshot),
        inspect.getmodule(PreTradeRiskDecision),
    )
    forbidden = (
        "sqlalchemy",
        "alembic",
        "fastapi",
        "persistence",
        "application",
        "docker",
        "broker",
        "qmt",
        "requests",
        "httpx",
    )
    for module in modules:
        assert module is not None
        source = inspect.getsource(module).lower()
        assert all(token not in source for token in forbidden)


def test_s201_closed_vocabulary_and_schema_versions_are_exact() -> None:
    assert (
        PRE_TRADE_RISK_POLICY_SCHEMA_VERSION,
        PRE_TRADE_RISK_PRICE_REFERENCE_SCHEMA_VERSION,
        EVALUATE_PRE_TRADE_RISK_COMMAND_SCHEMA_VERSION,
        PRE_TRADE_RISK_RULE_EVIDENCE_SCHEMA_VERSION,
        PRE_TRADE_RISK_INPUT_SNAPSHOT_SCHEMA_VERSION,
        PRE_TRADE_RISK_DECISION_SCHEMA_VERSION,
    ) == (1, 1, 1, 1, 1, 1)
    assert PRE_TRADE_RISK_RULE_ORDER == (
        PRE_TRADE_RISK_REASON_INSUFFICIENT_POSITION,
        PRE_TRADE_RISK_REASON_MAXIMUM_QUANTITY,
        PRE_TRADE_RISK_REASON_MAXIMUM_NOTIONAL,
        PRE_TRADE_RISK_REASON_INSUFFICIENT_CASH,
    )
