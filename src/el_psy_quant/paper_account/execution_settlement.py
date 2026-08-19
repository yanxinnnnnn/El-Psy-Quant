"""Pure M31 posting semantics for one M34 execution Fill."""

from __future__ import annotations

from datetime import datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from el_psy_quant.paper_account._shared import (
    canonical_digest,
    money_from_decimal,
    normalize_utc_datetime,
    quantity_from_decimal,
    validate_digest,
)
from el_psy_quant.paper_account.cash_ledger import _create_cash_ledger_entry
from el_psy_quant.paper_account.decimals import PaperMoney, PaperQuantity
from el_psy_quant.paper_account.events import (
    _ExecutionFillPostedDetails,
    _create_event,
    _execution_fill_posted_details,
)
from el_psy_quant.paper_account.ledger_state import (
    PaperAccountLedgerEventBundle,
    PaperAccountLedgerState,
    PaperAccountPosition,
    _add_exact,
    _create_ledger_bundle,
    _create_ledger_state,
    _create_position,
    _validate_ledger_state,
)
from el_psy_quant.paper_account.position_commands import (
    _normalize_position_symbol,
)
from el_psy_quant.paper_account.position_ledger import (
    _create_position_ledger_entry,
)

PAPER_ACCOUNT_EXECUTION_SETTLEMENT_MONEY_QUANTUM = Decimal("0.00000001")
PAPER_ACCOUNT_EXECUTION_SETTLEMENT_ROUNDING_MODE = "ROUND_HALF_EVEN"

_SETTLEMENT_CONTEXT = Context(prec=100, rounding=ROUND_HALF_EVEN)


def _exact_money(
    value: object,
    *,
    field_name: str,
    non_negative: bool = False,
    positive: bool = False,
) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if rebuilt != value or (
        rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is not canonical")
    if non_negative and rebuilt.decimal_value < 0:
        raise ValueError(f"{field_name} must not be negative")
    if positive and rebuilt.decimal_value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return rebuilt


def _exact_quantity(
    value: object,
    *,
    field_name: str,
    positive: bool = False,
) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} is invalid") from exc
    if rebuilt != value or (
        rebuilt.decimal_value.as_tuple() != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} is not canonical")
    if positive and rebuilt.decimal_value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return rebuilt


def _validate_reference(
    reference_id: object,
    digest: object,
    *,
    prefix: str,
    field_name: str,
) -> tuple[str, str]:
    valid_digest = validate_digest(digest, f"{field_name}_digest")
    if not isinstance(reference_id, str) or reference_id != (f"{prefix}{valid_digest}"):
        raise ValueError(f"{field_name}_id does not match its digest")
    return reference_id, valid_digest


def _position_for(
    state: PaperAccountLedgerState,
    instrument_id: str,
) -> PaperAccountPosition | None:
    return next(
        (position for position in state.positions if position.symbol == instrument_id),
        None,
    )


