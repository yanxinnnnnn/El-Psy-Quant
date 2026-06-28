"""Small, deterministic backtesting experiments."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from el_psy_quant.backtesting.pipelines import moving_average_crossover_pipeline
from el_psy_quant.data import load_daily_prices_csv
from el_psy_quant.performance import backtest_summary

RESULT_COLUMNS = [
    "fast_window",
    "slow_window",
    "initial_equity",
    "final_equity",
    "total_return",
    "max_drawdown",
    "periods",
]
OVERVIEW_COLUMNS = [
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


def moving_average_crossover_parameter_sweep(
    path: str | Path,
    fast_windows: Iterable[int],
    slow_windows: Iterable[int],
    initial_capital: float = 1.0,
    transaction_cost_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> pd.DataFrame:
    """Summarize valid moving-average window pairs for one local CSV."""
    fast_windows = list(fast_windows)
    slow_windows = list(slow_windows)
    if not fast_windows:
        raise ValueError("fast_windows must not be empty")
    if not slow_windows:
        raise ValueError("slow_windows must not be empty")

    prices = load_daily_prices_csv(path)
    rows: list[dict[str, float | int]] = []
    for fast_window in fast_windows:
        for slow_window in slow_windows:
            if fast_window >= slow_window:
                continue
            result = moving_average_crossover_pipeline(
                prices["Close"],
                fast_window,
                slow_window,
                initial_capital,
                transaction_cost_rate,
                slippage_rate,
            )
            rows.append(
                {
                    "fast_window": fast_window,
                    "slow_window": slow_window,
                    **backtest_summary(result),
                }
            )

    if not rows:
        raise ValueError("no valid moving-average window combinations")

    return (
        pd.DataFrame(rows, columns=RESULT_COLUMNS)
        .sort_values(["fast_window", "slow_window"])
        .reset_index(drop=True)
    )


def summarize_parameter_sweep_results(results: pd.DataFrame) -> pd.DataFrame:
    """Return a one-row descriptive overview of parameter sweep results."""
    if results.empty:
        raise ValueError("results must not be empty")
    missing = [column for column in RESULT_COLUMNS if column not in results]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    overview = {
        "runs": len(results),
        "fast_window_min": results["fast_window"].min(),
        "fast_window_max": results["fast_window"].max(),
        "slow_window_min": results["slow_window"].min(),
        "slow_window_max": results["slow_window"].max(),
        "initial_equity_min": results["initial_equity"].min(),
        "initial_equity_max": results["initial_equity"].max(),
        "final_equity_min": results["final_equity"].min(),
        "final_equity_mean": results["final_equity"].mean(),
        "final_equity_max": results["final_equity"].max(),
        "total_return_min": results["total_return"].min(),
        "total_return_mean": results["total_return"].mean(),
        "total_return_max": results["total_return"].max(),
        "max_drawdown_min": results["max_drawdown"].min(),
        "max_drawdown_mean": results["max_drawdown"].mean(),
        "max_drawdown_max": results["max_drawdown"].max(),
        "periods_min": results["periods"].min(),
        "periods_max": results["periods"].max(),
    }
    return pd.DataFrame([overview], columns=OVERVIEW_COLUMNS)
