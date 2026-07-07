import json
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.execution import (
    ExecutionAssumptions,
    OrderIntent,
    default_execution_assumptions,
    validate_order_intent,
)


def test_valid_order_intent_can_be_created() -> None:
    assumptions = ExecutionAssumptions(
        timing="same_bar",
        price_field="close",
        missing_price_policy="raise",
    )

    intent = OrderIntent(
        timestamp=pd.Timestamp("2026-01-02 09:30:00"),
        symbol="AAPL",
        side="buy",
        quantity=10,
        assumptions=assumptions,
    )

    assert intent.timestamp == pd.Timestamp("2026-01-02 09:30:00")
    assert intent.symbol == "AAPL"
    assert intent.side == "buy"
    assert intent.quantity == 10.0
    assert intent.assumptions == assumptions


def test_timestamp_is_normalized_and_serialized_deterministically() -> None:
    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol="MSFT",
        side="sell",
        quantity=1.5,
    )

    assert intent.timestamp == pd.Timestamp("2026-01-02")
    assert intent.to_dict()["timestamp"] == "2026-01-02T00:00:00"


def test_symbol_and_side_are_normalized() -> None:
    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol=" msft ",
        side=" SELL ",
        quantity=2,
    )

    assert intent.symbol == "MSFT"
    assert intent.side == "sell"


def test_invalid_side_raises_value_error() -> None:
    with pytest.raises(ValueError, match="side"):
        validate_order_intent(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="hold",
            quantity=1,
        )


def test_invalid_symbol_raises_value_error() -> None:
    with pytest.raises(ValueError, match="symbol must not be empty"):
        validate_order_intent(
            timestamp="2026-01-02",
            symbol=" ",
            side="buy",
            quantity=1,
        )


@pytest.mark.parametrize(
    "quantity",
    [0, -1, float("nan"), float("inf"), "1"],
)
def test_invalid_quantity_raises_value_error(quantity: object) -> None:
    with pytest.raises(ValueError, match="quantity must be a positive number"):
        validate_order_intent(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=quantity,  # type: ignore[arg-type]
        )


def test_bool_quantity_raises_value_error() -> None:
    with pytest.raises(ValueError, match="quantity must be a positive number"):
        validate_order_intent(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=True,  # type: ignore[arg-type]
        )


def test_assumptions_are_included_in_dictionary_output() -> None:
    assumptions = ExecutionAssumptions(
        timing="same_bar",
        price_field="close",
        missing_price_policy="raise",
    )

    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol="AAPL",
        side="buy",
        quantity=1,
        assumptions=assumptions,
    )

    assert intent.to_dict()["assumptions"] == assumptions.to_dict()


def test_omitted_assumptions_use_default_execution_assumptions() -> None:
    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol="AAPL",
        side="buy",
        quantity=1,
    )

    assert intent.assumptions == default_execution_assumptions()


def test_invalid_assumptions_raise_value_error() -> None:
    with pytest.raises(ValueError, match="ExecutionAssumptions"):
        validate_order_intent(
            timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=1,
            assumptions={"timing": "next_bar"},  # type: ignore[arg-type]
        )


def test_dictionary_output_is_json_compatible() -> None:
    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol="AAPL",
        side="buy",
        quantity=1,
    )

    payload = intent.to_dict()

    assert payload == {
        "timestamp": "2026-01-02T00:00:00",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1.0,
        "assumptions": {
            "timing": "next_bar",
            "price_field": "open",
            "missing_price_policy": "raise",
        },
    }
    json.dumps(payload, allow_nan=False)


def test_order_intent_is_immutable() -> None:
    intent = validate_order_intent(
        timestamp="2026-01-02",
        symbol="AAPL",
        side="buy",
        quantity=1,
    )

    with pytest.raises(FrozenInstanceError):
        intent.side = "sell"  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.execution as execution

    assert execution.OrderIntent is OrderIntent
    assert execution.validate_order_intent is validate_order_intent
