"""Immutable M31 ledger-state evidence bound to one Strategy Signal."""

from __future__ import annotations

from dataclasses import dataclass

from el_psy_quant.market_time import normalize_market_instrument_id
from el_psy_quant.paper_account import (
    MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
    MAX_PAPER_ACCOUNT_ID_LENGTH,
    PaperAccountLedgerState,
    PaperMoney,
    PaperQuantity,
    validate_paper_account_ledger_state,
)
from el_psy_quant.strategy_order._canonical import (
    canonical_digest,
    normalize_bounded_string,
    reject_public_construction,
    validate_digest,
)
from el_psy_quant.strategy_order.signals import (
    StrategySignal,
    validate_strategy_signal,
)

ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION = 1


def _exact_money(value: object, *, field_name: str) -> PaperMoney:
    if type(value) is not PaperMoney:
        raise ValueError(f"{field_name} must be PaperMoney")
    try:
        rebuilt = PaperMoney.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperMoney") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} must be a valid PaperMoney")
    return rebuilt


def _exact_quantity(value: object, *, field_name: str) -> PaperQuantity:
    if type(value) is not PaperQuantity:
        raise ValueError(f"{field_name} must be PaperQuantity")
    try:
        rebuilt = PaperQuantity.parse(value.canonical)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid PaperQuantity") from exc
    if (
        rebuilt != value
        or rebuilt.decimal_value.as_tuple()
        != value.decimal_value.as_tuple()
    ):
        raise ValueError(f"{field_name} must be a valid PaperQuantity")
    return rebuilt


def _payload_without_digest(
    *,
    schema_version: int,
    account_id: str,
    base_currency: str,
    lifecycle_status: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    cash_balance: PaperMoney,
    available_cash: PaperMoney,
    instrument_id: str,
    current_instrument_quantity: PaperQuantity,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "account_id": account_id,
        "base_currency": base_currency,
        "lifecycle_status": lifecycle_status,
        "account_head_version": account_head_version,
        "account_head_event_id": account_head_event_id,
        "account_head_chain_digest": account_head_chain_digest,
        "cash_balance": cash_balance.to_json_value(),
        "available_cash": available_cash.to_json_value(),
        "instrument_id": instrument_id,
        "current_instrument_quantity": (
            current_instrument_quantity.to_json_value()
        ),
    }


@dataclass(frozen=True, init=False)
class OrderIntentAccountReference:
    """Copied evidence from one exact validated M31 ledger-state head."""

    schema_version: int
    account_id: str
    base_currency: str
    lifecycle_status: str
    account_head_version: int
    account_head_event_id: str
    account_head_chain_digest: str
    cash_balance: PaperMoney
    available_cash: PaperMoney
    instrument_id: str
    current_instrument_quantity: PaperQuantity
    reference_digest: str

    __init__ = reject_public_construction

    def to_dict(self) -> dict[str, object]:
        """Return the complete strict-JSON account evidence snapshot."""
        return {
            **_payload_without_digest(
                schema_version=self.schema_version,
                account_id=self.account_id,
                base_currency=self.base_currency,
                lifecycle_status=self.lifecycle_status,
                account_head_version=self.account_head_version,
                account_head_event_id=self.account_head_event_id,
                account_head_chain_digest=self.account_head_chain_digest,
                cash_balance=self.cash_balance,
                available_cash=self.available_cash,
                instrument_id=self.instrument_id,
                current_instrument_quantity=(
                    self.current_instrument_quantity
                ),
            ),
            "reference_digest": self.reference_digest,
        }


def _build_account_reference(
    *,
    schema_version: int,
    account_id: str,
    base_currency: str,
    lifecycle_status: str,
    account_head_version: int,
    account_head_event_id: str,
    account_head_chain_digest: str,
    cash_balance: PaperMoney,
    available_cash: PaperMoney,
    instrument_id: str,
    current_instrument_quantity: PaperQuantity,
) -> OrderIntentAccountReference:
    payload = _payload_without_digest(
        schema_version=schema_version,
        account_id=account_id,
        base_currency=base_currency,
        lifecycle_status=lifecycle_status,
        account_head_version=account_head_version,
        account_head_event_id=account_head_event_id,
        account_head_chain_digest=account_head_chain_digest,
        cash_balance=cash_balance,
        available_cash=available_cash,
        instrument_id=instrument_id,
        current_instrument_quantity=current_instrument_quantity,
    )
    result = object.__new__(OrderIntentAccountReference)
    for field_name, value in (
        ("schema_version", schema_version),
        ("account_id", account_id),
        ("base_currency", base_currency),
        ("lifecycle_status", lifecycle_status),
        ("account_head_version", account_head_version),
        ("account_head_event_id", account_head_event_id),
        ("account_head_chain_digest", account_head_chain_digest),
        ("cash_balance", cash_balance),
        ("available_cash", available_cash),
        ("instrument_id", instrument_id),
        ("current_instrument_quantity", current_instrument_quantity),
        ("reference_digest", canonical_digest(payload)),
    ):
        object.__setattr__(result, field_name, value)
    return result


def create_order_intent_account_reference(
    *,
    signal: StrategySignal,
    account_state: PaperAccountLedgerState,
) -> OrderIntentAccountReference:
    """Bind a complete Signal to copied evidence from one active M31 state."""
    valid_signal = validate_strategy_signal(signal)
    return _create_order_intent_account_reference_from_instrument(
        instrument_id=valid_signal.market_reference.instrument_id,
        account_state=account_state,
    )


