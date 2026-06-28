from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.backtesting import moving_average_crossover_from_csv

EXPECTED_RESULT_COLUMNS = [
    "close",
    "fast_sma",
    "slow_sma",
    "signal",
    "position",
    "asset_return",
    "strategy_return",
    "transaction_cost",
    "slippage",
    "net_strategy_return",
    "equity",
]
EXPECTED_SUMMARY_KEYS = {
    "initial_equity",
    "final_equity",
    "total_return",
    "max_drawdown",
    "periods",
}


def write_prices(path: Path) -> None:
    pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=5),
            "Open": [10.0, 11.0, 12.0, 11.0, 13.0],
            "High": [11.0, 12.0, 13.0, 12.0, 14.0],
            "Low": [9.0, 10.0, 11.0, 10.0, 12.0],
            "Close": [10.0, 11.0, 12.0, 11.0, 13.0],
            "Volume": [100, 110, 120, 130, 140],
        }
    ).to_csv(path, index=False)


def test_returns_pipeline_result_and_summary_from_csv(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result, summary = moving_average_crossover_from_csv(str(path), 1, 2)

    assert list(result.columns) == EXPECTED_RESULT_COLUMNS
    assert set(summary) == EXPECTED_SUMMARY_KEYS
    assert result.index.name == "Date"


def test_accepts_path_object(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result, _ = moving_average_crossover_from_csv(path, 1, 2)

    assert len(result) == 5


def test_custom_initial_capital_is_reflected_in_summary(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    _, summary = moving_average_crossover_from_csv(
        path, 1, 2, initial_capital=1_000.0
    )

    assert summary["initial_equity"] == 1_000.0


def test_transaction_cost_rate_produces_cost_adjusted_result(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result, _ = moving_average_crossover_from_csv(
        path, 1, 2, transaction_cost_rate=0.01
    )

    pd.testing.assert_series_equal(
        result["net_strategy_return"],
        (result["strategy_return"] - result["transaction_cost"]).rename(
            "net_strategy_return"
        ),
    )


def test_slippage_rate_produces_adjusted_result(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result, _ = moving_average_crossover_from_csv(
        path, 1, 2, slippage_rate=0.01
    )

    expected = (
        result["strategy_return"]
        - result["transaction_cost"]
        - result["slippage"]
    ).rename("net_strategy_return")
    pd.testing.assert_series_equal(result["net_strategy_return"], expected)


def test_invalid_csv_error_is_propagated(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "Close": [10.0]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing required columns"):
        moving_average_crossover_from_csv(path, 1, 2)


def test_invalid_windows_error_is_propagated(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    with pytest.raises(ValueError, match="fast_window must be less than slow_window"):
        moving_average_crossover_from_csv(path, 2, 2)


def test_workflow_is_exported_from_backtesting_package() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.moving_average_crossover_from_csv
        is moving_average_crossover_from_csv
    )