def _sell_cost_basis_removed(
    *,
    current_position: PaperAccountPosition,
    fill_quantity: PaperQuantity,
) -> PaperMoney:
    if fill_quantity.decimal_value > current_position.quantity.decimal_value:
        raise ValueError("sell Fill exceeds current position quantity")
    if fill_quantity == current_position.quantity:
        return current_position.aggregate_cost_basis
    with localcontext(_SETTLEMENT_CONTEXT):
        removed = (
            current_position.aggregate_cost_basis.decimal_value
            * fill_quantity.decimal_value
            / current_position.quantity.decimal_value
        ).quantize(
            PAPER_ACCOUNT_EXECUTION_SETTLEMENT_MONEY_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
    return money_from_decimal(removed)


def _derive_effects(
    state: PaperAccountLedgerState,
    *,
    instrument_id: str,
    side: str,
    fill_quantity: PaperQuantity,
    gross_notional: PaperMoney,
    total_charges: PaperMoney,
) -> tuple[PaperMoney, PaperQuantity, PaperMoney]:
    quantity = _exact_quantity(
        fill_quantity,
        field_name="fill_quantity",
        positive=True,
    )
    gross = _exact_money(
        gross_notional,
        field_name="gross_notional",
        positive=True,
    )
    charges = _exact_money(
        total_charges,
        field_name="total_charges",
        non_negative=True,
    )
    if side == "buy":
        with localcontext(_SETTLEMENT_CONTEXT):
            total_debit = gross.decimal_value + charges.decimal_value
        return (
            money_from_decimal(-total_debit),
            quantity,
            money_from_decimal(total_debit),
        )
    if side != "sell":
        raise ValueError("execution settlement side must be buy or sell")
    position = _position_for(state, instrument_id)
    if position is None:
        raise ValueError("sell Fill requires a current position")
    removed = _sell_cost_basis_removed(
        current_position=position,
        fill_quantity=quantity,
    )
    with localcontext(_SETTLEMENT_CONTEXT):
        net_proceeds = gross.decimal_value - charges.decimal_value
    if net_proceeds < 0:
        raise ValueError("sell Fill net proceeds must not be negative")
    return (
        money_from_decimal(net_proceeds),
        quantity_from_decimal(-quantity.decimal_value),
        money_from_decimal(-removed.decimal_value),
    )


def _identity_payload(
    state: PaperAccountLedgerState,
    *,
    execution_order_id: str,
    execution_order_digest: str,
    execution_attempt_id: str,
    execution_attempt_digest: str,
    execution_fill_id: str,
    execution_fill_digest: str,
    instrument_id: str,
    side: str,
    fill_quantity: PaperQuantity,
    gross_notional: PaperMoney,
    total_charges: PaperMoney,
    effective_timestamp_utc: datetime,
) -> dict[str, object]:
    return {
        "settlement_type": "paper_execution_fill_settlement_v1",
        "account_id": state.account_identity.account_id,
        "previous_account_version": state.head_version,
        "previous_event_id": state.head_event_id,
        "previous_chain_digest": state.head_chain_digest,
        "execution_order_id": execution_order_id,
        "execution_order_digest": execution_order_digest,
        "execution_attempt_id": execution_attempt_id,
        "execution_attempt_digest": execution_attempt_digest,
        "execution_fill_id": execution_fill_id,
        "execution_fill_digest": execution_fill_digest,
        "instrument_id": instrument_id,
        "side": side,
        "fill_quantity": fill_quantity.to_json_value(),
        "gross_notional": gross_notional.to_json_value(),
        "total_charges": total_charges.to_json_value(),
        "effective_timestamp_utc": effective_timestamp_utc.isoformat(),
    }


def _resulting_state(
    state: PaperAccountLedgerState,
    *,
    instrument_id: str,
    signed_cash_delta: PaperMoney,
    signed_quantity_delta: PaperQuantity,
    signed_cost_basis_delta: PaperMoney,
    head_event_id: str,
    head_chain_digest: str,
) -> PaperAccountLedgerState:
    cash = money_from_decimal(
        _add_exact(
            state.cash_balance.decimal_value,
            signed_cash_delta.decimal_value,
        )
    )
    if cash.decimal_value < 0:
        raise ValueError("execution settlement would make cash negative")
    positions = {position.symbol: position for position in state.positions}
    prior = positions.get(instrument_id)
    prior_quantity = Decimal("0") if prior is None else prior.quantity.decimal_value
    prior_cost = (
        Decimal("0") if prior is None else prior.aggregate_cost_basis.decimal_value
    )
    quantity = quantity_from_decimal(
        _add_exact(prior_quantity, signed_quantity_delta.decimal_value)
    )
    cost = money_from_decimal(
        _add_exact(prior_cost, signed_cost_basis_delta.decimal_value)
    )
    if quantity.decimal_value < 0 or cost.decimal_value < 0:
        raise ValueError("execution settlement violates long-only position state")
    if quantity.decimal_value == 0 and cost.decimal_value != 0:
        raise ValueError("zero position quantity requires zero cost basis")
    if quantity.decimal_value == 0:
        positions.pop(instrument_id, None)
    else:
        positions[instrument_id] = _create_position(
            symbol=instrument_id,
            quantity=quantity,
            aggregate_cost_basis=cost,
        )
    return _create_ledger_state(
        account_identity=state.account_identity,
        lifecycle_status=state.lifecycle_status,
        cash_balance=cash,
        positions=tuple(positions[symbol] for symbol in sorted(positions)),
        approved_portfolio_reviews=state.approved_portfolio_reviews,
        head_version=state.head_version + 1,
        head_event_id=head_event_id,
        head_chain_digest=head_chain_digest,
    )


def _apply_paper_execution_fill_settlement(
    state: PaperAccountLedgerState,
    *,
    execution_order_id: str,
    execution_order_digest: str,
    execution_attempt_id: str,
    execution_attempt_digest: str,
    execution_fill_id: str,
    execution_fill_digest: str,
    instrument_id: str,
    side: str,
    fill_quantity: PaperQuantity,
    gross_notional: PaperMoney,
    total_charges: PaperMoney,
    effective_timestamp_utc: datetime,
    recorded_timestamp_utc: datetime,
) -> PaperAccountLedgerEventBundle:
    """Create one exact execution event with its cash and position postings."""
    current = _validate_ledger_state(state)
    if current.lifecycle_status != "active":
        raise ValueError("execution settlement requires an active account")
    order_id, order_digest = _validate_reference(
        execution_order_id,
        execution_order_digest,
        prefix="peo_",
        field_name="execution_order",
    )
    attempt_id, attempt_digest = _validate_reference(
        execution_attempt_id,
        execution_attempt_digest,
        prefix="pea_",
        field_name="execution_attempt",
    )
    fill_id, fill_digest = _validate_reference(
        execution_fill_id,
        execution_fill_digest,
        prefix="pef_",
        field_name="execution_fill",
    )
    symbol = _normalize_position_symbol(instrument_id)
    if symbol != instrument_id:
        raise ValueError("execution instrument_id must already be normalized")
    quantity = _exact_quantity(
        fill_quantity,
        field_name="fill_quantity",
        positive=True,
    )
    gross = _exact_money(
        gross_notional,
        field_name="gross_notional",
        positive=True,
    )
    charges = _exact_money(
        total_charges,
        field_name="total_charges",
        non_negative=True,
    )
    effective = normalize_utc_datetime(
        effective_timestamp_utc,
        field_name="effective_timestamp_utc",
    )
    recorded = normalize_utc_datetime(
        recorded_timestamp_utc,
        field_name="recorded_timestamp_utc",
    )
    cash_delta, quantity_delta, cost_delta = _derive_effects(
        current,
        instrument_id=symbol,
        side=side,
        fill_quantity=quantity,
        gross_notional=gross,
        total_charges=charges,
    )
    identity = _identity_payload(
        current,
        execution_order_id=order_id,
        execution_order_digest=order_digest,
        execution_attempt_id=attempt_id,
        execution_attempt_digest=attempt_digest,
        execution_fill_id=fill_id,
        execution_fill_digest=fill_digest,
        instrument_id=symbol,
        side=side,
        fill_quantity=quantity,
        gross_notional=gross,
        total_charges=charges,
        effective_timestamp_utc=effective,
    )
    identity_digest = canonical_digest(identity)
    event_id = f"pae_{identity_digest}"
    cash_entry_id = f"pce_{canonical_digest({**identity, 'posting': 'cash'})}"
    position_entry_id = f"ppe_{canonical_digest({**identity, 'posting': 'position'})}"
    cash_entry = _create_cash_ledger_entry(
        cash_entry_id=cash_entry_id,
        account_id=current.account_identity.account_id,
        event_id=event_id,
        movement_type="execution_settlement",
        currency=current.account_identity.base_currency,
        signed_amount=cash_delta,
    )
    position_entry = _create_position_ledger_entry(
        position_entry_id=position_entry_id,
        account_id=current.account_identity.account_id,
        event_id=event_id,
        symbol=symbol,
        signed_quantity_delta=quantity_delta,
        signed_cost_basis_delta=cost_delta,
        adjustment_category="execution_fill",
    )
    details = _execution_fill_posted_details(
        execution_order_id=order_id,
        execution_order_digest=order_digest,
        execution_attempt_id=attempt_id,
        execution_attempt_digest=attempt_digest,
        execution_fill_id=fill_id,
        execution_fill_digest=fill_digest,
        instrument_id=symbol,
        side=side,
        fill_quantity=quantity,
        gross_notional=gross,
        total_charges=charges,
        signed_cash_delta=cash_delta,
        signed_position_quantity_delta=quantity_delta,
        signed_position_cost_basis_delta=cost_delta,
    )
    event = _create_event(
        event_id=event_id,
        account_id=current.account_identity.account_id,
        sequence_number=current.head_version + 1,
        event_type="execution_fill_posted",
        command_idempotency_key=f"paper-execution-fill:{fill_id}",
        command_digest=identity_digest,
        expected_account_version=current.head_version,
        actor="paper_execution",
        reason=None,
        recorded_timestamp_utc=recorded,
        effective_timestamp_utc=effective,
        previous_chain_digest=current.head_chain_digest,
        details=details,
        cash_entries=(cash_entry,),
        position_entries=(position_entry,),
    )
    resulting = _resulting_state(
        current,
        instrument_id=symbol,
        signed_cash_delta=cash_delta,
        signed_quantity_delta=quantity_delta,
        signed_cost_basis_delta=cost_delta,
        head_event_id=event.event_id,
        head_chain_digest=event.chain_digest,
    )
    return _create_ledger_bundle(
        event=event,
        cash_entries=(cash_entry,),
        position_entries=(position_entry,),
        resulting_state=resulting,
    )


def validate_paper_execution_fill_settlement_bundle(
    state: PaperAccountLedgerState,
    bundle: PaperAccountLedgerEventBundle,
) -> PaperAccountLedgerEventBundle:
    """Validate one settlement bundle against its exact prior M31 head."""
    current = _validate_ledger_state(state)
    if type(bundle) is not PaperAccountLedgerEventBundle:
        raise ValueError("settlement bundle must be PaperAccountLedgerEventBundle")
    try:
        event = bundle.event
        if (
            event.event_type != "execution_fill_posted"
            or type(event.details) is not _ExecutionFillPostedDetails
            or len(bundle.cash_entries) != 1
            or len(bundle.position_entries) != 1
            or event.effective_timestamp_utc is None
        ):
            raise ValueError("execution settlement bundle shape is invalid")
        details = event.details
        expected = _apply_paper_execution_fill_settlement(
            current,
            execution_order_id=details.execution_order_id,
            execution_order_digest=details.execution_order_digest,
            execution_attempt_id=details.execution_attempt_id,
            execution_attempt_digest=details.execution_attempt_digest,
            execution_fill_id=details.execution_fill_id,
            execution_fill_digest=details.execution_fill_digest,
            instrument_id=details.instrument_id,
            side=details.side,
            fill_quantity=details.fill_quantity,
            gross_notional=details.gross_notional,
            total_charges=details.total_charges,
            effective_timestamp_utc=event.effective_timestamp_utc,
            recorded_timestamp_utc=event.recorded_timestamp_utc,
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("paper execution settlement bundle is invalid") from exc
    if expected != bundle or expected.to_dict() != bundle.to_dict():
        raise ValueError("paper execution settlement bundle is invalid")
    return bundle
