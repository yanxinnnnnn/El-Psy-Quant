"""Focused deterministic Sprint 210 execution-settlement coverage."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

import el_psy_quant.paper_account as paper_account
from el_psy_quant.paper_account import (
    SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES,
    SUPPORTED_PAPER_CASH_LEDGER_MOVEMENT_TYPES,
    SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES,
    PaperAccountIdentity,
    PaperMoney,
    PaperQuantity,
    PostPaperCashMovementCommand,
    PostPaperPositionAdjustmentCommand,
    apply_paper_position_adjustment,
    create_paper_account_command,
    create_paper_account_event_bundle,
    create_post_paper_position_adjustment_command,
    replay_paper_account_ledger,
    validate_paper_execution_fill_settlement_bundle,
)
from el_psy_quant.paper_account.execution_settlement import (
    _apply_paper_execution_fill_settlement,
)
from el_psy_quant.paper_execution import (
    ExecutionSettlementLink,
    PaperExecutionSettlementResult,
    reconcile_paper_execution_settlement,
    settle_paper_execution_fill,
    validate_execution_settlement_link,
    validate_paper_execution_settlement_result,
)
from el_psy_quant.paper_execution.attempts import (
    _build_attempt,
    create_paper_execution_attempt_reference,
)
from el_psy_quant.paper_execution.costs import _build as _build_cost_evidence
from el_psy_quant.paper_execution.fills import _build_fill
from el_psy_quant.paper_execution.lifecycle import _build_state
from el_psy_quant.paper_execution.policies import PaperExecutionBasisPoints
from el_psy_quant.paper_execution.pricing import _build as _build_price_evidence
from el_psy_quant.strategy_order import (
    create_long_only_cash_risk_policy_reference,
)
from test_paper_execution_stepping import (  # type: ignore[import-not-found]
    CREATED,
    INSTRUMENT,
    _policy,
    _rebuild_risk,
    _scenario,
    _step,
)

UTC = timezone.utc
RECORDED = datetime(2026, 8, 18, 18, tzinfo=UTC)
ORDER_DIGEST = "1" * 64
ATTEMPT_DIGEST = "2" * 64
FILL_DIGEST = "3" * 64


def _ledger_history(
    *,
    cash: str = "1000",
    quantity: str = "0",
    cost_basis: str = "0",
):
    identity = PaperAccountIdentity(
        account_id="account-s210",
        display_name="Sprint 210 Account",
        base_currency="USD",
        created_by="founder",
        created_timestamp=CREATED,
    )
    command = create_paper_account_command(
        account_identity=identity,
        initial_cash=PaperMoney.parse(cash),
        command_idempotency_key="create-s210",
        actor="founder",
    )
    created = create_paper_account_event_bundle(
        command,
        event_id="account-s210-event-1",
        cash_entry_id="account-s210-cash-1",
        recorded_timestamp_utc=CREATED,
    )
    history = [created]
    state = replay_paper_account_ledger(history)
    if Decimal(quantity) > 0:
        position_command = create_post_paper_position_adjustment_command(
            account_id=identity.account_id,
            expected_account_version=state.head_version,
            command_idempotency_key="position-s210",
            actor="founder",
            reason="Opening position",
            symbol=INSTRUMENT,
            adjustment_category="opening_balance",
            signed_quantity_delta=PaperQuantity.parse(quantity),
            signed_cost_basis_delta=PaperMoney.parse(cost_basis),
        )
        position = apply_paper_position_adjustment(
            state,
            position_command,
            event_id="account-s210-event-2",
            position_entry_id="account-s210-position-2",
            recorded_timestamp_utc=CREATED + timedelta(minutes=1),
        )
        history.append(position)
        state = replay_paper_account_ledger(history)
    return history, state


def _m31_settlement(
    state,
    *,
    side: str = "buy",
    quantity: str = "2",
    gross: str = "200",
    charges: str = "5",
    recorded: datetime = RECORDED,
):
    return _apply_paper_execution_fill_settlement(
        state,
        execution_order_id=f"peo_{ORDER_DIGEST}",
        execution_order_digest=ORDER_DIGEST,
        execution_attempt_id=f"pea_{ATTEMPT_DIGEST}",
        execution_attempt_digest=ATTEMPT_DIGEST,
        execution_fill_id=f"pef_{FILL_DIGEST}",
        execution_fill_digest=FILL_DIGEST,
        instrument_id=INSTRUMENT,
        side=side,
        fill_quantity=PaperQuantity.parse(quantity),
        gross_notional=PaperMoney.parse(gross),
        total_charges=PaperMoney.parse(charges),
        effective_timestamp_utc=CREATED + timedelta(hours=6),
        recorded_timestamp_utc=recorded,
    )


def _rebuild_attempt_and_fill(
    step,
    *,
    prior_order_state=None,
    risk_revalidation=None,
):
    assert step.fill is not None
    prior = prior_order_state or step.attempt.prior_order_state
    risk = risk_revalidation or step.attempt.risk_revalidation
    assert risk is not None
    attempt = _build_attempt(
        execution_order_reference=step.attempt.execution_order_reference,
        prior_order_state=prior,
        pre_step_cursor=step.attempt.pre_step_cursor,
        post_step_cursor=step.attempt.post_step_cursor,
        consumed_event_reference=step.attempt.consumed_event_reference,
        attempt_result=step.attempt.attempt_result,
        no_fill_reason_code=step.attempt.no_fill_reason_code,
        terminal_reason_code=step.attempt.terminal_reason_code,
        risk_revalidation=risk,
        created_at=step.attempt.created_at,
    )
    fill = _build_fill(
        execution_order_reference=step.fill.execution_order_reference,
        attempt_reference=create_paper_execution_attempt_reference(attempt),
        execution_event_reference=step.fill.execution_event_reference,
        side=risk.execution_price_evidence.side,
        fill_quantity=risk.candidate_fill_quantity,
        execution_price_evidence=risk.execution_price_evidence,
        cost_evidence=risk.cost_evidence,
        created_at=step.fill.created_at,
    )
    return attempt, fill


def _settled_scenario(**scenario_changes):
    data = _scenario(**scenario_changes)
    step = _step(data, 0)
    assert step.fill is not None
    settlement = settle_paper_execution_fill(
        order=data["order"],
        attempt=step.attempt,
        fill=step.fill,
        account_state=data["state"],
        recorded_timestamp_utc=RECORDED,
    )
    return data, step, settlement


def test_additive_vocabulary_does_not_expand_generic_commands() -> None:
    assert "execution_fill_posted" in SUPPORTED_PAPER_ACCOUNT_EVENT_TYPES
    assert "execution_settlement" in SUPPORTED_PAPER_CASH_LEDGER_MOVEMENT_TYPES
    assert "execution_fill" in SUPPORTED_PAPER_POSITION_ADJUSTMENT_CATEGORIES
    with pytest.raises(ValueError, match="movement_type"):
        PostPaperCashMovementCommand(
            account_id="account-s210",
            expected_account_version=1,
            command_idempotency_key="manual-execution-cash",
            actor="founder",
            reason="not allowed",
            movement_type="execution_settlement",  # type: ignore[arg-type]
            requested_amount=PaperMoney.parse("1"),
        )
    with pytest.raises(ValueError, match="adjustment_category"):
        PostPaperPositionAdjustmentCommand(
            account_id="account-s210",
            expected_account_version=1,
            command_idempotency_key="manual-execution-position",
            actor="founder",
            reason="not allowed",
            symbol=INSTRUMENT,
            adjustment_category="execution_fill",
            signed_quantity_delta=PaperQuantity.parse("1"),
            signed_cost_basis_delta=PaperMoney.parse("1"),
        )


def test_public_m31_package_has_no_execution_settlement_constructor() -> None:
    assert not hasattr(
        paper_account,
        "apply_paper_execution_fill_settlement",
    )
    assert "apply_paper_execution_fill_settlement" not in paper_account.__all__


@pytest.mark.parametrize(
    ("charges", "cash_delta", "cost_delta"),
    [("0", "-200", "200"), ("5", "-205", "205")],
)
def test_buy_posts_one_cash_and_one_position_with_exact_math(
    charges: str,
    cash_delta: str,
    cost_delta: str,
) -> None:
    history, state = _ledger_history(quantity="1", cost_basis="50")
    bundle = _m31_settlement(state, charges=charges)
    assert bundle.event.event_type == "execution_fill_posted"
    assert len(bundle.cash_entries) == len(bundle.position_entries) == 1
    assert bundle.cash_entry is not None
    assert bundle.cash_entry.movement_type == "execution_settlement"
    assert bundle.cash_entry.signed_amount == PaperMoney.parse(cash_delta)
    assert bundle.position_entry is not None
    assert bundle.position_entry.adjustment_category == "execution_fill"
    assert bundle.position_entry.signed_quantity_delta == PaperQuantity.parse("2")
    assert bundle.position_entry.signed_cost_basis_delta == PaperMoney.parse(cost_delta)
    assert bundle.resulting_state.cash_balance == PaperMoney.parse(
        "800" if charges == "0" else "795"
    )
    position = bundle.resulting_state.positions[0]
    assert position.quantity == PaperQuantity.parse("3")
    assert position.aggregate_cost_basis == PaperMoney.parse(
        "250" if charges == "0" else "255"
    )
    assert replay_paper_account_ledger([*history, bundle]) == (bundle.resulting_state)


def test_buy_creates_a_new_position_and_fails_before_negative_cash() -> None:
    _, state = _ledger_history(cash="205")
    bundle = _m31_settlement(state)
    assert bundle.resulting_state.cash_balance == PaperMoney.parse("0")
    assert bundle.resulting_state.positions[0].quantity == PaperQuantity.parse("2")
    with pytest.raises(ValueError, match="cash negative"):
        _m31_settlement(_ledger_history(cash="204")[1])


def test_partial_sell_uses_average_cost_and_half_even_quantum() -> None:
    history, state = _ledger_history(
        cash="10",
        quantity="3",
        cost_basis="0.00000003",
    )
    bundle = _m31_settlement(
        state,
        side="sell",
        quantity="0.5",
        gross="10",
        charges="1",
    )
    assert bundle.cash_entry is not None
    assert bundle.cash_entry.signed_amount == PaperMoney.parse("9")
    assert bundle.position_entry is not None
    assert bundle.position_entry.signed_quantity_delta == PaperQuantity.parse("-0.5")
    # 0.00000003 * 0.5 / 3 == 0.000000005, the half-even tie rounds to 0.
    assert bundle.position_entry.signed_cost_basis_delta == PaperMoney.parse("0")
    assert bundle.resulting_state.positions[0].aggregate_cost_basis == (
        PaperMoney.parse("0.00000003")
    )
    assert replay_paper_account_ledger([*history, bundle]) == (bundle.resulting_state)


def test_full_sell_removes_exact_cost_basis_and_position() -> None:
    history, state = _ledger_history(
        cash="10",
        quantity="3",
        cost_basis="123.45678901",
    )
    bundle = _m31_settlement(
        state,
        side="sell",
        quantity="3",
        gross="300",
        charges="2",
    )
    assert bundle.cash_entry is not None
    assert bundle.cash_entry.signed_amount == PaperMoney.parse("298")
    assert bundle.position_entry is not None
    assert bundle.position_entry.signed_cost_basis_delta == PaperMoney.parse(
        "-123.45678901"
    )
    assert bundle.resulting_state.positions == ()
    assert replay_paper_account_ledger([*history, bundle]) == (bundle.resulting_state)


def test_sell_rejects_overdraw_and_negative_net_proceeds() -> None:
    _, state = _ledger_history(quantity="1", cost_basis="10")
    with pytest.raises(ValueError, match="exceeds"):
        _m31_settlement(state, side="sell", quantity="2")
    with pytest.raises(ValueError, match="net proceeds"):
        _m31_settlement(
            state,
            side="sell",
            quantity="1",
            gross="1",
            charges="2",
        )


@pytest.mark.parametrize("tamper", ["missing_cash", "extra_cash", "cash", "position"])
def test_m31_bundle_and_replay_fail_closed_under_posting_tamper(tamper: str) -> None:
    history, state = _ledger_history(quantity="1", cost_basis="50")
    bundle = copy.deepcopy(_m31_settlement(state))
    if tamper == "missing_cash":
        object.__setattr__(bundle, "cash_entries", ())
    elif tamper == "extra_cash":
        object.__setattr__(
            bundle,
            "cash_entries",
            (bundle.cash_entries[0], bundle.cash_entries[0]),
        )
    elif tamper == "cash":
        object.__setattr__(bundle.cash_entries[0], "movement_type", "deposit")
    else:
        object.__setattr__(
            bundle.position_entries[0],
            "adjustment_category",
            "manual_correction",
        )
    with pytest.raises(ValueError):
        validate_paper_execution_fill_settlement_bundle(state, bundle)
    with pytest.raises(ValueError):
        replay_paper_account_ledger([*history, bundle])


def test_event_digest_commits_both_posting_groups() -> None:
    _, state = _ledger_history()
    original = _m31_settlement(state)
    changed = copy.deepcopy(original)
    object.__setattr__(changed.position_entries[0], "entry_digest", "4" * 64)
    assert changed.event.event_digest == original.event.event_digest
    with pytest.raises(ValueError, match="invalid"):
        validate_paper_execution_fill_settlement_bundle(state, changed)


def test_m34_buy_settlement_reuses_fill_economics_and_event_time() -> None:
    data, step, result = _settled_scenario()
    assert step.fill is not None
    costs = step.fill.cost_evidence
    cash = result.ledger_bundle.cash_entries[0]
    position = result.ledger_bundle.position_entries[0]
    expected = -(costs.gross_notional.decimal_value + costs.total_charges.decimal_value)
    assert cash.signed_amount.decimal_value == expected
    assert position.signed_quantity_delta == step.fill.fill_quantity
    assert position.signed_cost_basis_delta.decimal_value == -expected
    assert result.ledger_bundle.event.effective_timestamp_utc == (
        step.fill.execution_event_reference.event_time
    )
    assert result.ledger_bundle.event.recorded_timestamp_utc == RECORDED
    assert data["state"].to_dict() == _scenario()["state"].to_dict()


def test_m34_capped_and_uncapped_sell_settlement() -> None:
    policy = _policy(max_fill_quantity_per_trade_event=PaperQuantity.parse("1"))
    _, partial_step, partial = _settled_scenario(
        target_quantity="1",
        current_quantity="4",
        execution_policy=policy,
    )
    assert partial_step.fill is not None
    assert partial.ledger_bundle.position_entries[0].signed_quantity_delta == (
        PaperQuantity.parse("-1")
    )
    _, full_step, full = _settled_scenario(
        target_quantity="1",
        current_quantity="4",
    )
    assert full_step.fill is not None
    assert full.ledger_bundle.position_entries[0].signed_quantity_delta == (
        PaperQuantity.parse("-3")
    )
    assert full.ledger_bundle.resulting_state.positions[0].quantity == (
        PaperQuantity.parse("1")
    )


def test_settlement_link_is_deterministic_one_to_one_and_audit_time_stable() -> None:
    data = _scenario()
    step = _step(data, 0)
    assert step.fill is not None
    first = settle_paper_execution_fill(
        order=data["order"],
        attempt=step.attempt,
        fill=step.fill,
        account_state=data["state"],
        recorded_timestamp_utc=RECORDED,
    )
    second = settle_paper_execution_fill(
        order=data["order"],
        attempt=step.attempt,
        fill=step.fill,
        account_state=data["state"],
        recorded_timestamp_utc=RECORDED + timedelta(hours=1),
    )
    assert first.settlement_link.settlement_link_id.startswith("pes_")
    assert first.settlement_link.settlement_link_id == (
        second.settlement_link.settlement_link_id
    )
    assert first.settlement_link.settlement_link_digest == (
        second.settlement_link.settlement_link_digest
    )
    assert first.settlement_link.settlement_link_evidence_digest != (
        second.settlement_link.settlement_link_evidence_digest
    )
    assert first.ledger_bundle.event.event_digest != (
        second.ledger_bundle.event.event_digest
    )
    assert validate_execution_settlement_link(first.settlement_link) == (
        first.settlement_link
    )
    assert (
        reconcile_paper_execution_settlement(
            account_state=data["state"],
            order=data["order"],
            attempt=step.attempt,
            fill=step.fill,
            result=first,
        )
        == first
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "account_event_id",
        "account_event_digest",
        "cash_entry_id",
        "position_entry_digest",
    ],
)
def test_wrong_link_event_posting_or_digest_fails_closed(field_name: str) -> None:
    data, step, result = _settled_scenario()
    changed = copy.deepcopy(result)
    link = changed.settlement_link
    object.__setattr__(
        link,
        field_name,
        "5" * 64 if "digest" in field_name else "wrong",
    )
    with pytest.raises(ValueError):
        validate_paper_execution_settlement_result(changed)
    with pytest.raises(ValueError):
        reconcile_paper_execution_settlement(
            account_state=data["state"],
            order=data["order"],
            attempt=step.attempt,
            fill=step.fill,
            result=changed,
        )


@pytest.mark.parametrize(
    "field_name",
    ["account_event_digest", "account_chain_digest"],
)
def test_standalone_link_validation_binds_event_and_chain_digests(
    field_name: str,
) -> None:
    _, _, result = _settled_scenario()
    link = copy.deepcopy(result.settlement_link)
    object.__setattr__(link, field_name, "a" * 64)
    with pytest.raises(ValueError, match="invalid"):
        validate_execution_settlement_link(link)


def test_stale_reapplication_and_account_anchors_fail_before_evidence() -> None:
    data, step, result = _settled_scenario()
    assert step.fill is not None
    with pytest.raises(ValueError, match="stale"):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=step.attempt,
            fill=step.fill,
            account_state=result.ledger_bundle.resulting_state,
            recorded_timestamp_utc=RECORDED + timedelta(minutes=1),
        )
    stale = copy.deepcopy(data["state"])
    object.__setattr__(stale, "available_cash", PaperMoney.parse("999"))
    with pytest.raises(ValueError):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=step.attempt,
            fill=step.fill,
            account_state=stale,
            recorded_timestamp_utc=RECORDED,
        )


def test_order_attempt_fill_mismatch_and_non_fill_attempt_fail_closed() -> None:
    data = _scenario()
    step = _step(data, 0)
    assert step.fill is not None
    other = _scenario(target_quantity="11")
    with pytest.raises(ValueError, match="incompatible"):
        settle_paper_execution_fill(
            order=other["order"],
            attempt=step.attempt,
            fill=step.fill,
            account_state=data["state"],
            recorded_timestamp_utc=RECORDED,
        )
    no_fill_data = _scenario(
        future_events=[
            {
                "instrument_id": "XNYS:MSFT",
                "event_type": "trade",
                "price": 101,
            }
        ]
    )
    no_fill = _step(no_fill_data, 0)
    with pytest.raises(ValueError):
        settle_paper_execution_fill(
            order=no_fill_data["order"],
            attempt=no_fill.attempt,
            fill=step.fill,
            account_state=no_fill_data["state"],
            recorded_timestamp_utc=RECORDED,
        )


@pytest.mark.parametrize(
    "corruption",
    ["prior_requested", "risk_requested", "risk_remaining"],
)
def test_settlement_rebinds_internally_valid_quantity_authority(
    corruption: str,
) -> None:
    data = _scenario()
    step = _step(data, 0)
    risk = step.attempt.risk_revalidation
    assert risk is not None
    prior = step.attempt.prior_order_state
    if corruption == "prior_requested":
        prior = _build_state(
            execution_order_reference=prior.execution_order_reference,
            execution_version=prior.execution_version,
            requested_quantity=PaperQuantity.parse("7"),
            cumulative_filled_quantity=PaperQuantity.parse("0"),
            terminal_rejected=False,
        )
    elif corruption == "risk_requested":
        risk = _rebuild_risk(
            risk,
            requested_quantity=PaperQuantity.parse("7"),
        )
    else:
        risk = _rebuild_risk(
            risk,
            remaining_quantity_before_step=PaperQuantity.parse("7"),
        )
    attempt, fill = _rebuild_attempt_and_fill(
        step,
        prior_order_state=prior,
        risk_revalidation=risk,
    )
    with pytest.raises(ValueError, match="Order/prior state"):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=attempt,
            fill=fill,
            account_state=data["state"],
            recorded_timestamp_utc=RECORDED,
        )


def test_settlement_rebinds_internally_valid_frozen_risk_policy() -> None:
    data = _scenario()
    step = _step(data, 0)
    risk = step.attempt.risk_revalidation
    assert risk is not None
    changed_risk = _rebuild_risk(
        risk,
        risk_policy_reference=create_long_only_cash_risk_policy_reference(
            maximum_order_quantity=PaperQuantity.parse("100"),
            maximum_order_notional=None,
        ),
    )
    attempt, fill = _rebuild_attempt_and_fill(
        step,
        risk_revalidation=changed_risk,
    )
    with pytest.raises(ValueError, match="frozen Order policy"):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=attempt,
            fill=fill,
            account_state=data["state"],
            recorded_timestamp_utc=RECORDED,
        )


def test_settlement_rebinds_internally_valid_execution_policy_evidence() -> None:
    data = _scenario()
    step = _step(data, 0)
    risk = step.attempt.risk_revalidation
    assert risk is not None
    original_price = risk.execution_price_evidence
    original_cost = risk.cost_evidence
    changed_price = _build_price_evidence(
        execution_event_reference=original_price.execution_event_reference,
        side=original_price.side,
        base_trade_price=original_price.base_trade_price,
        slippage_bps=PaperExecutionBasisPoints.parse("2"),
    )
    changed_cost = _build_cost_evidence(
        execution_price_evidence=changed_price,
        fill_quantity=risk.candidate_fill_quantity,
        commission_bps=original_cost.commission_bps,
        fee_bps=original_cost.fee_bps,
        side_tax_bps=original_cost.side_tax_bps,
    )
    changed_risk = _rebuild_risk(
        risk,
        execution_price_evidence=changed_price,
        cost_evidence=changed_cost,
    )
    attempt, fill = _rebuild_attempt_and_fill(
        step,
        risk_revalidation=changed_risk,
    )
    with pytest.raises(ValueError, match="frozen Order policy"):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=attempt,
            fill=fill,
            account_state=data["state"],
            recorded_timestamp_utc=RECORDED,
        )


def test_settlement_rebinds_internally_valid_per_event_fill_cap() -> None:
    policy = _policy(
        max_fill_quantity_per_trade_event=PaperQuantity.parse("2")
    )
    data = _scenario(execution_policy=policy)
    step = _step(data, 0)
    risk = step.attempt.risk_revalidation
    assert risk is not None
    changed_quantity = PaperQuantity.parse("1")
    changed_cost = _build_cost_evidence(
        execution_price_evidence=risk.execution_price_evidence,
        fill_quantity=changed_quantity,
        commission_bps=risk.cost_evidence.commission_bps,
        fee_bps=risk.cost_evidence.fee_bps,
        side_tax_bps=risk.cost_evidence.side_tax_bps,
    )
    changed_risk = _rebuild_risk(
        risk,
        cost_evidence=changed_cost,
        candidate_fill_quantity=changed_quantity,
    )
    attempt, fill = _rebuild_attempt_and_fill(
        step,
        risk_revalidation=changed_risk,
    )
    with pytest.raises(ValueError, match="per-event cap"):
        settle_paper_execution_fill(
            order=data["order"],
            attempt=attempt,
            fill=fill,
            account_state=data["state"],
            recorded_timestamp_utc=RECORDED,
        )


def test_recorded_timestamp_is_normalized_and_inputs_remain_immutable() -> None:
    data = _scenario()
    step = _step(data, 0)
    assert step.fill is not None
    before = tuple(
        json.dumps(value.to_dict(), sort_keys=True, allow_nan=False)
        for value in (data["order"], step.attempt, step.fill, data["state"])
    )
    local = datetime.fromisoformat("2026-08-19T02:00:00+08:00")
    result = settle_paper_execution_fill(
        order=data["order"],
        attempt=step.attempt,
        fill=step.fill,
        account_state=data["state"],
        recorded_timestamp_utc=local,
    )
    assert result.ledger_bundle.event.recorded_timestamp_utc == RECORDED
    after = tuple(
        json.dumps(value.to_dict(), sort_keys=True, allow_nan=False)
        for value in (data["order"], step.attempt, step.fill, data["state"])
    )
    assert before == after
    assert json.dumps(result.to_dict(), sort_keys=True, allow_nan=False)


def test_new_public_evidence_rejects_direct_construction() -> None:
    with pytest.raises(TypeError):
        ExecutionSettlementLink()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        PaperExecutionSettlementResult()  # type: ignore[call-arg]
