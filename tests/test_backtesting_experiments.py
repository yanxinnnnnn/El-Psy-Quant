from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.backtesting import moving_average_crossover_parameter_sweep

EXPECTED_COLUMNS = [
    "fast_window",
    "slow_window",
    "initial_equity",
    "final_equity",
    "total_return",
    "max_drawdown",
    "periods",
]


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
