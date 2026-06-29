import pandas as pd
import pytest

from el_psy_quant.backtesting import (
    moving_average_crossover_multi_symbol,
    moving_average_crossover_pipeline,
    summarize_multi_symbol_results,
)
from el_psy_quant.performance import backtest_summary


def make_prices(values: list[float], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"Close": values}, index=pd.to_datetime(dates))


def make_result(values: list[float]) -> pd.DataFrame:
    equity = pd.Series(values)
    return pd.DataFrame(
        {
            "equity": equity,
            "strategy_return": equity.pct_change().fillna(0.0),
        }
    )


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


def test_summarizes_normalized_symbols_in_input_order() -> None:
    msft = make_result([1_000.0, 1_100.0, 1_045.0])
    aapl = make_result([1_000.0, 900.0, 990.0, 1_089.0])

    result = summarize_multi_symbol_results({" msft ": msft, "aapl": aapl})

    assert list(result.columns) == [
        "symbol",
        "initial_equity",
        "final_equity",
        "total_return",
        "max_drawdown",
        "periods",
    ]
    assert result["symbol"].tolist() == ["MSFT", "AAPL"]
    assert result.iloc[0].drop(labels="symbol").to_dict() == pytest.approx(
        backtest_summary(msft)
    )
    assert result.iloc[1].drop(labels="symbol").to_dict() == pytest.approx(
        backtest_summary(aapl)
    )


def test_summary_adds_annualized_metrics_when_frequency_is_provided() -> None:
    pipeline_result = make_result([1_000.0, 1_100.0, 1_045.0])

    result = summarize_multi_symbol_results(
        {"AAPL": pipeline_result},
        periods_per_year=252,
        annual_risk_free_rate=0.02,
    )
    expected = backtest_summary(pipeline_result, 252, 0.02)

    assert list(result.columns) == ["symbol", *expected]
    assert result.iloc[0].drop(labels="symbol").to_dict() == pytest.approx(expected)


def test_summary_omits_annualized_metrics_without_frequency() -> None:
    result = summarize_multi_symbol_results(
        {"AAPL": make_result([1_000.0, 1_100.0])}
    )

    assert "cagr" not in result
    assert "annualized_volatility" not in result
    assert "sharpe_ratio" not in result


def test_summary_rejects_empty_mapping() -> None:
    with pytest.raises(ValueError, match="results_by_symbol must not be empty"):
        summarize_multi_symbol_results({})


@pytest.mark.parametrize(
    ("results_by_symbol", "message"),
    [
        ({"  ": make_result([1.0, 2.0])}, "symbol must not be empty"),
        (
            {
                "AAPL": make_result([1.0, 2.0]),
                " aapl ": make_result([2.0, 3.0]),
            },
            "duplicate symbol: AAPL",
        ),
    ],
)
def test_summary_rejects_invalid_symbols(
    results_by_symbol: dict[str, pd.DataFrame], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        summarize_multi_symbol_results(results_by_symbol)


def test_summary_propagates_backtest_summary_validation_errors() -> None:
    with pytest.raises(ValueError, match="'equity' column"):
        summarize_multi_symbol_results(
            {"AAPL": pd.DataFrame({"strategy_return": [0.0]})}
        )


def test_summary_helper_is_exported() -> None:
    from el_psy_quant import backtesting

    assert backtesting.summarize_multi_symbol_results is summarize_multi_symbol_results
