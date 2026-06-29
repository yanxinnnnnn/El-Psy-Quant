import pandas as pd
import pytest

from el_psy_quant.backtesting import (
    moving_average_crossover_multi_symbol,
    moving_average_crossover_pipeline,
)


def make_prices(values: list[float], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"Close": values}, index=pd.to_datetime(dates))


def test_runs_pipeline_per_normalized_symbol_in_input_order() -> None:
    aapl = make_prices([1.0, 2.0, 3.0], ["2024-01-01", "2024-01-02", "2024-01-03"])
    msft = make_prices(
        [3.0, 2.0, 1.0, 2.0],
        ["2024-02-01", "2024-02-02", "2024-02-03", "2024-02-04"],
    )

    result = moving_average_crossover_multi_symbol(
        {" msft ": msft, "aapl": aapl},
        fast_window=1,
        slow_window=2,
    )

    assert type(result) is dict
    assert list(result) == ["MSFT", "AAPL"]
    pd.testing.assert_frame_equal(
        result["MSFT"], moving_average_crossover_pipeline(msft["Close"], 1, 2)
    )
    pd.testing.assert_frame_equal(
        result["AAPL"], moving_average_crossover_pipeline(aapl["Close"], 1, 2)
    )


def test_passes_capital_cost_and_slippage_to_each_pipeline() -> None:
    prices = make_prices(
        [1.0, 2.0, 3.0, 2.0, 1.0, 2.0],
        [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-06",
        ],
    )

    result = moving_average_crossover_multi_symbol(
        {"AAPL": prices, "MSFT": prices.copy()},
        fast_window=1,
        slow_window=2,
        initial_capital=1_000.0,
        transaction_cost_rate=0.01,
        slippage_rate=0.005,
    )
    expected = moving_average_crossover_pipeline(
        prices["Close"], 1, 2, 1_000.0, 0.01, 0.005
    )

    for pipeline_result in result.values():
        pd.testing.assert_frame_equal(pipeline_result, expected)
        assert list(pipeline_result.columns) == list(expected.columns)


def test_rejects_empty_mapping() -> None:
    with pytest.raises(ValueError, match="prices_by_symbol must not be empty"):
        moving_average_crossover_multi_symbol({}, 1, 2)


@pytest.mark.parametrize(
    ("prices_by_symbol", "message"),
    [
        ({"  ": make_prices([1.0, 2.0], ["2024-01-01", "2024-01-02"])}, "symbol must not be empty"),
        (
            {
                "AAPL": make_prices([1.0, 2.0], ["2024-01-01", "2024-01-02"]),
                " aapl ": make_prices([2.0, 3.0], ["2024-01-01", "2024-01-02"]),
            },
            "duplicate symbol: AAPL",
        ),
    ],
)
def test_rejects_invalid_symbols(
    prices_by_symbol: dict[str, pd.DataFrame], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        moving_average_crossover_multi_symbol(prices_by_symbol, 1, 2)


def test_rejects_missing_close_column() -> None:
    with pytest.raises(ValueError, match="must contain a Close column"):
        moving_average_crossover_multi_symbol(
            {"AAPL": pd.DataFrame({"Open": [1.0, 2.0]})}, 1, 2
        )


def test_propagates_pipeline_validation_errors() -> None:
    prices = make_prices([1.0, 2.0], ["2024-01-01", "2024-01-02"])

    with pytest.raises(ValueError, match="fast_window must be less than slow_window"):
        moving_average_crossover_multi_symbol({"AAPL": prices}, 2, 2)


def test_multi_symbol_helper_is_exported() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.moving_average_crossover_multi_symbol
        is moving_average_crossover_multi_symbol
    )
