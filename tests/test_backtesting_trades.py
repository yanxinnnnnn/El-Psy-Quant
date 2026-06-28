import pandas as pd
import pytest

from el_psy_quant.backtesting import (
    moving_average_crossover_pipeline,
    moving_average_crossover_trade_records,
)


def test_extracts_trade_rows_and_optional_pipeline_columns() -> None:
    result = moving_average_crossover_pipeline(
        pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0]),
        1,
        2,
        transaction_cost_rate=0.01,
        slippage_rate=0.005,
    )

    trades = moving_average_crossover_trade_records(result)

    assert not trades.empty
    assert list(trades.columns) == [
        "action",
        "position_before",
        "position_after",
        "close",
        "transaction_cost",
        "slippage",
        "net_strategy_return",
        "equity",
    ]
    assert trades.index.isin(result.index).all()


def test_returns_only_base_columns_when_optional_columns_are_absent() -> None:
    result = pd.DataFrame({"position": [0, 1], "close": [10.0, 11.0]})

    trades = moving_average_crossover_trade_records(result)

    assert list(trades.columns) == [
        "action",
        "position_before",
        "position_after",
        "close",
    ]


@pytest.mark.parametrize("missing", ["position", "close"])
def test_missing_required_column_raises_value_error(missing: str) -> None:
    result = pd.DataFrame({"position": [0], "close": [10.0]}).drop(
        columns=missing
    )

    with pytest.raises(ValueError, match=f"missing required columns: {missing}"):
        moving_average_crossover_trade_records(result)


def test_trade_helper_is_exported_from_backtesting() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.moving_average_crossover_trade_records
        is moving_average_crossover_trade_records
    )
