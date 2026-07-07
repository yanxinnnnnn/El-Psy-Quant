import json
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from el_psy_quant.execution import (
    AssumedFill,
    ExecutionAssumptions,
    OrderIntent,
    fill_order_intent,
)


def make_price_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [110.0, 111.0, 112.0],
            "Low": [90.0, 91.0, 92.0],
            "Close": [105.0, 106.0, 107.0],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-05"]),
    )


def make_intent(
    *,
    timestamp: object = "2026-01-03",
    timing: str = "same_bar",
    price_field: str = "open",
) -> OrderIntent:
    return OrderIntent(
        timestamp=timestamp,
        symbol=" aapl ",
        side=" BUY ",
        quantity=10,
        assumptions=ExecutionAssumptions(
            timing=timing,
            price_field=price_field,
            missing_price_policy="raise",
        ),
    )


def test_same_bar_uses_order_intent_timestamp_row() -> None:
    fill = fill_order_intent(make_intent(timing="same_bar"), make_price_data())

    assert fill.intent_timestamp == pd.Timestamp("2026-01-03")
    assert fill.fill_timestamp == pd.Timestamp("2026-01-03")
    assert fill.price == 101.0
    assert fill.symbol == "AAPL"
    assert fill.side == "buy"
    assert fill.quantity == 10.0


def test_next_bar_uses_first_row_strictly_after_order_intent_timestamp() -> None:
    fill = fill_order_intent(
        make_intent(timestamp="2026-01-02", timing="next_bar"),
        make_price_data(),
    )

    assert fill.fill_timestamp == pd.Timestamp("2026-01-03")
    assert fill.price == 101.0


@pytest.mark.parametrize(
    ("price_field", "expected_price"),
    [
        ("open", 101.0),
        ("high", 111.0),
        ("low", 91.0),
        ("close", 106.0),
    ],
)
def test_selected_price_field_is_used(
    price_field: str,
    expected_price: float,
) -> None:
    fill = fill_order_intent(
        make_intent(price_field=price_field),
        make_price_data(),
    )

    assert fill.price_field == price_field
    assert fill.price == expected_price


def test_missing_required_price_column_raises_value_error() -> None:
    price_data = make_price_data().drop(columns=["Open"])

    with pytest.raises(ValueError, match="missing required column: Open"):
        fill_order_intent(make_intent(price_field="open"), price_data)


def test_missing_fill_price_raises_value_error() -> None:
    price_data = make_price_data()
    price_data.loc[pd.Timestamp("2026-01-03"), "Open"] = float("nan")

    with pytest.raises(ValueError, match="fill price must not be missing"):
        fill_order_intent(make_intent(), price_data)


@pytest.mark.parametrize("bad_price", [float("inf"), float("-inf")])
def test_non_finite_fill_price_raises_value_error(bad_price: float) -> None:
    price_data = make_price_data()
    price_data.loc[pd.Timestamp("2026-01-03"), "Open"] = bad_price

    with pytest.raises(ValueError, match="fill price must be finite"):
        fill_order_intent(make_intent(), price_data)


def test_missing_next_bar_raises_value_error() -> None:
    with pytest.raises(ValueError, match="next_bar fill bar is unavailable"):
        fill_order_intent(
            make_intent(timestamp="2026-01-05", timing="next_bar"),
            make_price_data(),
        )


def test_missing_same_bar_raises_value_error() -> None:
    with pytest.raises(ValueError, match="same_bar fill bar is unavailable"):
        fill_order_intent(
            make_intent(timestamp="2026-01-04", timing="same_bar"),
            make_price_data(),
        )


def test_invalid_price_data_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="pandas DataFrame"):
        fill_order_intent(make_intent(), [])  # type: ignore[arg-type]


def test_empty_price_data_raises_value_error() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        fill_order_intent(make_intent(), pd.DataFrame())


def test_non_datetime_index_raises_value_error() -> None:
    price_data = make_price_data()
    price_data.index = [0, 1, 2]

    with pytest.raises(ValueError, match="DatetimeIndex"):
        fill_order_intent(make_intent(), price_data)


def test_non_numeric_price_column_raises_value_error() -> None:
    price_data = make_price_data()
    price_data["Open"] = ["bad", "bad", "bad"]

    with pytest.raises(ValueError, match="Open must contain numeric values"):
        fill_order_intent(make_intent(), price_data)


def test_invalid_order_intent_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="OrderIntent"):
        fill_order_intent(object(), make_price_data())  # type: ignore[arg-type]


def test_output_dictionary_is_json_compatible() -> None:
    fill = fill_order_intent(make_intent(price_field="close"), make_price_data())

    payload = fill.to_dict()

    assert payload == {
        "intent_timestamp": "2026-01-03T00:00:00",
        "fill_timestamp": "2026-01-03T00:00:00",
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10.0,
        "price": 106.0,
        "price_field": "close",
        "assumptions": {
            "timing": "same_bar",
            "price_field": "close",
            "missing_price_policy": "raise",
        },
    }
    json.dumps(payload, allow_nan=False)


def test_assumed_fill_is_immutable() -> None:
    fill = fill_order_intent(make_intent(), make_price_data())

    with pytest.raises(FrozenInstanceError):
        fill.price = 1.0  # type: ignore[misc]


def test_package_exports_work() -> None:
    import el_psy_quant.execution as execution

    assert execution.AssumedFill is AssumedFill
    assert execution.fill_order_intent is fill_order_intent


def test_input_price_data_is_not_mutated() -> None:
    price_data = make_price_data()
    before = price_data.copy(deep=True)

    fill_order_intent(make_intent(), price_data)

    pd.testing.assert_frame_equal(price_data, before)