def _create_order_intent_account_reference_from_instrument(
    *,
    instrument_id: str,
    account_state: PaperAccountLedgerState,
) -> OrderIntentAccountReference:
    """Recreate exact account evidence for a previously validated instrument."""
    valid_state = validate_paper_account_ledger_state(account_state)
    if valid_state.lifecycle_status != "active":
        raise ValueError("order intent account state must be active")

    normalized_instrument = normalize_market_instrument_id(instrument_id)
    if normalized_instrument != instrument_id:
        raise ValueError("account-reference instrument_id is not normalized")
    positions = {
        position.symbol: position.quantity
        for position in valid_state.positions
    }
    quantity = positions.get(
        normalized_instrument,
        PaperQuantity.parse("0"),
    )
    return _build_account_reference(
        schema_version=ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION,
        account_id=valid_state.account_identity.account_id,
        base_currency=valid_state.account_identity.base_currency,
        lifecycle_status=valid_state.lifecycle_status,
        account_head_version=valid_state.head_version,
        account_head_event_id=valid_state.head_event_id,
        account_head_chain_digest=valid_state.head_chain_digest,
        cash_balance=PaperMoney.parse(valid_state.cash_balance.canonical),
        available_cash=PaperMoney.parse(valid_state.available_cash.canonical),
        instrument_id=normalized_instrument,
        current_instrument_quantity=PaperQuantity.parse(quantity.canonical),
    )


def validate_order_intent_account_reference(
    value: object,
) -> OrderIntentAccountReference:
    """Recompute and verify one complete immutable account reference."""
    if type(value) is not OrderIntentAccountReference:
        raise ValueError(
            "account_reference must be an OrderIntentAccountReference"
        )
    try:
        if (
            type(value.schema_version) is not int
            or value.schema_version
            != ORDER_INTENT_ACCOUNT_REFERENCE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported account-reference schema_version")
        if value.lifecycle_status != "active":
            raise ValueError("account reference lifecycle must be active")
        account_id = normalize_bounded_string(
            value.account_id,
            field_name="account_id",
            maximum_length=MAX_PAPER_ACCOUNT_ID_LENGTH,
        )
        if account_id != value.account_id:
            raise ValueError("account reference account_id is not normalized")
        if (
            not isinstance(value.base_currency, str)
            or len(value.base_currency) != 3
            or any(
                character < "A" or character > "Z"
                for character in value.base_currency
            )
        ):
            raise ValueError("account reference base_currency is invalid")
        if (
            type(value.account_head_version) is not int
            or value.account_head_version <= 0
        ):
            raise ValueError("account head version must be positive")
        event_id = normalize_bounded_string(
            value.account_head_event_id,
            field_name="account_head_event_id",
            maximum_length=MAX_PAPER_ACCOUNT_EVENT_ID_LENGTH,
        )
        if event_id != value.account_head_event_id:
            raise ValueError("account head event ID is not normalized")
        validate_digest(
            value.account_head_chain_digest,
            field_name="account_head_chain_digest",
        )
        instrument_id = normalize_market_instrument_id(value.instrument_id)
        if instrument_id != value.instrument_id:
            raise ValueError("account reference instrument_id is invalid")
        cash = _exact_money(value.cash_balance, field_name="cash_balance")
        available = _exact_money(
            value.available_cash,
            field_name="available_cash",
        )
        if cash.canonical != available.canonical:
            raise ValueError("available_cash must equal cash_balance")
        if cash.decimal_value < 0:
            raise ValueError("cash balance must be non-negative")
        current = _exact_quantity(
            value.current_instrument_quantity,
            field_name="current_instrument_quantity",
        )
        if current.decimal_value < 0:
            raise ValueError("current instrument quantity must be non-negative")
        rebuilt = _build_account_reference(
            schema_version=value.schema_version,
            account_id=value.account_id,
            base_currency=value.base_currency,
            lifecycle_status=value.lifecycle_status,
            account_head_version=value.account_head_version,
            account_head_event_id=value.account_head_event_id,
            account_head_chain_digest=value.account_head_chain_digest,
            cash_balance=cash,
            available_cash=available,
            instrument_id=value.instrument_id,
            current_instrument_quantity=current,
        )
        validate_digest(value.reference_digest, field_name="reference_digest")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("order intent account reference is invalid") from exc
    if rebuilt != value or rebuilt.to_dict() != value.to_dict():
        raise ValueError("order intent account reference is invalid")
    return value


def _clone_order_intent_account_reference(
    value: OrderIntentAccountReference,
) -> OrderIntentAccountReference:
    validate_order_intent_account_reference(value)
    return _build_account_reference(
        schema_version=value.schema_version,
        account_id=value.account_id,
        base_currency=value.base_currency,
        lifecycle_status=value.lifecycle_status,
        account_head_version=value.account_head_version,
        account_head_event_id=value.account_head_event_id,
        account_head_chain_digest=value.account_head_chain_digest,
        cash_balance=PaperMoney.parse(value.cash_balance.canonical),
        available_cash=PaperMoney.parse(value.available_cash.canonical),
        instrument_id=value.instrument_id,
        current_instrument_quantity=PaperQuantity.parse(
            value.current_instrument_quantity.canonical
        ),
    )
