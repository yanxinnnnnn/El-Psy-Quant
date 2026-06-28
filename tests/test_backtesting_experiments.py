from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.backtesting import (
    moving_average_crossover_parameter_sweep,
    summarize_parameter_sweep_results,
)

EXPECTED_COLUMNS = [
    "fast_window",
    "slow_window",
    "initial_equity",
    "final_equity",
    "total_return",
    "max_drawdown",
    "periods",
]
EXPECTED_OVERVIEW_COLUMNS = [
    "runs",
    "fast_window_min",
    "fast_window_max",
    "slow_window_min",
    "slow_window_max",
    "initial_equity_min",
    "initial_equity_max",
    "final_equity_min",
    "final_equity_mean",
    "final_equity_max",
    "total_return_min",
    "total_return_mean",
    "total_return_max",
    "max_drawdown_min",
    "max_drawdown_mean",
    "max_drawdown_max",
    "periods_min",
    "periods_max",
]


def make_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "fast_window": [1, 2, 3],
            "slow_window": [4, 5, 6],
            "initial_equity": [100.0, 100.0, 100.0],
            "final_equity": [90.0, 110.0, 130.0],
            "total_return": [-0.1, 0.1, 0.3],
            "max_drawdown": [-0.2, -0.1, -0.3],
            "periods": [10.0, 20.0, 30.0],
        }
    )


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


def test_returns_sorted_row_for_each_valid_pair(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result = moving_average_crossover_parameter_sweep(
        path, fast_windows=[2, 1], slow_windows=[3, 2]
    )

    pairs = list(
        result[["fast_window", "slow_window"]].itertuples(
            index=False, name=None
        )
    )
    assert list(result.columns) == EXPECTED_COLUMNS
    assert pairs == [(1, 2), (1, 3), (2, 3)]


def test_custom_initial_capital_is_reflected_in_every_row(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    result = moving_average_crossover_parameter_sweep(
        path, [1], [2, 3], initial_capital=1_000.0
    )

    assert result["initial_equity"].tolist() == [1_000.0, 1_000.0]


@pytest.mark.parametrize(
    ("fast_windows", "slow_windows", "message"),
    [([], [2], "fast_windows"), ([1], [], "slow_windows")],
)
def test_rejects_empty_window_inputs(
    tmp_path: Path,
    fast_windows: list[int],
    slow_windows: list[int],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=f"{message} must not be empty"):
        moving_average_crossover_parameter_sweep(
            tmp_path / "unused.csv", fast_windows, slow_windows
        )


def test_rejects_all_invalid_combinations(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)

    with pytest.raises(
        ValueError, match="no valid moving-average window combinations"
    ):
        moving_average_crossover_parameter_sweep(path, [2, 3], [1, 2])


def test_invalid_csv_error_is_propagated(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "Close": [10.0]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing required columns"):
        moving_average_crossover_parameter_sweep(path, [1], [2])


def test_parameter_sweep_is_exported_from_backtesting_package() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.moving_average_crossover_parameter_sweep
        is moving_average_crossover_parameter_sweep
    )


def test_overview_returns_one_row_with_stable_columns_and_values() -> None:
    results = make_results()

    overview = summarize_parameter_sweep_results(results)

    assert overview.shape == (1, len(EXPECTED_OVERVIEW_COLUMNS))
    assert list(overview.columns) == EXPECTED_OVERVIEW_COLUMNS
    assert overview.iloc[0].to_dict() == {
        "runs": 3.0,
        "fast_window_min": 1.0,
        "fast_window_max": 3.0,
        "slow_window_min": 4.0,
        "slow_window_max": 6.0,
        "initial_equity_min": 100.0,
        "initial_equity_max": 100.0,
        "final_equity_min": 90.0,
        "final_equity_mean": 110.0,
        "final_equity_max": 130.0,
        "total_return_min": -0.1,
        "total_return_mean": pytest.approx(0.1),
        "total_return_max": 0.3,
        "max_drawdown_min": -0.3,
        "max_drawdown_mean": pytest.approx(-0.2),
        "max_drawdown_max": -0.1,
        "periods_min": 10.0,
        "periods_max": 30.0,
    }


def test_overview_does_not_mutate_results() -> None:
    results = make_results()
    original = results.copy(deep=True)

    summarize_parameter_sweep_results(results)

    pd.testing.assert_frame_equal(results, original)


def test_overview_rejects_empty_results() -> None:
    with pytest.raises(ValueError, match="results must not be empty"):
        summarize_parameter_sweep_results(pd.DataFrame(columns=EXPECTED_COLUMNS))


def test_overview_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns: periods"):
        summarize_parameter_sweep_results(make_results().drop(columns="periods"))


def test_overview_accepts_parameter_sweep_result(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)
    results = moving_average_crossover_parameter_sweep(path, [1], [2, 3])

    overview = summarize_parameter_sweep_results(results)

    assert overview.loc[0, "runs"] == 2


def test_overview_is_exported_from_backtesting_package() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.summarize_parameter_sweep_results
        is summarize_parameter_sweep_results
    )
