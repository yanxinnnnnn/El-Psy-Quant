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


def moving_average_crossover_parameter_sweep(
    path: str | Path,
    fast_windows: Iterable[int],
    slow_windows: Iterable[int],
    initial_capital: float = 1.0,
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
