import json
from dataclasses import replace

import pandas as pd
import pytest

from el_psy_quant.execution import (
    AssumedFill,
    ExecutionAssumptions,
    summarize_assumed_fills,
)


def make_fill(
    *,
    intent_timestamp: str = "2026-01-02",
    fill_timestamp: str = "2026-01-03",
    symbol: str = "AAPL",
    side: str = "buy",
    quantity: float = 10.0,
    price: float = 100.0,
    price_field: str = "open",
    timing: str = "next_bar",
) -> AssumedFill:
    return AssumedFill(
        intent_timestamp=pd.Timestamp(intent_timestamp),
        fill_timestamp=pd.Timestamp(fill_timestamp),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        price_field=price_field,
        assumptions=ExecutionAssumptions(
            timing=timing,
            price_field=price_field,
            missing_price_policy="raise",
        ),
    )


def test_valid_fills_produce_expected_summary() -> None:
    fills = [
        make_fill(
            intent_timestamp="2026-01-02",
            fill_timestamp="2026-01-03",
            symbol="AAPL",
            side="buy",
            quantity=10.0,
            price=100.0,
            price_field="open",
            timing="next_bar",
        ),
        make_fill(
            intent_timestamp="2026-01-04",
            fill_timestamp="2026-01-04",
            symbol="MSFT",
            side="sell",
            quantity=4.0,
            price=200.0,
            price_field="close",
            timing="same_bar",
        ),
        make_fill(
            intent_timestamp="2026-01-01",
            fill_timestamp="2026-01-02",
            symbol="AAPL",
            side="buy",
            quantity=1.5,
            price=120.0,
            price_field="open",
            timing="next_bar",
        ),
    ]

    summary = summarize_assumed_fills(fills)

    assert summary == {
        "fill_count": 3,
        "symbols": ["AAPL", "MSFT"],
        "buy_count": 2,
        "sell_count": 1,
        "buy_quantity": 11.5,
        "sell_quantity": 4.0,
        "gross_quantity": 15.5,
        "buy_notional": 1180.0,
        "sell_notional": 800.0,
        "gross_notional": 1980.0,
        "price_fields": {"open": 2, "close": 1},
        "timings": {"next_bar": 2, "same_bar": 1},
        "first_intent_timestamp": "2026-01-01T00:00:00",
        "last_intent_timestamp": "2026-01-04T00:00:00",
        "first_fill_timestamp": "2026-01-02T00:00:00",
        "last_fill_timestamp": "2026-01-04T00:00:00",
    }


def test_symbol_price_field_and_timing_order_follow_first_appearance() -> None:
    fills = [
        make_fill(symbol="MSFT", price_field="close", timing="same_bar"),
        make_fill(symbol="AAPL", price_field="open", timing="next_bar"),
        make_fill(symbol="MSFT", price_field="close", timing="same_bar"),
    ]

    summary = summarize_assumed_fills(fills)

    assert summary["symbols"] == ["MSFT", "AAPL"]
    assert list(summary["price_fields"]) == ["close", "open"]
    assert list(summary["timings"]) == ["same_bar", "next_bar"]


def test_output_is_json_compatible() -> None:
    summary = summarize_assumed_fills([make_fill()])

    json.dumps(summary, allow_nan=False)


def test_empty_input_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        summarize_assumed_fills([])


@pytest.mark.parametrize("fills", [make_fill(), "bad", object()])
def test_invalid_input_type_raises_value_error(fills: object) -> None:
    with pytest.raises(ValueError, match="sequence of AssumedFill"):
        summarize_assumed_fills(fills)  # type: ignore[arg-type]


def test_invalid_fill_item_raises_value_error() -> None:
    with pytest.raises(ValueError, match="only AssumedFill"):
        summarize_assumed_fills([make_fill(), object()])  # type: ignore[list-item]


def test_invalid_side_raises_value_error() -> None:
    fill = replace(make_fill(), side="hold")

    with pytest.raises(ValueError, match="side"):
        summarize_assumed_fills([fill])


@pytest.mark.parametrize("quantity", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_quantity_raises_value_error(quantity: float) -> None:
    fill = replace(make_fill(), quantity=quantity)

    with pytest.raises(ValueError, match="quantity"):
        summarize_assumed_fills([fill])


@pytest.mark.parametrize("price", [float("nan"), float("inf"), float("-inf")])
def test_invalid_price_raises_value_error(price: float) -> None:
    fill = replace(make_fill(), price=price)

    with pytest.raises(ValueError, match="price"):
        summarize_assumed_fills([fill])


def test_package_exports_work() -> None:
    import el_psy_quant.execution as execution

    assert execution.summarize_assumed_fills is summarize_assumed_fills


def test_input_sequence_is_not_mutated() -> None:
    fills = [make_fill(), make_fill(symbol="MSFT", side="sell")]
    before = list(fills)

    summarize_assumed_fills(fills)

    assert fills == before
